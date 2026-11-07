"""Empirically re-derive THECF's three gate thresholds from real data.

The paper's own methodology states its thresholds were derived from statistical analysis of
real windows (explicitly: mean +/- 2*std for layer 3's NCC threshold; the same logic is the
only non-arbitrary way to read layers 1-2 too). Two independent measurements on real MIT-BIH
(scipy Butterworth+filtfilt, and a raw FFT band-power calculation, across records 100/101/
103/118) already confirmed the paper's *literal published* QRS-band-ratio range [0.18, 0.85]
does not hold under a whole-1-second-window convention — real clean windows measure ~0.2-1.3%
QRS-band energy, not ~42%. Rather than hard-code numbers that may assume a different window
definition we can't recover from the paper's text, this module re-derives thresholds the
paper's own stated way, from our own real data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from Common.datasets import mitdb
from Paper_2_Layered_MIOT_Framework.THECF import thecf

WINDOW_SECONDS = 1.0

# Bounded record subset so calibration finishes in minutes, not hours, while still
# comfortably clearing ~1,000 windows (paper's own validation used ~12,000, scoped down here
# per the compute-budget discipline — see FEASIBILITY_REPORT.md).
CALIBRATION_RECORDS = [
    "100", "101", "102", "103", "104", "105", "106", "107", "108", "109",
    "111", "112", "113", "114", "115", "116", "117", "118", "119", "121",
]


@dataclass
class CalibrationReport:
    thresholds: thecf.Thresholds
    n_clean_windows: int
    energy_mean: float
    energy_std: float
    qrs_ratio_mean: float
    qrs_ratio_std: float
    ncc_mean: float
    ncc_std: float


def _windows(signal: np.ndarray, fs: float) -> list[np.ndarray]:
    win_len = int(WINDOW_SECONDS * fs)
    return [signal[i:i + win_len] for i in range(0, len(signal) - win_len, win_len)]


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


def calibrate_thresholds(
    record_names: list[str] = CALIBRATION_RECORDS, template_records: list[str] | None = None,
) -> CalibrationReport:
    """Derive thresholds from real clean-window statistics: mean +/- 2*std, matching the
    paper's own stated layer-3 method, applied consistently to all three layers."""
    template_records = template_records or record_names[:3]
    template = _build_template(template_records)

    energies, qrs_ratios, nccs = [], [], []
    for record_name in record_names:
        signal, fs = mitdb.lead_signal(record_name)
        for window in _windows(signal, fs):
            energies.append(thecf.total_energy(window))
            qrs_ratios.append(thecf.qrs_band_energy_ratio(window, fs))
            nccs.append(thecf.normalized_cross_correlation(window, template))

    energies_arr, qrs_arr, ncc_arr = np.array(energies), np.array(qrs_ratios), np.array(nccs)

    e_mean, e_std = float(energies_arr.mean()), float(energies_arr.std())
    q_mean, q_std = float(qrs_arr.mean()), float(qrs_arr.std())
    n_mean, n_std = float(ncc_arr.mean()), float(ncc_arr.std())

    thresholds = thecf.Thresholds(
        energy_low=max(0.0, e_mean - 2 * e_std),
        energy_high=e_mean + 2 * e_std,
        qrs_ratio_low=max(0.0, q_mean - 2 * q_std),
        qrs_ratio_high=q_mean + 2 * q_std,
        # NCC is one-sided in the paper's own layer-3 definition (accept >= threshold) —
        # mean - 2*std keeps the paper's own "reject the low tail" logic for this layer.
        ncc_accept=max(0.0, n_mean - 2 * n_std),
    )

    return CalibrationReport(
        thresholds=thresholds,
        n_clean_windows=len(energies_arr),
        energy_mean=e_mean, energy_std=e_std,
        qrs_ratio_mean=q_mean, qrs_ratio_std=q_std,
        ncc_mean=n_mean, ncc_std=n_std,
    )


if __name__ == "__main__":
    import json

    report = calibrate_thresholds()
    print(json.dumps({
        "n_clean_windows": report.n_clean_windows,
        "energy_mean": report.energy_mean, "energy_std": report.energy_std,
        "qrs_ratio_mean": report.qrs_ratio_mean, "qrs_ratio_std": report.qrs_ratio_std,
        "ncc_mean": report.ncc_mean, "ncc_std": report.ncc_std,
        "calibrated_thresholds": {
            "energy_low": report.thresholds.energy_low, "energy_high": report.thresholds.energy_high,
            "qrs_ratio_low": report.thresholds.qrs_ratio_low, "qrs_ratio_high": report.thresholds.qrs_ratio_high,
            "ncc_accept": report.thresholds.ncc_accept,
        },
    }, indent=2))
