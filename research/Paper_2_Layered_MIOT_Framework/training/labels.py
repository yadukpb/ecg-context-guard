"""Map MIT-BIH beat/rhythm annotations onto the paper's two label sets.

MIT-BIH's own annotation stream carries two different kinds of information, both needed
here (this mapping is not named explicitly in the paper, since MIT-BIH's annotation symbols
don't use the words "Bigeminy"/"Trigeminy" directly — this is our own documented derivation,
stated as such):

1. **Beat symbols** (e.g. ``N``=normal, ``A``=atrial premature, ``V``=PVC, ...) at each beat.
2. **Rhythm annotations** (``aux_note`` on ``+`` markers, e.g. ``(AFIB``, ``(AFL``, ``(B``
   bigeminy, ``(T`` trigeminy, ``(VT`` ventricular tachycardia, ``(N`` normal sinus) that hold
   until the next rhythm marker — this is where AFIB/AFL/VT/Bigeminy/Trigeminy actually come
   from; they are rhythm states, not single-beat symbols.

Stage-1 (THECF/HGAN-SVM-DT) needs only **normal vs. abnormal** per window: any non-``N`` beat
in a window -> abnormal.

Stage-2 (CNN) needs the **7-class** rhythm label: the active rhythm annotation for a window
wins, except ``APB`` (atrial premature beat), which is a beat-level label reported when the
window contains one or more ``A`` beats and no more specific active rhythm annotation.
Windows whose rhythm doesn't map onto the 7 target classes are excluded from stage-2 training
(flagged, not silently mislabeled).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import wfdb

RHYTHM_TO_CLASS = {
    "(N": "NSR",
    "(AFIB": "AFIB",
    "(AFL": "AFL",
    "(VT": "VT",
    "(B": "Bigeminy",
    "(T": "Trigeminy",
}
ABNORMAL_BEAT_SYMBOLS = set("AaJSVFejnE/fQ?")  # anything that isn't 'N' or non-beat markers


@dataclass
class RecordLabels:
    beat_samples: np.ndarray
    beat_symbols: list[str]
    rhythm_boundaries: list[tuple[int, str]]  # (start_sample, class_name) sorted ascending


def build_record_labels(ann: wfdb.Annotation) -> RecordLabels:
    beat_samples, beat_symbols = [], []
    rhythm_boundaries: list[tuple[int, str]] = []

    for sample, symbol, aux in zip(ann.sample, ann.symbol, ann.aux_note):
        if symbol == "+":
            tag = aux.strip("\x00").strip()
            if tag in RHYTHM_TO_CLASS:
                rhythm_boundaries.append((int(sample), RHYTHM_TO_CLASS[tag]))
        else:
            beat_samples.append(int(sample))
            beat_symbols.append(symbol)

    rhythm_boundaries.sort(key=lambda t: t[0])
    return RecordLabels(np.array(beat_samples), beat_symbols, rhythm_boundaries)


def _active_rhythm(labels: RecordLabels, start: int) -> str | None:
    active = None
    for boundary_sample, class_name in labels.rhythm_boundaries:
        if boundary_sample <= start:
            active = class_name
        else:
            break
    return active


def detection_label(labels: RecordLabels, start: int, end: int) -> int:
    """0 = normal, 1 = abnormal, for the THECF/HGAN-SVM-DT binary stage."""
    in_window = (labels.beat_samples >= start) & (labels.beat_samples < end)
    symbols_in_window = [s for s, keep in zip(labels.beat_symbols, in_window) if keep]
    return int(any(s in ABNORMAL_BEAT_SYMBOLS for s in symbols_in_window))


def classification_label(labels: RecordLabels, start: int, end: int) -> str | None:
    """One of the 7 CNN classes, or None if this window doesn't map onto any of them."""
    rhythm = _active_rhythm(labels, start)
    if rhythm and rhythm != "NSR":
        return rhythm

    in_window = (labels.beat_samples >= start) & (labels.beat_samples < end)
    symbols_in_window = [s for s, keep in zip(labels.beat_symbols, in_window) if keep]
    if any(s == "A" for s in symbols_in_window):
        return "APB"
    if rhythm == "NSR" or (rhythm is None and all(s == "N" for s in symbols_in_window)):
        return "NSR"
    return None
