"""Manipulation detection — combines temporal and cross-sensor scores into a verdict.

Deliberately not ML-based: the slides' own Scope slide defers "ML/DL-based detection
methods" to a future extension, so this semester's detector is a documented, inspectable
weighted z-score scheme. See docs/building/05-detection-algorithm.md for the full writeup
and the reasoning behind every threshold below.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from .baseline import BaselineProfile
from .signal_proc import WindowFeatures

# Expected noise between the ECG-derived HR and the independent secondary-vital HR under
# *normal* conditions — used to z-score their disagreement. Two different values:
# - The synthetic stand-in (cross_sensor.py, used for MIT-BIH-backed patients, which have no
#   real second sensor) is generated with tight, small noise, so a tight std is appropriate.
# - A real second sensor (BIDMC-backed patients — see bidmc.py and signal_proc.extract_ppg_hr)
#   genuinely disagrees more: two independently-estimated short-window peak rates naturally
#   drift apart by several bpm even when both are honest. Scoring real sensor noise against
#   the synthetic path's tight std would flag genuine patients as suspicious routinely —
#   verified against real BIDMC data during development (see docs/mistakes-log.md).
_CROSS_SENSOR_EXPECTED_STD_BPM_SYNTHETIC = 2.0
_CROSS_SENSOR_EXPECTED_STD_BPM_REAL = 5.0

# Weights for combining the baseline-deviation and sudden-change components of the
# temporal score. Sudden change is weighted higher: a patient's rhythm drifting slowly over
# many sessions is normal; an abrupt within-session jump is the signature an attack leaves.
_W_BASELINE_DEVIATION = 0.4
_W_SUDDEN_CHANGE = 0.6

# Combining temporal vs. cross-sensor into the final score.
_W_TEMPORAL = 0.6
_W_CROSS_SENSOR = 0.4

# Verdict thresholds on the final combined z-score-like value.
_SUSPICIOUS_THRESHOLD = 2.0
_MANIPULATED_THRESHOLD = 3.5


class Verdict(str, Enum):
    GENUINE = "genuine"
    SUSPICIOUS = "suspicious"
    MANIPULATED = "manipulated"


@dataclass
class DetectionResult:
    baseline_deviation: float
    sudden_change: float
    temporal_score: float
    cross_sensor_score: float
    combined_score: float
    verdict: Verdict

    def to_dict(self) -> dict:
        return {
            "baseline_deviation": self.baseline_deviation,
            "sudden_change": self.sudden_change,
            "temporal_score": self.temporal_score,
            "cross_sensor_score": self.cross_sensor_score,
            "combined_score": self.combined_score,
            "verdict": self.verdict.value,
        }


def _zscore(value: float, mean: float, std: float) -> float:
    return abs(value - mean) / std if std > 0 else 0.0


def _baseline_deviation(features: WindowFeatures, baseline: BaselineProfile) -> float:
    if features.n_beats < 2:
        return 0.0
    z_hr = _zscore(features.heart_rate_bpm, baseline.hr_mean, baseline.hr_std)
    z_rr = _zscore(features.rr_mean_sec, baseline.rr_mean, baseline.rr_std)
    z_amp = _zscore(features.qrs_amplitude_mean, baseline.amp_mean, baseline.amp_std)
    return float(0.4 * z_hr + 0.3 * z_rr + 0.3 * z_amp)


def _sudden_change(features: WindowFeatures, history: list[WindowFeatures]) -> float:
    """Deviation from the patient's own last few windows, independent of their long-run
    baseline — catches an abrupt change even if it hasn't yet pulled the patient outside
    their historical normal range."""
    usable = [h for h in history if h.n_beats >= 2]
    if len(usable) < 3 or features.n_beats < 2:
        return 0.0

    hr_hist = np.array([h.heart_rate_bpm for h in usable])
    rr_hist = np.array([h.rr_mean_sec for h in usable])
    amp_hist = np.array([h.qrs_amplitude_mean for h in usable])

    z_hr = _zscore(features.heart_rate_bpm, float(np.mean(hr_hist)), max(float(np.std(hr_hist)), 2.0))
    z_rr = _zscore(features.rr_mean_sec, float(np.mean(rr_hist)), max(float(np.std(rr_hist)), 0.02))
    z_amp = _zscore(features.qrs_amplitude_mean, float(np.mean(amp_hist)), max(float(np.std(amp_hist)), 0.03))
    return float(0.4 * z_hr + 0.3 * z_rr + 0.3 * z_amp)


def _cross_sensor_score(ecg_hr_bpm: float, secondary_hr_bpm: float, expected_std_bpm: float) -> float:
    # secondary_hr_bpm == 0.0 means "no reading this window" (see signal_proc.extract_ppg_hr
    # for the real-sensor case) — score 0 rather than treating a missing reading as a huge
    # disagreement, same as the ECG side already does for ecg_hr_bpm.
    #
    # An earlier version also zeroed this out whenever the ECG side had fewer than 3 beats
    # in the window, to guard against the same short-window fragility fixed for PPG. That
    # backfired: the RR-interval-stretch attack itself legitimately reduces the apparent beat
    # count (time-warping the window), so the gate silently defeated detection of that attack
    # on low-sample-rate (BIDMC) records. See docs/mistakes-log.md. Record selection, not a
    # detector-logic gate, is how the remaining rare false positive on noisy real data is
    # handled — see config.DEFAULT_BIDMC_RECORDS.
    if ecg_hr_bpm <= 0 or secondary_hr_bpm <= 0:
        return 0.0
    return _zscore(ecg_hr_bpm, secondary_hr_bpm, expected_std_bpm)


def _verdict_from_score(score: float) -> Verdict:
    if score >= _MANIPULATED_THRESHOLD:
        return Verdict.MANIPULATED
    if score >= _SUSPICIOUS_THRESHOLD:
        return Verdict.SUSPICIOUS
    return Verdict.GENUINE


def score_window(
    features: WindowFeatures,
    baseline: BaselineProfile,
    history: list[WindowFeatures],
    secondary_hr_bpm: float,
    cross_sensor_is_real: bool = False,
) -> DetectionResult:
    baseline_dev = _baseline_deviation(features, baseline)
    sudden = _sudden_change(features, history)
    temporal = _W_BASELINE_DEVIATION * baseline_dev + _W_SUDDEN_CHANGE * sudden
    expected_std = _CROSS_SENSOR_EXPECTED_STD_BPM_REAL if cross_sensor_is_real else _CROSS_SENSOR_EXPECTED_STD_BPM_SYNTHETIC
    cross_sensor = _cross_sensor_score(features.heart_rate_bpm, secondary_hr_bpm, expected_std)
    combined = _W_TEMPORAL * temporal + _W_CROSS_SENSOR * cross_sensor

    return DetectionResult(
        baseline_deviation=baseline_dev,
        sudden_change=sudden,
        temporal_score=temporal,
        cross_sensor_score=cross_sensor,
        combined_score=combined,
        verdict=_verdict_from_score(combined),
    )
