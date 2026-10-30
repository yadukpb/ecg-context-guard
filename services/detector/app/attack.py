"""Attack simulation — the slides' "Attack Simulation" module.

These deliberately do NOT add random noise or push values out of range (that's exactly the
kind of attack naive threshold detectors already catch, per the literature-review gap the
slides identify). Instead each attack type keeps the signal "clinically plausible" while
being wrong, by construction:

- ``amplitude_drift``:  QRS amplitude is scaled up/down smoothly across the window. A real
  heart doesn't change electrode contact/amplitude abruptly, but the *values themselves*
  stay within a normal ECG's amplitude range — still "plausible" in isolation.
- ``rr_stretch``:  the window is time-warped so beats land closer together or farther apart
  than they actually occurred, i.e. a fabricated heart-rate change, while every individual
  sample value is untouched (it's the same real waveform, just resampled in time).
- ``segment_replay``:  the second half of the window is overwritten with a copy of the first
  half. Every value is a real, previously-genuine sample — but exact repetition like this
  doesn't happen in a real heartbeat and shows up as an anomaly in temporal/rhythm analysis.

``intensity`` is a 0-1 knob controlling how aggressive the manipulation is, clamped so even
at intensity=1 the result stays inside documented "plausible" bounds.
"""
from __future__ import annotations

from enum import Enum

import numpy as np
from scipy.signal import resample


class AttackType(str, Enum):
    NONE = "none"
    AMPLITUDE_DRIFT = "amplitude_drift"
    RR_STRETCH = "rr_stretch"
    SEGMENT_REPLAY = "segment_replay"


# Bounds chosen so the manipulated signal stays within what a clinician would consider a
# plausible single reading, even at full intensity.
_MAX_AMPLITUDE_SCALE_DELTA = 0.18  # up to +/-18% amplitude scaling
_MAX_TIME_WARP = 0.20  # up to +/-20% effective RR stretch/compression


def apply_attack(window: np.ndarray, attack_type: AttackType, intensity: float) -> np.ndarray:
    intensity = max(0.0, min(1.0, intensity))

    if attack_type == AttackType.NONE:
        return window

    if attack_type == AttackType.AMPLITUDE_DRIFT:
        n = len(window)
        delta = _MAX_AMPLITUDE_SCALE_DELTA * intensity
        ramp = np.linspace(1.0, 1.0 + delta, n)
        return window * ramp

    if attack_type == AttackType.RR_STRETCH:
        n = len(window)
        warp = 1.0 + _MAX_TIME_WARP * intensity
        stretched = resample(window, int(n * warp))
        if len(stretched) >= n:
            return stretched[:n]
        return np.pad(stretched, (0, n - len(stretched)), mode="edge")

    if attack_type == AttackType.SEGMENT_REPLAY:
        n = len(window)
        half = n // 2
        out = window.copy()
        out[half:] = window[: n - half]
        return out

    raise ValueError(f"Unknown attack type: {attack_type}")
