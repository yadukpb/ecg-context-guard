"""Triple Hierarchical Energy & Correlation-based Fault Detection (THECF).

Pure signal processing, no training — implements the three gating layers exactly as the
paper states them (its "Sensor error detection..." section and Fig. 2):

1. Total-energy gate: mean squared amplitude of a 1-second window must fall inside
   [0.001, 15] mV^2 (below -> flatline/electrode disconnection, above -> severe motion
   artefact).
2. QRS-band energy ratio: after a 4th-order Butterworth band-pass at 30-45 Hz, the ratio of
   that band's energy to the window's total energy must fall inside [0.18, 0.85].
3. Normalized cross-correlation (NCC) against a healthy-beat template (averaged from 100
   clean beats) must be >= 0.72.

A window that fails any layer is rejected as faulty; only windows that pass all three are
forwarded to HGAN-SVM-DT.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, filtfilt

ENERGY_LOW, ENERGY_HIGH = 0.001, 15.0
QRS_RATIO_LOW, QRS_RATIO_HIGH = 0.18, 0.85
NCC_ACCEPT = 0.72


@dataclass
class Thresholds:
    """The three gate thresholds — defaults are the paper's own published numbers. See
    ``calibrate.py`` for thresholds re-derived from our own real data using the paper's own
    stated methodology (statistical analysis of real windows), for the case — confirmed via
    direct measurement on real MIT-BIH, not assumed — where the published numbers don't hold
    under our windowing convention."""

    energy_low: float = ENERGY_LOW
    energy_high: float = ENERGY_HIGH
    qrs_ratio_low: float = QRS_RATIO_LOW
    qrs_ratio_high: float = QRS_RATIO_HIGH
    ncc_accept: float = NCC_ACCEPT


PAPER_THRESHOLDS = Thresholds()


@dataclass
class THECFVerdict:
    passed: bool
    energy: float
    qrs_ratio: float
    ncc: float
    failed_layer: str | None  # "energy" | "qrs_band" | "correlation" | None if passed


def total_energy(window: np.ndarray) -> float:
    return float(np.mean(window.astype(np.float64) ** 2))


def _qrs_band_filter(window: np.ndarray, fs: float) -> np.ndarray:
    nyq = fs / 2.0
    low, high = 30.0 / nyq, min(45.0, nyq - 1e-6) / nyq
    b, a = butter(4, [low, high], btype="bandpass")
    # filtfilt needs a signal longer than ~3x the filter order; 1s windows at typical ECG
    # sampling rates (>=200Hz) comfortably satisfy this.
    return filtfilt(b, a, window)


def qrs_band_energy_ratio(window: np.ndarray, fs: float) -> float:
    total = total_energy(window)
    if total == 0:
        return 0.0
    band = _qrs_band_filter(window, fs)
    return float(np.mean(band**2) / total)


def build_healthy_template(beats: list[np.ndarray]) -> np.ndarray:
    """Average up to 100 clean, equal-length beat waveforms into one reference template."""
    beats = beats[:100]
    length = min(len(b) for b in beats)
    stacked = np.stack([b[:length] for b in beats])
    return stacked.mean(axis=0)


def normalized_cross_correlation(window: np.ndarray, template: np.ndarray) -> float:
    n = min(len(window), len(template))
    w, t = window[:n] - window[:n].mean(), template[:n] - template[:n].mean()
    denom = np.linalg.norm(w) * np.linalg.norm(t)
    if denom == 0:
        return 0.0
    return float(np.dot(w, t) / denom)


def evaluate(
    window: np.ndarray, fs: float, template: np.ndarray, thresholds: Thresholds = PAPER_THRESHOLDS,
) -> THECFVerdict:
    energy = total_energy(window)
    if not (thresholds.energy_low <= energy <= thresholds.energy_high):
        return THECFVerdict(False, energy, float("nan"), float("nan"), "energy")

    qrs_ratio = qrs_band_energy_ratio(window, fs)
    if not (thresholds.qrs_ratio_low <= qrs_ratio <= thresholds.qrs_ratio_high):
        return THECFVerdict(False, energy, qrs_ratio, float("nan"), "qrs_band")

    ncc = normalized_cross_correlation(window, template)
    if ncc < thresholds.ncc_accept:
        return THECFVerdict(False, energy, qrs_ratio, ncc, "correlation")

    return THECFVerdict(True, energy, qrs_ratio, ncc, None)
