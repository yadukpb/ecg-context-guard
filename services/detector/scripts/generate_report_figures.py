"""Standalone script producing static report figures — no FastAPI/Express/Mongo required.

Run with the detector venv active:
    cd services/detector && ./venv/bin/python scripts/generate_report_figures.py

Produces two figures into docs/figures/, meant to go straight into the written report or the
next review's slides:

1. waveform_comparison.png — a genuine window vs. each attack type applied to it, so a
   reader can see by eye that the manipulated signal still "looks like" a plausible ECG.
2. detection_timeline.png — combined detection score across a sequence of windows where an
   attack is switched on partway through, showing the verdict flip from genuine to
   suspicious/manipulated.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

from app import mitdb
from app.attack import AttackType, apply_attack
from app.baseline import BaselineBuilder
from app.config import CALIBRATION_WINDOWS, FS_HZ, WINDOW_SEC
from app.cross_sensor import new_state, next_secondary_hr
from app.detector import score_window
from app.signal_proc import extract_features, preprocess

WINDOW_SAMPLES = WINDOW_SEC * FS_HZ
FIGURES_DIR = Path(__file__).resolve().parents[3] / "docs" / "figures"
RECORD_ID = "100"


def _windows(signal, n: int):
    return [signal[i * WINDOW_SAMPLES : (i + 1) * WINDOW_SAMPLES] for i in range(n)]


def plot_waveform_comparison(genuine_window) -> None:
    attack_types = [AttackType.AMPLITUDE_DRIFT, AttackType.RR_STRETCH, AttackType.SEGMENT_REPLAY]
    fig, axes = plt.subplots(len(attack_types) + 1, 1, figsize=(10, 9), sharex=True)

    axes[0].plot(genuine_window, color="tab:blue")
    axes[0].set_title("Genuine (preprocessed)")

    for ax, attack_type in zip(axes[1:], attack_types):
        attacked = apply_attack(genuine_window, attack_type, intensity=1.0)
        ax.plot(genuine_window, color="tab:blue", alpha=0.35, label="genuine")
        ax.plot(attacked, color="tab:red", alpha=0.8, label="manipulated")
        ax.set_title(f"Attack: {attack_type.value} (intensity=1.0)")
        ax.legend(loc="upper right", fontsize=8)

    axes[-1].set_xlabel("sample")
    fig.suptitle("Genuine vs. manipulated ECG window — values stay 'clinically plausible'")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "waveform_comparison.png", dpi=150)
    plt.close(fig)


def plot_detection_timeline(windows: list) -> None:
    """Replay a sequence of windows, building a baseline from the first
    CALIBRATION_WINDOWS, then switching an attack on halfway through the remainder."""
    builder = BaselineBuilder()
    calibration = windows[:CALIBRATION_WINDOWS]
    remainder = windows[CALIBRATION_WINDOWS:]

    for w in calibration:
        builder.add(extract_features(w, FS_HZ))
    baseline = builder.build()

    attack_on_from = len(remainder) // 2
    history = []
    scores, verdicts, attack_flags = [], [], []
    cross_state = new_state("figure-demo-patient")

    for i, w in enumerate(remainder):
        true_features = extract_features(w, FS_HZ)
        secondary_hr, cross_state = next_secondary_hr(true_features.heart_rate_bpm, cross_state)

        attack_on = i >= attack_on_from
        transmitted = apply_attack(w, AttackType.RR_STRETCH, intensity=0.8) if attack_on else w
        features = extract_features(transmitted, FS_HZ)

        result = score_window(features, baseline, history, secondary_hr)
        history.append(features)

        scores.append(result.combined_score)
        verdicts.append(result.verdict.value)
        attack_flags.append(attack_on)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    colors = {"genuine": "tab:green", "suspicious": "tab:orange", "manipulated": "tab:red"}
    ax.plot(scores, color="black", linewidth=1, zorder=1)
    ax.scatter(
        range(len(scores)),
        scores,
        c=[colors[v] for v in verdicts],
        zorder=2,
        label=None,
    )
    ax.axvline(attack_on_from, color="gray", linestyle="--", label="attack switched on")
    ax.axhline(2.0, color="tab:orange", linestyle=":", linewidth=1, label="suspicious threshold")
    ax.axhline(3.5, color="tab:red", linestyle=":", linewidth=1, label="manipulated threshold")
    ax.set_xlabel("window index (post-calibration)")
    ax.set_ylabel("combined detection score")
    ax.set_title("Detection score over time — attack switched on partway through")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "detection_timeline.png", dpi=150)
    plt.close(fig)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    raw_signal = mitdb.lead_ii_signal(RECORD_ID)
    n_windows = CALIBRATION_WINDOWS + 20
    raw_windows = _windows(raw_signal, n_windows)
    processed_windows = [preprocess(w, FS_HZ) for w in raw_windows]

    plot_waveform_comparison(processed_windows[CALIBRATION_WINDOWS + 5])
    plot_detection_timeline(processed_windows)

    print(f"Figures written to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
