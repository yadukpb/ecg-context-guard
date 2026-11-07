"""Evaluate the trained gatekeeper on clean/noisy test data and under each attack/epsilon."""
from __future__ import annotations

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score

from Paper_1_Attack_Independent_Defence.adversarial_attacks import attacks

EPSILONS = (0.001, 0.01, 0.03, 0.1, 0.3, 0.5, 1.0)  # paper's own Algorithm 1 sweep, verified from the PDF


def clean_vs_noisy_metrics(model, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    X_t = torch.tensor(X_test).unsqueeze(1)
    with torch.no_grad():
        preds = model(X_t).argmax(dim=1).numpy()
    return {"accuracy": float(accuracy_score(y_test, preds)), "f1": float(f1_score(y_test, preds, zero_division=0))}


def attack_metrics(model, X_test: np.ndarray, y_test: np.ndarray, n_subset: int = 30) -> dict:
    """Run FGSM/PGD (full subset) + simplified black-box attacks (smaller subset, query-
    heavy) across EPSILONS, report ACC/F1 of the gatekeeper against the resulting adversarial
    inputs with their TRUE (pre-attack) label — mirrors the paper's Tables 3-5 structure."""
    rng = np.random.default_rng(0)
    idx = rng.choice(len(X_test), size=min(n_subset, len(X_test)), replace=False)
    X_sub = torch.tensor(X_test[idx]).unsqueeze(1)
    y_sub = torch.tensor(y_test[idx])

    results: dict[str, dict[float, dict]] = {"fgsm": {}, "pgd": {}}

    for eps in EPSILONS:
        for name, fn in [("fgsm", attacks.fgsm_attack), ("pgd", attacks.pgd_attack)]:
            x_adv = fn(model, X_sub, y_sub, eps)
            with torch.no_grad():
                preds = model(x_adv).argmax(dim=1).numpy()
            results[name][eps] = {
                "accuracy": float(accuracy_score(y_sub.numpy(), preds)),
                "f1": float(f1_score(y_sub.numpy(), preds, zero_division=0)),
            }

    # Black-box: query-heavy, so a smaller sample (5) and fewer epsilons to keep runtime bounded.
    bb_idx = idx[:5]

    try:
        import art  # noqa: F401 — presence check only; actual calls are in attacks.py
        art_available = True
    except ImportError:
        art_available = False

    if art_available:
        for name, attack_fn in [
            ("hopskipjump_art", attacks.art_hopskipjump_attack),
            ("boundary_art", attacks.art_boundary_attack),
        ]:
            bb_preds, bb_true = [], []
            for i in bb_idx:
                x = torch.tensor(X_test[i : i + 1]).unsqueeze(1)
                x_adv = attack_fn(model, x)
                with torch.no_grad():
                    pred = int(model(x_adv).argmax(dim=1).item())
                bb_preds.append(pred)
                bb_true.append(int(y_test[i]))
            results[name] = {
                0.0: {  # epsilon isn't a parameter of these attacks; keyed at 0.0 for table-shape consistency
                    "accuracy": float(accuracy_score(bb_true, bb_preds)),
                    "f1": float(f1_score(bb_true, bb_preds, zero_division=0)) if len(set(bb_true)) > 1 else float("nan"),
                    "n_samples": len(bb_true),
                }
            }
    else:
        bb_preds, bb_true = [], []
        for i in bb_idx:
            x = torch.tensor(X_test[i : i + 1]).unsqueeze(1)
            orig_class = y_test[i]
            x_adv = attacks.simplified_boundary_walk(model, x, int(orig_class), epsilon=0.1)
            with torch.no_grad():
                pred = int(model(x_adv).argmax(dim=1).item())
            bb_preds.append(pred)
            bb_true.append(orig_class)
        results["boundary_walk_simplified"] = {
            0.1: {
                "accuracy": float(accuracy_score(bb_true, bb_preds)),
                "f1": float(f1_score(bb_true, bb_preds, zero_division=0)) if len(set(bb_true)) > 1 else float("nan"),
                "n_samples": len(bb_true),
            }
        }

    return results
