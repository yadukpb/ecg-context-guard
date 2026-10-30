"""Patient-specific baseline modeling — the slides' "Patient Baseline Analysis" module.

Instead of a single global "normal ECG" threshold, each patient's first
`CALIBRATION_WINDOWS` windows are used to learn *their own* normal heart-rate, rhythm, and
QRS-amplitude ranges. Everything downstream (temporal analysis, detection) measures
deviation from this patient, not from a population norm.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .signal_proc import WindowFeatures


@dataclass
class BaselineProfile:
    hr_mean: float
    hr_std: float
    rr_mean: float
    rr_std: float
    amp_mean: float
    amp_std: float
    n_calibration_windows: int

    def to_dict(self) -> dict:
        return {
            "hr_mean": self.hr_mean,
            "hr_std": self.hr_std,
            "rr_mean": self.rr_mean,
            "rr_std": self.rr_std,
            "amp_mean": self.amp_mean,
            "amp_std": self.amp_std,
            "n_calibration_windows": self.n_calibration_windows,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BaselineProfile":
        return cls(
            hr_mean=d["hr_mean"],
            hr_std=d["hr_std"],
            rr_mean=d["rr_mean"],
            rr_std=d["rr_std"],
            amp_mean=d["amp_mean"],
            amp_std=d["amp_std"],
            n_calibration_windows=d["n_calibration_windows"],
        )


# A floor on the standard deviations we'll use for z-scoring, so a patient whose calibration
# window happens to be perfectly uniform doesn't produce a baseline so tight that normal
# variation later reads as an extreme z-score (division by ~0).
_MIN_STD = {"hr": 2.0, "rr": 0.02, "amp": 0.03}


@dataclass
class BaselineBuilder:
    """Accumulates calibration-phase window features for one patient, then freezes a
    BaselineProfile once enough windows have been seen."""

    _hr: list[float] = field(default_factory=list)
    _rr: list[float] = field(default_factory=list)
    _amp: list[float] = field(default_factory=list)

    def add(self, features: WindowFeatures) -> None:
        if features.n_beats < 2:
            return  # skip windows too sparse to be representative
        self._hr.append(features.heart_rate_bpm)
        self._rr.append(features.rr_mean_sec)
        self._amp.append(features.qrs_amplitude_mean)

    @property
    def n_windows(self) -> int:
        return len(self._hr)

    def build(self) -> BaselineProfile:
        return BaselineProfile(
            hr_mean=float(np.mean(self._hr)),
            hr_std=max(float(np.std(self._hr)), _MIN_STD["hr"]),
            rr_mean=float(np.mean(self._rr)),
            rr_std=max(float(np.std(self._rr)), _MIN_STD["rr"]),
            amp_mean=float(np.mean(self._amp)),
            amp_std=max(float(np.std(self._amp)), _MIN_STD["amp"]),
            n_calibration_windows=self.n_windows,
        )
