"""Build the per-window dataset (THECF input, HGAN-SVM-DT features, CNN images) from MIT-BIH.

Paper 2 divides recordings into 10-second windows uniformly for both stages (its own
"Input data preprocessing details" section). Each window gets:
- a detection label (normal/abnormal) for THECF/HGAN-SVM-DT,
- a classification label (one of 7 classes, or excluded) for the CNN stage,
- the sample index of the beat nearest the window's centre, used as the ``r_index`` for
  32-feature extraction (``feature_extraction.features``) and as the image's beat anchor.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from Common.datasets import mitdb
from Paper_2_Layered_MIOT_Framework.training.labels import (
    build_record_labels, classification_label, detection_label,
)

WINDOW_SECONDS = 10.0


@dataclass
class Window:
    record: str
    start: int
    end: int
    fs: float
    r_index: int | None
    rr_prev_samples: int | None
    rr_next_samples: int | None
    detection: int
    classification: str | None


def _nearest_beat_with_neighbors(labels, start: int, end: int) -> tuple[int | None, int | None, int | None]:
    """Representative beat for this window (closest to its centre) plus its RR distances to
    the immediately preceding and following beats in the *whole record* (not just this
    window), needed for the morphology features' rr_prev/rr_next/heart_rate columns."""
    in_window = labels.beat_samples[(labels.beat_samples >= start) & (labels.beat_samples < end)]
    if len(in_window) == 0:
        return None, None, None
    centre = (start + end) // 2
    r_index = int(in_window[np.argmin(np.abs(in_window - centre))])

    all_beats = labels.beat_samples
    pos = int(np.searchsorted(all_beats, r_index))
    rr_prev = int(r_index - all_beats[pos - 1]) if pos > 0 else None
    rr_next = int(all_beats[pos + 1] - r_index) if pos + 1 < len(all_beats) else None
    return r_index, rr_prev, rr_next


def windows_for_record(record_name: str) -> list[Window]:
    signal, fs = mitdb.lead_signal(record_name)
    ann = mitdb.get_annotation(record_name)
    labels = build_record_labels(ann)

    win_len = int(WINDOW_SECONDS * fs)
    windows = []
    for start in range(0, len(signal) - win_len, win_len):
        end = start + win_len
        r_index, rr_prev, rr_next = _nearest_beat_with_neighbors(labels, start, end)
        windows.append(Window(
            record=record_name, start=start, end=end, fs=fs, r_index=r_index,
            rr_prev_samples=rr_prev, rr_next_samples=rr_next,
            detection=detection_label(labels, start, end),
            classification=classification_label(labels, start, end),
        ))
    return windows


def build_dataset(record_names: list[str]) -> list[Window]:
    all_windows: list[Window] = []
    for record_name in record_names:
        all_windows.extend(windows_for_record(record_name))
    return all_windows
