"""Build the combined ECG-ID + CinC-2011 + CinC-2014 + teleECG dataset, train the
ResNet-18(1D) clean/noisy gatekeeper.

All four of the paper's named datasets are wired up (ECG-ID, CinC-2011, CinC-2014 all
PhysioNet-hosted and ``wfdb``-loadable; teleECG is Harvard-Dataverse-hosted — see
``Common/datasets/teleecg.py`` — openly licensed (CC0), verified live before this was built).

Two different ways of getting a noisy/clean label, used honestly rather than blurred
together:
- ECG-ID, CinC-2011, CinC-2014 have no artifact ground truth of their own, so (same as the
  original ECG-ID-only pass) real BW/EM/MA NSTDB noise is synthetically injected and labelled
  via ``noise_generation/synth_noise.py``'s re-derived proxy rule.
- teleECG ships its own human-annotated artifact mask (``visual_mask``) — real ground truth,
  not a proxy — used directly instead of synthetic injection.

Person-independent (ECG-ID) / record-independent (the other three) group IDs are tracked
throughout so a train/test split never puts two samples from the same underlying
person/recording on opposite sides (the same leakage class of mistake already documented in
ecg-context-guard's docs/mistakes-log.md), and a parallel per-sample dataset-name array
supports leave-one-dataset-out evaluation (the paper's own stated protocol, §5.2).
"""
from __future__ import annotations

import numpy as np
import torch
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from Common.datasets import cinc2011, cinc2014, ecgiddb, nstdb, teleecg
from Paper_1_Attack_Independent_Defence.models.resnet1d import ResNet18_1D
from Paper_1_Attack_Independent_Defence.noise_generation import synth_noise

SEGMENT_LEN = 5000  # 10s @ 500Hz, matches the paper's standardized segment length
DATASETS = ("ecgid", "cinc2011", "cinc2014", "teleecg")

# Per-dataset record counts: ECG-ID uses its full 90 people (matching the paper's own
# count); CinC-2011/2014/teleECG are each bounded to a subset of their much larger pools
# (1000 / 100 / 250 records respectively) so a full run stays CPU-tractable in one sitting —
# a scope choice, not a access limitation (all three are verified fully accessible above).
DEFAULT_ECGID_PERSONS = list(range(1, ecgiddb.NUM_PERSONS + 1))
DEFAULT_CINC2011_N = 60
DEFAULT_CINC2014_N = 15
DEFAULT_TELEECG_N = 60


def _noise_traces() -> tuple[dict[str, np.ndarray], float]:
    noise_traces, noise_fs = {}, None
    for noise_type in ["bw", "em", "ma"]:
        trace, noise_fs = nstdb.noise_trace(noise_type)
        noise_traces[noise_type] = trace
    return noise_traces, noise_fs


def _fit_segment(signal: np.ndarray, fs: float) -> np.ndarray:
    if fs != synth_noise.TARGET_FS:
        signal = synth_noise._resample_to(signal, fs, synth_noise.TARGET_FS)
    if len(signal) < SEGMENT_LEN:
        signal = np.pad(signal, (0, SEGMENT_LEN - len(signal)), mode="edge")
    return signal[:SEGMENT_LEN]


