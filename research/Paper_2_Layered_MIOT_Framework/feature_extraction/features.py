"""32 morphological + statistical features per beat, for the HGAN-SVM-DT stage.

The paper attributes its 32-feature set to "Discrete Wavelet Transform (DWT) and the MB
Assiouni method" (Table 1: "Properties of Multi-Scale Wavelet Transform" + "Morphology-Based
Features"). No further citation for "MB Assiouni" could be found anywhere checked during the
feasibility pass (see research/FEASIBILITY_REPORT.md section 15/17) — it is not a method this
implementation recovers. What follows is a **documented, justified substitute 32-feature set**
built from the same two named categories (DWT statistics + beat morphology), not a
reconstruction of the original paper's exact feature list.

Beat delineation here is a simplified, fixed-offset heuristic around a given R-peak sample
index (typical physiological P/QRS/T search windows scaled by sampling rate) — not a
clinical-grade ECG delineator. Good enough to produce 32 real, varying numbers per beat for a
reproduction pipeline; not a diagnostic-quality feature extractor.
"""
from __future__ import annotations

import numpy as np
import pywt

DWT_WAVELET = "db4"
DWT_LEVEL = 4  # -> 5 subbands (cA4, cD4, cD3, cD2, cD1)

FEATURE_NAMES = (
    [f"dwt_{band}_{stat}" for band in ["cA4", "cD4", "cD3", "cD2", "cD1"]
     for stat in ["energy", "variance", "std", "waveform_length"]]
    + [
        "r_amplitude", "q_amplitude", "s_amplitude", "p_amplitude", "t_amplitude",
        "qrs_duration_ms", "pr_interval_ms", "st_segment_ms", "qt_interval_ms",
        "rr_prev_ms", "rr_next_ms", "heart_rate_bpm",
    ]
)
assert len(FEATURE_NAMES) == 32


def _dwt_features(beat: np.ndarray) -> list[float]:
    coeffs = pywt.wavedec(beat, DWT_WAVELET, level=DWT_LEVEL)
    feats: list[float] = []
    for band in coeffs:
        band = band.astype(np.float64)
        energy = float(np.sum(band**2))
        variance = float(np.var(band))
        std = float(np.std(band))
        waveform_length = float(np.sum(np.abs(np.diff(band))))
        feats.extend([energy, variance, std, waveform_length])
    return feats


def _search_extremum(signal: np.ndarray, lo: int, hi: int, mode: str) -> tuple[int, float]:
    lo, hi = max(0, lo), min(len(signal), hi)
    if hi <= lo:
        return lo, float(signal[min(lo, len(signal) - 1)])
    segment = signal[lo:hi]
    idx = int(np.argmax(segment)) if mode == "max" else int(np.argmin(segment))
    return lo + idx, float(segment[idx])


def _morphology_features(
    signal: np.ndarray, fs: float, r_index: int, prev_rr_samples: int | None,
    next_rr_samples: int | None,
) -> list[float]:
    ms = lambda samples: 1000.0 * samples / fs  # noqa: E731

    r_amp = float(signal[r_index])
    q_idx, q_amp = _search_extremum(signal, r_index - int(0.04 * fs), r_index, "min")
    s_idx, s_amp = _search_extremum(signal, r_index, r_index + int(0.04 * fs), "min")
    p_idx, p_amp = _search_extremum(
        signal, r_index - int(0.20 * fs), r_index - int(0.08 * fs), "max"
    )
    t_idx, t_amp = _search_extremum(
        signal, r_index + int(0.10 * fs), r_index + int(0.40 * fs), "max"
    )

    qrs_duration = ms(s_idx - q_idx)
    pr_interval = ms(r_index - p_idx)
    st_segment = ms(t_idx - s_idx)
    qt_interval = ms(t_idx - q_idx)

    rr_prev = ms(prev_rr_samples) if prev_rr_samples else float("nan")
    rr_next = ms(next_rr_samples) if next_rr_samples else float("nan")
    hr = 60000.0 / rr_prev if prev_rr_samples else float("nan")

    return [
        r_amp, q_amp, s_amp, p_amp, t_amp,
        qrs_duration, pr_interval, st_segment, qt_interval,
        rr_prev, rr_next, hr,
    ]


def extract_features(
    signal: np.ndarray,
    fs: float,
    r_index: int,
    beat_window: tuple[int, int],
    prev_rr_samples: int | None = None,
    next_rr_samples: int | None = None,
) -> np.ndarray:
    """32-dim feature vector for one beat centred at ``r_index`` in ``signal``.

    ``beat_window`` = (samples_before_r, samples_after_r) defines the DWT input segment.
    """
    lo, hi = r_index - beat_window[0], r_index + beat_window[1]
    beat = signal[max(0, lo): min(len(signal), hi)]
    if len(beat) < 2 ** DWT_LEVEL:
        beat = np.pad(beat, (0, 2 ** DWT_LEVEL - len(beat)), mode="edge")

    dwt_feats = _dwt_features(beat)
    morph_feats = _morphology_features(signal, fs, r_index, prev_rr_samples, next_rr_samples)
    return np.array(dwt_feats + morph_feats, dtype=np.float64)
