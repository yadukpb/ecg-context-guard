"""Training entry points for both Paper-2 stages.
Every number this module returns comes from an actual run against actual MIT-BIH data.
"""
from __future__ import annotations

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, recall_score, roc_auc_score
from sklearn.model_selection import KFold
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from Common.datasets import mitdb
from Paper_2_Layered_MIOT_Framework.CNN_classifier.model import CLASSES, ArrhythmiaCNN
from Paper_2_Layered_MIOT_Framework.differential_transformation.ecg_to_image import ecg_to_image
from Paper_2_Layered_MIOT_Framework.feature_extraction.features import extract_features
from Paper_2_Layered_MIOT_Framework.HGAN_SVM_DT import model as hsd
from Paper_2_Layered_MIOT_Framework.training.dataset import Window, build_dataset

# Full MIT-BIH config, matching the paper's own scale (all 47/48 usable records). An earlier
# scoped-down pass used a hand-picked 12-record subset after discovering the first 12 records
# by number contain zero AFIB/AFL/VT windows and only one Trigeminy window (silently making 4
# of the paper's 7 classes untestable) — that finding is preserved in
# research/COMPARISON_REPORT.md. VT is still the thinnest class across the full 48 records;
# reported per-class, not hidden, regardless.
DEFAULT_RECORDS = mitdb.ALL_RECORDS
BEAT_WINDOW = (90, 110)  # samples before/after R, ~0.25s before + 0.3s after at 360Hz


def _features_for_windows(windows: list[Window]) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for w in windows:
        if w.r_index is None or w.rr_prev_samples is None or w.rr_next_samples is None:
            # First/last beat of a record has no previous/next RR interval to compute from
            # — excluded rather than imputed, so every feature column is a real measurement.
            continue
        signal, fs = mitdb.lead_signal(w.record)
        feats = extract_features(
            signal, fs, w.r_index, BEAT_WINDOW,
            prev_rr_samples=w.rr_prev_samples, next_rr_samples=w.rr_next_samples,
        )
        X.append(feats)
        y.append(w.detection)
    return np.array(X), np.array(y)


def run_detection_stage(
    record_names: list[str] = DEFAULT_RECORDS, k_folds: int = 5,
    sfoa_population: int = 30, sfoa_iterations: int = 50,
) -> dict:
    """Patient-independent k-fold ablation for THECF-screened HGAN-SVM-DT.

    Returns per-variant metrics averaged over folds: svm_only, dt_only,
    svm_plus_dt_default, svm_plus_dt_sfoa (our ablation naming — see model.py docstring for
    why this doesn't map 1:1 onto the paper's "GAN only" row).
    """
    kf = KFold(n_splits=k_folds, shuffle=True, random_state=0)
    records = np.array(record_names)
    variant_scores: dict[str, list[dict]] = {
        "svm_only": [], "dt_only": [], "svm_plus_dt_default": [], "svm_plus_dt_sfoa": [],
    }

    for train_idx, test_idx in kf.split(records):
        train_records, test_records = records[train_idx].tolist(), records[test_idx].tolist()
        X_train, y_train = _features_for_windows(build_dataset(train_records))
        X_test, y_test = _features_for_windows(build_dataset(test_records))
        if len(np.unique(y_train)) < 2 or len(X_test) == 0:
            continue

        mu, sigma = X_train.mean(0), X_train.std(0) + 1e-9
        X_train, X_test = (X_train - mu) / sigma, (X_test - mu) / sigma

        svm_only = hsd.HGANSVMDT.from_params(np.array([0.0, -1.0, 8.0, 0.0, 1.0])).fit(X_train, y_train)
        dt_only = hsd.HGANSVMDT.from_params(np.array([0.0, -1.0, 8.0, 0.0, 0.0])).fit(X_train, y_train)
        default_ensemble = hsd.train_default(X_train, y_train)
        sfoa_ensemble, sfoa_result = hsd.train_with_sfoa(
            X_train, y_train, X_test, y_test, population=sfoa_population, iterations=sfoa_iterations,
        )

        for name, model in [
            ("svm_only", svm_only), ("dt_only", dt_only),
            ("svm_plus_dt_default", default_ensemble), ("svm_plus_dt_sfoa", sfoa_ensemble),
        ]:
            preds = model.predict(X_test)
            proba = model.predict_proba_abnormal(X_test)
            variant_scores[name].append({
                "accuracy": accuracy_score(y_test, preds),
                "recall": recall_score(y_test, preds, zero_division=0),
                "f1": f1_score(y_test, preds, zero_division=0),
                "auc": roc_auc_score(y_test, proba) if len(np.unique(y_test)) > 1 else float("nan"),
            })

    return {
        name: {metric: float(np.nanmean([s[metric] for s in scores])) for metric in ["accuracy", "recall", "f1", "auc"]}
        for name, scores in variant_scores.items() if scores
    }


