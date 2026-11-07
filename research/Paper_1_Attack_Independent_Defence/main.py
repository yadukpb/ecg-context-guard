"""End-to-end Paper-1 reproduction run: build dataset -> train gatekeeper -> evaluate clean/
noisy + adversarial robustness, both under a person/record-independent split and under
leave-one-dataset-out (the paper's own stated generalization protocol, §5.2).

Run with: ``cd research && Common/venv/bin/python -m Paper_1_Attack_Independent_Defence.main``

Combines all four of the paper's named datasets (ECG-ID full 90 people, bounded subsets of
CinC-2011/CinC-2014/teleECG — see training/train.py's module docstring for exact scope and
why), the paper's own full 7-value epsilon sweep, and real IBM ART HopSkipJump/Boundary
attacks (ART installed cleanly this pass — see adversarial_attacks/attacks.py).
"""
from __future__ import annotations

import json

from Paper_1_Attack_Independent_Defence.evaluation.evaluate import attack_metrics, clean_vs_noisy_metrics
from Paper_1_Attack_Independent_Defence.training.train import (
    DATASETS, build_dataset, leave_one_dataset_out_split, person_independent_split, train_resnet,
)


def main() -> None:
    print("=== Building ECG-ID + CinC-2011 + CinC-2014 + teleECG dataset ===")
    X, y, group_ids, dataset_ids = build_dataset()
    print(f"Total samples: {len(X)}, noisy fraction (our/real label): {y.mean():.3f}")
    for name in DATASETS:
        n = int((dataset_ids == name).sum())
        print(f"  {name}: {n} samples")

    X_train, y_train, X_test, y_test = person_independent_split(X, y, group_ids)
    print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples (person/record-independent split)")

    print("\n=== Training ResNet-18 (1D) gatekeeper ===")
    model = train_resnet(X_train, y_train)

    print("\n=== Clean/noisy evaluation ===")
    clean_noisy = clean_vs_noisy_metrics(model, X_test, y_test)
    print(json.dumps(clean_noisy, indent=2))

    print("\n=== Adversarial robustness evaluation ===")
    attack_results = attack_metrics(model, X_test, y_test)
    print(json.dumps(attack_results, indent=2))

    print("\n=== Leave-one-dataset-out generalization ===")
    lodo_results = {}
    for held_out in DATASETS:
        X_tr, y_tr, X_te, y_te = leave_one_dataset_out_split(X, y, dataset_ids, held_out)
        if len(X_tr) == 0 or len(X_te) == 0 or len(set(y_tr.tolist())) < 2:
            lodo_results[held_out] = {"skipped": "insufficient data for this split"}
            continue
        lodo_model = train_resnet(X_tr, y_tr)
        lodo_results[held_out] = clean_vs_noisy_metrics(lodo_model, X_te, y_te)
    print(json.dumps(lodo_results, indent=2))

    with open("Paper_1_Attack_Independent_Defence/evaluation/results.json", "w") as f:
        json.dump({
            "n_total": len(X), "n_train": len(X_train), "n_test": len(X_test),
            "per_dataset_counts": {name: int((dataset_ids == name).sum()) for name in DATASETS},
            "clean_vs_noisy": clean_noisy, "attacks": attack_results,
            "leave_one_dataset_out": lodo_results,
        }, f, indent=2)


if __name__ == "__main__":
    main()
