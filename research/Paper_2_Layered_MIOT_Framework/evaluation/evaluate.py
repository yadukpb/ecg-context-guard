"""THECF validation against real MIT-BIH (clean) + NSTDB (noisy) windows."""
from __future__ import annotations

import numpy as np

from Common.datasets import mitdb, nstdb
from Paper_2_Layered_MIOT_Framework.THECF import calibrate, thecf

WINDOW_SECONDS = 1.0


def _build_template(record_names: list[str], n_beats: int = 100) -> np.ndarray:
    beats = []
    for record_name in record_names:
        signal, fs = mitdb.lead_signal(record_name)
        ann = mitdb.get_annotation(record_name)
        for sample, symbol in zip(ann.sample, ann.symbol):
            if symbol != "N":
                continue
            lo, hi = sample - int(0.1 * fs), sample + int(0.2 * fs)
            if lo < 0 or hi > len(signal):
                continue
            beats.append(signal[lo:hi])
            if len(beats) >= n_beats:
                return thecf.build_healthy_template(beats)
    return thecf.build_healthy_template(beats)


def _windows(signal: np.ndarray, fs: float) -> list[np.ndarray]:
    win_len = int(WINDOW_SECONDS * fs)
    return [signal[i:i + win_len] for i in range(0, len(signal) - win_len, win_len)]


def run_thecf_validation(
    template_records: list[str], clean_records: list[str], noise_types: list[str] = ("bw", "em", "ma"),
    thresholds: thecf.Thresholds = thecf.PAPER_THRESHOLDS,
) -> dict:
    template = _build_template(template_records)

    clean_pass = []
    for record_name in clean_records:
        signal, fs = mitdb.lead_signal(record_name)
        for window in _windows(signal, fs):
            clean_pass.append(thecf.evaluate(window, fs, template, thresholds).passed)
    clean_accuracy = float(np.mean(clean_pass)) if clean_pass else float("nan")

    noisy_fail_by_type = {}
    for noise_type in noise_types:
        noise, noise_fs = nstdb.noise_trace(noise_type)
        signal, fs = mitdb.lead_signal(clean_records[0])
        if noise_fs != fs:
            continue  # sampling-rate mismatch for this pairing; skip rather than silently resample-guess
        n = min(len(signal), len(noise))
        noisy_signal = signal[:n] + noise[:n] * 3.0  # strong injected noise, by construction "faulty"
        results = [not thecf.evaluate(w, fs, template, thresholds).passed for w in _windows(noisy_signal, fs)]
        noisy_fail_by_type[noise_type] = float(np.mean(results)) if results else float("nan")

    return {
        "clean_pass_rate": clean_accuracy,
        "noisy_detected_rate_by_type": noisy_fail_by_type,
    }


def run_thecf_comparison(
    template_records: list[str], clean_records: list[str], noise_types: list[str] = ("bw", "em", "ma"),
    calibration_records: list[str] | None = None,
) -> dict:
    """Report both the paper's literal published thresholds and thresholds re-derived from
    our own real data (paper's own stated method: mean +/- 2*std) side by side — the honest
    way to show both "what happens if you take their numbers literally" and "what happens if
    you re-derive them our own way," without erasing the earlier (literal) finding."""
    calibration = calibrate.calibrate_thresholds(
        record_names=calibration_records or calibrate.CALIBRATION_RECORDS,
    )

    literal = run_thecf_validation(template_records, clean_records, noise_types, thecf.PAPER_THRESHOLDS)
    calibrated = run_thecf_validation(template_records, clean_records, noise_types, calibration.thresholds)

    return {
        "literal_paper_thresholds": literal,
        "calibrated_thresholds": calibrated,
        "calibration_derivation": {
            "n_clean_windows": calibration.n_clean_windows,
            "energy_mean": calibration.energy_mean, "energy_std": calibration.energy_std,
            "qrs_ratio_mean": calibration.qrs_ratio_mean, "qrs_ratio_std": calibration.qrs_ratio_std,
            "ncc_mean": calibration.ncc_mean, "ncc_std": calibration.ncc_std,
            "thresholds": {
                "energy_low": calibration.thresholds.energy_low, "energy_high": calibration.thresholds.energy_high,
                "qrs_ratio_low": calibration.thresholds.qrs_ratio_low,
                "qrs_ratio_high": calibration.thresholds.qrs_ratio_high,
                "ncc_accept": calibration.thresholds.ncc_accept,
            },
        },
    }
