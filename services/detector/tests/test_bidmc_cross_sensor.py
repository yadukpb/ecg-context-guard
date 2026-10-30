"""Real cross-sensor detection tests — BIDMC patients get a genuine PPG-derived secondary
heart rate (see app/bidmc.py, signal_proc.extract_ppg_hr) instead of the synthetic stand-in
MIT-BIH patients use. This file locks in two things found by hand against real PhysioNet
data during development (see docs/mistakes-log.md):

1. The PPG-derived rate actually tracks the ECG-derived rate on genuine data (proves it's a
   real signal, not noise).
2. Scoring a sustained run of genuine, unattacked BIDMC data never crosses the "manipulated"
   threshold — a regression test for a false-positive bug caused by occasional real PPG
   artifacts (dicrotic-notch double-counting, missed beats) before the continuity check and
   wider real-sensor noise tolerance were added.
"""
from app import bidmc
from app.attack import AttackType, apply_attack
from app.baseline import BaselineBuilder
from app.config import BIDMC_FS_HZ, WINDOW_SEC
from app.detector import Verdict, score_window
from app.signal_proc import extract_features, extract_ppg_hr, preprocess
from app.streamer import PatientStream, _real_secondary_hr

WINDOW_SAMPLES = WINDOW_SEC * BIDMC_FS_HZ


def _windows(record_number: str, n: int):
    ecg = bidmc.ecg_signal(record_number)
    ppg = bidmc.ppg_signal(record_number)
    for i in range(n):
        s = i * WINDOW_SAMPLES
        yield ecg[s : s + WINDOW_SAMPLES], ppg[s : s + WINDOW_SAMPLES]


def test_ppg_hr_tracks_ecg_hr_on_genuine_data():
    diffs = []
    for ecg_w, ppg_w in _windows("05", 30):
        features = extract_features(preprocess(ecg_w, BIDMC_FS_HZ), BIDMC_FS_HZ)
        ppg_hr = extract_ppg_hr(ppg_w, BIDMC_FS_HZ)
        if features.heart_rate_bpm > 0 and ppg_hr > 0:
            diffs.append(abs(features.heart_rate_bpm - ppg_hr))

    assert len(diffs) > 15  # most windows should produce a confident reading on clean data
    assert sum(diffs) / len(diffs) < 3.0  # average disagreement well under a few bpm


def test_extract_ppg_hr_abstains_on_flat_signal():
    import numpy as np

    flat = np.zeros(WINDOW_SAMPLES)
    assert extract_ppg_hr(flat, BIDMC_FS_HZ) == 0.0


def test_sustained_genuine_bidmc_stream_never_reads_manipulated():
    """Regression test: replay ~2 minutes of real, unattacked BIDMC data through the exact
    scoring path streamer.py uses, and assert it never flips to `manipulated`. Before the
    continuity check (streamer._real_secondary_hr) and the wider real-sensor noise std were
    added, rare PPG artifacts did occasionally cross the manipulated threshold here."""
    record_number = "05"  # one of the five curated demo BIDMC records — see config.py
    ecg = bidmc.ecg_signal(record_number)
    ppg = bidmc.ppg_signal(record_number)

    builder = BaselineBuilder()
    calibration = []
    for i in range(15):
        s = i * WINDOW_SAMPLES
        calibration.append(preprocess(ecg[s : s + WINDOW_SAMPLES], BIDMC_FS_HZ))
    for w in calibration:
        builder.add(extract_features(w, BIDMC_FS_HZ))
    baseline = builder.build()

    stream = PatientStream(patient_id="test", record_id=f"bidmc:{record_number}")
    history = []
    verdicts = []
    for i in range(15, 75):  # another minute of post-calibration data
        s = i * WINDOW_SAMPLES
        if s + WINDOW_SAMPLES > len(ecg):
            break
        features = extract_features(preprocess(ecg[s : s + WINDOW_SAMPLES], BIDMC_FS_HZ), BIDMC_FS_HZ)
        secondary_hr = _real_secondary_hr(stream, ppg[s : s + WINDOW_SAMPLES], BIDMC_FS_HZ)
        result = score_window(features, baseline, history, secondary_hr, cross_sensor_is_real=True)
        history.append(features)
        verdicts.append(result.verdict)

    assert Verdict.MANIPULATED not in verdicts


def test_attack_on_bidmc_ecg_is_still_flagged_despite_wider_real_sensor_tolerance():
    """The wider noise tolerance for real sensors (vs. the synthetic path) must not blind
    the detector to an actual attack — an attack only touches the transmitted ECG, so the
    real, untouched PPG channel still disagrees sharply with it."""
    record_number = "05"  # one of the five curated demo BIDMC records — see config.py
    ecg = bidmc.ecg_signal(record_number)
    ppg = bidmc.ppg_signal(record_number)

    builder = BaselineBuilder()
    for i in range(15):
        s = i * WINDOW_SAMPLES
        builder.add(extract_features(preprocess(ecg[s : s + WINDOW_SAMPLES], BIDMC_FS_HZ), BIDMC_FS_HZ))
    baseline = builder.build()

    held_out_start = 25 * WINDOW_SAMPLES  # a window with a confident reading on both channels
    genuine = preprocess(ecg[held_out_start : held_out_start + WINDOW_SAMPLES], BIDMC_FS_HZ)
    attacked = apply_attack(genuine, AttackType.RR_STRETCH, intensity=1.0)
    attacked_features = extract_features(attacked, BIDMC_FS_HZ)

    # Real PPG is untouched by the attack — same window as the genuine ECG.
    ppg_window = ppg[held_out_start : held_out_start + WINDOW_SAMPLES]
    secondary_hr = extract_ppg_hr(ppg_window, BIDMC_FS_HZ)

    result = score_window(attacked_features, baseline, [], secondary_hr, cross_sensor_is_real=True)

    assert result.verdict in (Verdict.SUSPICIOUS, Verdict.MANIPULATED)
