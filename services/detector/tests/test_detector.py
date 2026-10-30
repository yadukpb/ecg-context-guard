"""Detector-logic tests: the core claim of the whole project — that a held-out genuine
window reads as `genuine`, and the same window with a "clinically plausible" attack applied
reads as `suspicious`/`manipulated`.
"""
from app.attack import AttackType, apply_attack
from app.baseline import BaselineBuilder
from app.config import FS_HZ
from app.detector import Verdict, score_window
from app.signal_proc import extract_features


def _build_baseline_and_history(calibration_windows):
    builder = BaselineBuilder()
    for w in calibration_windows[:15]:
        builder.add(extract_features(w, FS_HZ))
    baseline = builder.build()

    history = [extract_features(w, FS_HZ) for w in calibration_windows[15:25]]
    return baseline, history


def test_genuine_held_out_window_is_not_flagged(calibration_windows):
    baseline, history = _build_baseline_and_history(calibration_windows)
    held_out = calibration_windows[25]
    features = extract_features(held_out, FS_HZ)

    result = score_window(features, baseline, history, secondary_hr_bpm=features.heart_rate_bpm)

    assert result.verdict == Verdict.GENUINE


def test_segment_replay_attack_is_flagged(calibration_windows):
    baseline, history = _build_baseline_and_history(calibration_windows)
    held_out = calibration_windows[25]
    genuine_features = extract_features(held_out, FS_HZ)

    attacked = apply_attack(held_out, AttackType.SEGMENT_REPLAY, intensity=1.0)
    attacked_features = extract_features(attacked, FS_HZ)

    # Secondary vital reflects the *true* pre-attack physiology (independent sensor) — the
    # attacker only compromised the ECG channel, per the attack model in the slides.
    result = score_window(
        attacked_features, baseline, history, secondary_hr_bpm=genuine_features.heart_rate_bpm
    )

    assert result.verdict in (Verdict.SUSPICIOUS, Verdict.MANIPULATED)


def test_rr_stretch_attack_is_flagged(calibration_windows):
    baseline, history = _build_baseline_and_history(calibration_windows)
    held_out = calibration_windows[25]
    genuine_features = extract_features(held_out, FS_HZ)

    attacked = apply_attack(held_out, AttackType.RR_STRETCH, intensity=1.0)
    attacked_features = extract_features(attacked, FS_HZ)

    result = score_window(
        attacked_features, baseline, history, secondary_hr_bpm=genuine_features.heart_rate_bpm
    )

    assert result.verdict in (Verdict.SUSPICIOUS, Verdict.MANIPULATED)
