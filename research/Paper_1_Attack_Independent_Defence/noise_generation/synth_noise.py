"""Synthetic noisy-ECG generation for Paper 1's binary clean/noisy gatekeeper task.

Injects real BW/EM/MA traces from NSTDB onto clean ECG-ID segments at a controlled SNR,
mirroring the taxonomy in the paper's Table 2 (ECG+BW, ECG+EM, ECG+MA). The paper's own
clean/noisy ground truth was a manual annotation pass by its authors, never released (see
research/FEASIBILITY_REPORT.md section 2/3) — the rule below is **our own re-derivation** of
their stated definition ("noisy if it exhibits BW/EM/MA/PLI; noise-free if QRS and T are
visible"), approximated quantitatively via a noise-energy ratio, not a recovery of their
actual per-segment labels.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, filtfilt

TARGET_FS = 500.0  # paper resamples everything to 500Hz
SEGMENT_SECONDS = 10.0
NOISE_FREE_HF_RATIO_MAX = 0.15  # our rule's cutoff — see module docstring


@dataclass
class NoiseSample:
    segment: np.ndarray
    is_noisy: int  # 0 = clean/noise-free, 1 = noisy — OUR label, not the paper's
    noise_type: str  # "none" | "bw" | "em" | "ma"


def _resample_to(signal: np.ndarray, fs_in: float, fs_out: float) -> np.ndarray:
    if fs_in == fs_out:
        return signal
    from scipy.signal import resample
    n_out = int(len(signal) * fs_out / fs_in)
    return resample(signal, n_out)


def _min_max_normalize(x: np.ndarray) -> np.ndarray:
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def _noise_energy_ratio(segment: np.ndarray, fs: float) -> float:
    """High-frequency-content proxy for 'is the QRS/T shape still visible' — our rule."""
    nyq = fs / 2.0
    b, a = butter(4, min(40.0, nyq - 1) / nyq, btype="highpass")
    hf = filtfilt(b, a, segment)
    total_energy = float(np.mean(segment ** 2)) + 1e-12
    return float(np.mean(hf ** 2)) / total_energy


def label_by_our_rule(segment: np.ndarray, fs: float) -> int:
    return int(_noise_energy_ratio(segment, fs) > NOISE_FREE_HF_RATIO_MAX)


def inject_noise(clean_segment: np.ndarray, noise_trace: np.ndarray, snr_db: float) -> np.ndarray:
    n = min(len(clean_segment), len(noise_trace))
    clean = clean_segment[:n]
    noise = noise_trace[:n]
    signal_power = float(np.mean(clean ** 2)) + 1e-12
    noise_power = float(np.mean(noise ** 2)) + 1e-12
    scale = np.sqrt(signal_power / (noise_power * (10 ** (snr_db / 10))))
    return clean + scale * noise


def build_dataset(
    clean_segments: list[np.ndarray], fs: float, noise_traces: dict[str, np.ndarray],
    noise_fs: float, snr_levels_db: tuple[float, ...] = (0.0, -6.0),
) -> list[NoiseSample]:
    samples: list[NoiseSample] = []
    for seg in clean_segments:
        seg_norm = _min_max_normalize(seg)
        samples.append(NoiseSample(seg_norm, label_by_our_rule(seg, fs), "none"))
        for noise_type, trace in noise_traces.items():
            trace_rs = _resample_to(trace, noise_fs, fs)
            for snr in snr_levels_db:
                noisy = inject_noise(seg, trace_rs, snr)
                samples.append(NoiseSample(_min_max_normalize(noisy), 1, noise_type))
    return samples
