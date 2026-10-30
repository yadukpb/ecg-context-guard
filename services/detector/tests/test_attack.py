import numpy as np

from app.attack import AttackType, apply_attack, _MAX_AMPLITUDE_SCALE_DELTA


def test_no_attack_is_identity(genuine_window):
    out = apply_attack(genuine_window, AttackType.NONE, intensity=1.0)
    assert np.array_equal(out, genuine_window)


def test_amplitude_drift_stays_within_documented_bounds(genuine_window):
    out = apply_attack(genuine_window, AttackType.AMPLITUDE_DRIFT, intensity=1.0)
    ratio = np.abs(out) / (np.abs(genuine_window) + 1e-9)
    # Every sample's scale factor must stay within the documented clinically-plausible bound.
    assert np.all(ratio <= 1 + _MAX_AMPLITUDE_SCALE_DELTA + 1e-6)


def test_rr_stretch_preserves_window_length(genuine_window):
    out = apply_attack(genuine_window, AttackType.RR_STRETCH, intensity=1.0)
    assert len(out) == len(genuine_window)


def test_segment_replay_duplicates_first_half(genuine_window):
    out = apply_attack(genuine_window, AttackType.SEGMENT_REPLAY, intensity=1.0)
    n = len(genuine_window)
    half = n // 2
    assert np.array_equal(out[half:], genuine_window[: n - half])
    # And the first half is untouched.
    assert np.array_equal(out[:half], genuine_window[:half])