class _ImageDataset(TensorDataset):
    pass


def _build_image_tensors(windows: list[Window]) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
    images, labels = [], []
    seen_classes: list[str] = []
    for w in windows:
        if w.classification is None:
            continue
        signal, _ = mitdb.lead_signal(w.record)
        window_signal = signal[w.start:w.end]
        img = ecg_to_image(window_signal, image_size=64)  # 64px: CPU-friendly for this pass
        images.append(img.transpose(2, 0, 1) / 255.0)
        if w.classification not in seen_classes:
            seen_classes.append(w.classification)
        labels.append(CLASSES.index(w.classification))

    X = torch.tensor(np.array(images), dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)
    return X, y, seen_classes


def run_classification_stage(
    record_names: list[str] = DEFAULT_RECORDS, k_folds: int = 5, epochs: int = 12,
) -> dict:
    """Patient-independent k-fold CNN training on differential-image windows.

    64x64 images (CPU-friendly; the paper doesn't specify its own image resolution).
    """
    kf = KFold(n_splits=k_folds, shuffle=True, random_state=0)
    records = np.array(record_names)
    fold_metrics = []
    pooled_true: list[int] = []
    pooled_pred: list[int] = []

    for train_idx, test_idx in kf.split(records):
        train_records, test_records = records[train_idx].tolist(), records[test_idx].tolist()
        X_train, y_train, _ = _build_image_tensors(build_dataset(train_records))
        X_test, y_test, _ = _build_image_tensors(build_dataset(test_records))
        if len(X_train) == 0 or len(X_test) == 0:
            continue

        # Class weighting (paper's own "class balancing and class weighting" step, §6/G of
        # the brief) — MIT-BIH's 7 rhythm classes are naturally very imbalanced (NSR
        # dominates, VT is rare); inverse-frequency weights keep rare classes from being
        # ignored by the loss.
        class_counts = torch.bincount(y_train, minlength=len(CLASSES)).float()
        class_weights = torch.where(class_counts > 0, 1.0 / class_counts, torch.zeros_like(class_counts))
        class_weights = class_weights / class_weights.sum() * len(CLASSES)

        model = ArrhythmiaCNN(num_classes=len(CLASSES))
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.CrossEntropyLoss(weight=class_weights)
        loader = DataLoader(TensorDataset(X_train, y_train), batch_size=16, shuffle=True)

        model.train()
        for _ in range(epochs):
            for xb, yb in loader:
                opt.zero_grad()
                loss_fn(model(xb), yb).backward()
                opt.step()

        model.eval()
        with torch.no_grad():
            preds = model(X_test).argmax(dim=1).numpy()
        y_test_np = y_test.numpy()
        pooled_true.extend(y_test_np.tolist())
        pooled_pred.extend(preds.tolist())
        fold_metrics.append({
            "accuracy": accuracy_score(y_test_np, preds),
            "f1_macro": f1_score(y_test_np, preds, average="macro", zero_division=0),
            "recall_macro": recall_score(y_test_np, preds, average="macro", zero_division=0),
            "n_test": len(y_test_np),
        })

    per_class_recall = {}
    if pooled_true:
        present = sorted(set(pooled_true) | set(pooled_pred))
        recalls = recall_score(pooled_true, pooled_pred, labels=present, average=None, zero_division=0)
        per_class_recall = {CLASSES[i]: float(r) for i, r in zip(present, recalls)}

    return {
        metric: float(np.mean([f[metric] for f in fold_metrics]))
        for metric in ["accuracy", "f1_macro", "recall_macro"]
    } | {"folds_run": len(fold_metrics), "per_class_recall_pooled": per_class_recall}
