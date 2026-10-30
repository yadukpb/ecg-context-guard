"""Preprocessing, R-peak detection, and feature extraction for one ECG window.

This is the "Preprocessing & Noise Removal" and "Patient Baseline / Temporal Analysis" input
stage from the slides' workflow. R-peak detection follows the classic Pan-Tompkins recipe
(bandpass -> derivative -> square -> moving-window integrate -> peak-pick), simplified to work
well on short (2s) windows rather than a full continuous recording.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sps


def bandpass_filter(x: np.ndarray, fs: int, low: float = 0.5, high: float = 40.0) -> np.ndarray:
    """General-purpose noise removal: keep the 0.5-40Hz band ECG signal content lives in."""
    nyq = fs / 2
    b, a = sps.butter(4, [low / nyq, high / nyq], btype="bandpass")
    return sps.filtfilt(b, a, x)


def remove_baseline_wander(x: np.ndarray, fs: int, cutoff: float = 0.5) -> np.ndarray:
    """Strip slow drift (respiration, electrode motion) below `cutoff` Hz."""
    nyq = fs / 2
    b, a = sps.butter(2, cutoff / nyq, btype="highpass")
    return sps.filtfilt(b, a, x)


def preprocess(raw: np.ndarray, fs: int) -> np.ndarray:
    """Full preprocessing step applied to every incoming window before anything else sees it."""
    x = remove_baseline_wander(raw, fs)
    x = bandpass_filter(x, fs)
    return x


def detect_r_peaks(x: np.ndarray, fs: int) -> np.ndarray:
    """Simplified Pan-Tompkins R-peak detector. Returns sample indices of detected peaks."""
    nyq = fs / 2
    b, a = sps.butter(2, [5 / nyq, 15 / nyq], btype="bandpass")
    filtered = sps.filtfilt(b, a, x)

    derivative = np.diff(filtered, prepend=filtered[0])
    squared = derivative ** 2

    window_samples = max(1, int(0.15 * fs))  # ~150ms integration window
    integrated = np.convolve(squared, np.ones(window_samples) / window_samples, mode="same")

    # Refractory period: two real heartbeats can't be closer than ~300ms (200bpm cap).
    min_distance = max(1, int(0.3 * fs))
    threshold = 0.35 * np.max(integrated) if np.max(integrated) > 0 else 0
    peaks, _ = sps.find_peaks(integrated, distance=min_distance, height=threshold)
    return peaks


def detect_ppg_peaks(x: np.ndarray, fs: int) -> np.ndarray:
    """Peak-detect a PPG (pulse-oximeter) waveform to find individual pulse beats.

    PPG pulses are slower and broader than an ECG's QRS complex (no sharp spike to key off),
    so this keeps only the 0.5-8Hz band a resting-to-elevated pulse rate (30-240bpm) lives in,
    rather than reusing the ECG detector's 5-15Hz QRS-tuned filter.
    """
    nyq = fs / 2
    b, a = sps.butter(2, [0.5 / nyq, 8.0 / nyq], btype="bandpass")
    filtered = sps.filtfilt(b, a, x)

    min_distance = max(1, int(0.3 * fs))  # same 200bpm refractory cap as the ECG detector
    threshold = 0.3 * np.max(np.abs(filtered)) if np.max(np.abs(filtered)) > 0 else 0
    peaks, _ = sps.find_peaks(filtered, distance=min_distance, height=threshold)
    return peaks


# Real PPG is noisier than ECG (motion artifact, poor perfusion, dicrotic-notch
# double-counting) — a single missed or doubled peak in a 2s window swings the computed
# rate a lot. Require at least 2 intervals (3 peaks) before trusting a reading at all, same
# principle as the ECG path's "too few beats, say nothing" rule just with a stricter bar for
# the noisier signal.
_MIN_PPG_PEAKS = 3
_PLAUSIBLE_HR_RANGE = (30.0, 220.0)


def extract_ppg_hr(x: np.ndarray, fs: int) -> float:
    """Pulse rate from a real PPG window, independently of anything the ECG pipeline
    computed — this is what makes it a genuine cross-sensor reading rather than a derived
    one. Returns 0.0 ("no reliable reading this window") rather than guessing when the
    signal is too sparse or the result implausible — the same honest-abstention behavior a
    real pulse oximeter shows on a poor-perfusion finger, instead of reporting a number.

    This range check alone won't catch every artifact (e.g. a dicrotic notch mistaken for a
    second beat can double the rate into another still-plausible value) — the streamer layer
    additionally rejects a reading that jumps implausibly from this same patient's last
    accepted reading, which the range check can't see since it has no memory between
    windows. See streamer.py's continuity check.
    """
    peaks = detect_ppg_peaks(x, fs)
    if len(peaks) < _MIN_PPG_PEAKS:
        return 0.0
    intervals_sec = np.diff(peaks) / fs
    # Median, not mean: resists the one-off long interval a single missed peak produces.
    hr = float(60.0 / np.median(intervals_sec))
    if not (_PLAUSIBLE_HR_RANGE[0] <= hr <= _PLAUSIBLE_HR_RANGE[1]):
        return 0.0
    return hr


@dataclass
class WindowFeatures:
    n_beats: int
    heart_rate_bpm: float
    rr_mean_sec: float
    rr_std_sec: float
    qrs_amplitude_mean: float
    qrs_amplitude_std: float

    def to_dict(self) -> dict:
        return {
            "n_beats": self.n_beats,
            "heart_rate_bpm": self.heart_rate_bpm,
            "rr_mean_sec": self.rr_mean_sec,
            "rr_std_sec": self.rr_std_sec,
            "qrs_amplitude_mean": self.qrs_amplitude_mean,
            "qrs_amplitude_std": self.qrs_amplitude_std,
        }


def extract_features(x: np.ndarray, fs: int) -> WindowFeatures:
    """Turn one preprocessed window into the small feature set the detector reasons about."""
    peaks = detect_r_peaks(x, fs)

    if len(peaks) < 2:
        # Too few beats in this window to say anything about rate/rhythm. Still report
        # amplitude stats so the caller has *something* to compare.
        return WindowFeatures(
            n_beats=len(peaks),
            heart_rate_bpm=0.0,
            rr_mean_sec=0.0,
            rr_std_sec=0.0,
            qrs_amplitude_mean=float(np.mean(np.abs(x))),
            qrs_amplitude_std=float(np.std(x)),
        )

    rr_intervals_sec = np.diff(peaks) / fs
    heart_rate_bpm = 60.0 / np.mean(rr_intervals_sec)
    amplitudes = x[peaks]

    return WindowFeatures(
        n_beats=len(peaks),
        heart_rate_bpm=float(heart_rate_bpm),
        rr_mean_sec=float(np.mean(rr_intervals_sec)),
        rr_std_sec=float(np.std(rr_intervals_sec)) if len(rr_intervals_sec) > 1 else 0.0,
        qrs_amplitude_mean=float(np.mean(amplitudes)),
        qrs_amplitude_std=float(np.std(amplitudes)) if len(amplitudes) > 1 else 0.0,
    )
