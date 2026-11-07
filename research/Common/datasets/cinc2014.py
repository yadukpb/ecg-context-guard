"""PhysioNet/CinC Challenge 2014 loader ("Robust Detection of Heart Beats...").

100 long (~10 minute), multi-signal, 250Hz recordings in ``set-p`` (the training set; the
paper's Table 2 counts come from this set). Confirmed live:
``pn_dir="challenge-2014/1.0.0/set-p"``, numeric record names ``"100".."199"`` (overlapping
MIT-BIH's own numbering by coincidence — a different database, never conflated since the two
loaders are never called with each other's ``pn_dir``). The first signal is always an ECG
channel (named ``"ECG"``), per the dataset's own description — occasionally missing per-record,
checked explicitly below rather than assumed.
"""
from __future__ import annotations

import wfdb

_cache: dict[str, wfdb.Record] = {}
_records_cache: list[str] | None = None

PN_DIR = "challenge-2014/1.0.0/set-p"


def all_records() -> list[str]:
    global _records_cache
    if _records_cache is None:
        _records_cache = wfdb.get_record_list(PN_DIR)
    return _records_cache


def get_record(record_name: str) -> wfdb.Record:
    if record_name not in _cache:
        _cache[record_name] = wfdb.rdrecord(record_name, pn_dir=PN_DIR)
    return _cache[record_name]


def lead_signal(record_name: str):
    """The record's ECG channel (checked by name, not assumed to always be index 0 — the
    dataset's own documentation notes the ECG can occasionally be absent)."""
    record = get_record(record_name)
    channel_names = [c.upper() for c in record.sig_name]
    if "ECG" not in channel_names:
        raise ValueError(f"No ECG channel in CinC-2014 record {record_name}: {record.sig_name}")
    idx = channel_names.index("ECG")
    return record.p_signal[:, idx], record.fs
