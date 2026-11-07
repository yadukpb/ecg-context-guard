"""End-to-end Paper-2 reproduction run: THECF -> HGAN-SVM-DT ablation -> CNN classifier.

Run with: ``cd research && Common/venv/bin/python -m Paper_2_Layered_MIOT_Framework.main``

Scoped-down config by default (12 records, k=3 folds, SFOA population 10/iterations 15, 8
CNN epochs, 64px images) — see research/FEASIBILITY_REPORT.md compute-budget note and
training/train.py's module docstring. Every number printed below comes from this script
actually running against real MIT-BIH/NSTDB data, not from the papers' tables.
"""
from __future__ import annotations

import json

from Common.datasets import mitdb
from Paper_2_Layered_MIOT_Framework.evaluation.evaluate import run_thecf_comparison
from Paper_2_Layered_MIOT_Framework.training.train import (
    DEFAULT_RECORDS, run_classification_stage, run_detection_stage,
)


def main() -> None:
    print("=== Stage 0: THECF validation (MIT-BIH clean + NSTDB noisy) ===")
    thecf_results = run_thecf_comparison(
        template_records=DEFAULT_RECORDS[:3], clean_records=DEFAULT_RECORDS[:5],
    )
    print(json.dumps(thecf_results, indent=2))

    print("\n=== Stage 1: HGAN-SVM-DT ablation (normal vs. abnormal) ===")
    detection_results = run_detection_stage(DEFAULT_RECORDS)
    print(json.dumps(detection_results, indent=2))

    print("\n=== Stage 2: SFOA-CNN 7-class arrhythmia classification ===")
    classification_results = run_classification_stage(DEFAULT_RECORDS)
    print(json.dumps(classification_results, indent=2))

    with open("Paper_2_Layered_MIOT_Framework/evaluation/results.json", "w") as f:
        json.dump({
            "thecf": thecf_results,
            "detection_ablation": detection_results,
            "classification": classification_results,
            "records_used": DEFAULT_RECORDS,
        }, f, indent=2)


if __name__ == "__main__":
    main()