def _synthetic_subset(
    dataset_name: str, segments_with_ids: list[tuple[str, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Clean segments + real NSTDB noise injected on top, our proxy label rule — the path
    shared by ecgid/cinc2011/cinc2014 (none of which ship their own artifact ground truth)."""
    if not segments_with_ids:
        return np.empty((0, SEGMENT_LEN), dtype=np.float32), np.empty(0, dtype=np.int64), [], []

    ids, clean_segments = zip(*segments_with_ids)
    noise_traces, noise_fs = _noise_traces()
    samples = synth_noise.build_dataset(list(clean_segments), synth_noise.TARGET_FS, noise_traces, noise_fs)
    samples_per_clean = 1 + len(noise_traces) * 2  # 1 clean + (noise types * snr levels)
    group_ids = np.repeat(ids, samples_per_clean)[: len(samples)].tolist()

    X = np.array([s.segment for s in samples], dtype=np.float32)
    y = np.array([s.is_noisy for s in samples], dtype=np.int64)
    dataset_ids = [dataset_name] * len(samples)
    return X, y, group_ids, dataset_ids


def _ecgid_subset(persons: list[int]) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    segments = []
    for person in persons:
        try:
            signal, fs = ecgiddb.filtered_signal(person, recording=1)
        except Exception:
            continue
        segments.append((f"ecgid_{person}", _fit_segment(signal, fs)))
    return _synthetic_subset("ecgid", segments)


def _cinc2011_subset(n_records: int) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    segments = []
    for name in cinc2011.all_records()[:n_records]:
        try:
            signal, fs = cinc2011.lead_signal(name)
        except Exception:
            continue
        segments.append((f"cinc2011_{name}", _fit_segment(signal, fs)))
    return _synthetic_subset("cinc2011", segments)


def _cinc2014_subset(n_records: int) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Only the first 10s window per (much longer) record — bounds this dataset's
    contribution to roughly the same per-record sample count as the other three rather than
    letting one 10-minute recording dominate."""
    segments = []
    for name in cinc2014.all_records()[:n_records]:
        try:
            signal, fs = cinc2014.lead_signal(name)
        except Exception:
            continue
        win_len = int(10.0 * fs)
        if len(signal) < win_len:
            continue
        segments.append((f"cinc2014_{name}", _fit_segment(signal[:win_len], fs)))
    return _synthetic_subset("cinc2014", segments)


def _teleecg_subset(n_records: int) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Real ground-truth artifact mask, no synthetic injection — see module docstring."""
    X, y, group_ids = [], [], []
    for name in teleecg.all_records()[:n_records]:
        record = teleecg.get_record(name)
        if len(record.ecg_mv) < SEGMENT_LEN:
            continue
        segment = synth_noise._min_max_normalize(record.ecg_mv[:SEGMENT_LEN].astype(np.float32))
        label = 0 if teleecg.is_clean_segment(name, 0, SEGMENT_LEN) else 1
        X.append(segment)
        y.append(label)
        group_ids.append(f"teleecg_{name}")
    X_arr = np.array(X, dtype=np.float32) if X else np.empty((0, SEGMENT_LEN), dtype=np.float32)
    y_arr = np.array(y, dtype=np.int64) if y else np.empty(0, dtype=np.int64)
    return X_arr, y_arr, group_ids, ["teleecg"] * len(X)


_SUBSET_BUILDERS = {
    "ecgid": lambda: _ecgid_subset(DEFAULT_ECGID_PERSONS),
    "cinc2011": lambda: _cinc2011_subset(DEFAULT_CINC2011_N),
    "cinc2014": lambda: _cinc2014_subset(DEFAULT_CINC2014_N),
    "teleecg": lambda: _teleecg_subset(DEFAULT_TELEECG_N),
}


def build_dataset(
    datasets: list[str] = DATASETS,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Returns (X, y, group_ids, dataset_ids). ``group_ids`` is unique per underlying
    person/recording (for a leakage-free train/test split); ``dataset_ids`` names which of
    the four source datasets each sample came from (for leave-one-dataset-out)."""
    all_X, all_y, all_groups, all_datasets = [], [], [], []
    for name in datasets:
        X, y, groups, dataset_ids = _SUBSET_BUILDERS[name]()
        if len(X) == 0:
            continue
        all_X.append(X)
        all_y.append(y)
        all_groups.extend(groups)
        all_datasets.extend(dataset_ids)

    X = np.concatenate(all_X) if all_X else np.empty((0, SEGMENT_LEN), dtype=np.float32)
    y = np.concatenate(all_y) if all_y else np.empty(0, dtype=np.int64)
    return X, y, np.array(all_groups), np.array(all_datasets)


def person_independent_split(X, y, group_ids, test_size: float = 0.3, seed: int = 0):
    """Despite the name (kept for backward compatibility with existing call sites),
    this splits on whatever ``group_ids`` represents: ECG-ID person, or
    CinC-2011/2014/teleECG record — never two samples from the same group on both sides."""
    unique_groups = np.unique(group_ids)
    train_groups, test_groups = train_test_split(unique_groups, test_size=test_size, random_state=seed)
    train_mask = np.isin(group_ids, train_groups)
    test_mask = np.isin(group_ids, test_groups)
    return X[train_mask], y[train_mask], X[test_mask], y[test_mask]


def leave_one_dataset_out_split(X, y, dataset_ids, held_out: str):
    """Train on every dataset except ``held_out``, test on ``held_out`` — the paper's own
    stated generalization protocol (§5.2), in addition to (not instead of) the
    within-dataset person/record-independent split above."""
    test_mask = dataset_ids == held_out
    return X[~test_mask], y[~test_mask], X[test_mask], y[test_mask]


def train_resnet(X_train: np.ndarray, y_train: np.ndarray, epochs: int = 8) -> ResNet18_1D:
    model = ResNet18_1D(in_channels=1, num_classes=2)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()

    X_t = torch.tensor(X_train).unsqueeze(1)  # (N, 1, L)
    y_t = torch.tensor(y_train)
    loader = DataLoader(TensorDataset(X_t, y_t), batch_size=16, shuffle=True)

    model.train()
    for _ in range(epochs):
        for xb, yb in loader:
            opt.zero_grad()
            loss_fn(model(xb), yb).backward()
            opt.step()
    model.eval()
    return model
