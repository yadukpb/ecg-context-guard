"""Synthetic second vital-sign channel, standing in for e.g. a pulse oximeter's HR reading.

MIT-BIH only has ECG channels, so there is no real second sensor to cross-check against.
This is a disclosed limitation (see docs/building/05-detection-algorithm.md) — we generate a
plausible secondary HR reading that tracks the *true, pre-attack* physiology with its own
independent small noise and slow drift. The point: an attacker who tampers only with the ECG
channel cannot also retroactively tamper with this independent reading, so comparing the two
gives the detector a cross-sensor consistency signal even though both ultimately derive from
the same dataset.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class CrossSensorState:
    """Per-patient slowly-drifting offset between the two 'sensors', so the mismatch isn't
    just independent noise every window (a real second sensor has its own smooth trend)."""

    bias_bpm: float = 0.0
    rng_seed: int = 0

    def _rng(self) -> random.Random:
        return random.Random(self.rng_seed)


def new_state(patient_id: str) -> CrossSensorState:
    return CrossSensorState(bias_bpm=0.0, rng_seed=abs(hash(patient_id)) % (2**31))


def next_secondary_hr(true_hr_bpm: float, state: CrossSensorState) -> tuple[float, CrossSensorState]:
    """Advance the synthetic secondary-sensor reading by one window."""
    rng = state._rng()
    # Slow random walk in the bias (independent sensor calibration drift), small per-window
    # measurement noise on top. Bounded so it never drifts into physiologically silly values.
    drift = rng.uniform(-0.15, 0.15)
    new_bias = max(-2.5, min(2.5, state.bias_bpm + drift))
    noise = rng.gauss(0, 0.6)
    secondary_hr = true_hr_bpm + new_bias + noise

    next_state = CrossSensorState(bias_bpm=new_bias, rng_seed=(state.rng_seed + 1) % (2**31))
    return secondary_hr, next_state
