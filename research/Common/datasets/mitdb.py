"""MIT-BIH Arrhythmia Database loader.

Same pattern already proven in ``ecg-context-guard/services/detector/app/mitdb.py``:
``wfdb.rdrecord(..., pn_dir="mitdb")`` streams a record directly from PhysioNet (no local
download step), cached in memory per record name for the life of the process.
"""
from __future__ import annotations

import wfdb

_record_cache: dict[str, wfdb.Record] = {}
_ann_cache: dict[str, wfdb.Annotation] = {}

ALL_RECORDS = [
    "100", "101", "102", "103", "104", "105", "106", "107", "108", "109",
    "111", "112", "113", "114", "115", "116", "117", "118", "119", "121",
    "122", "123", "124", "200", "201", "202", "203", "205", "207", "208",
    "209", "210", "212", "213", "214", "215", "217", "219", "220", "221",
    "222", "223", "228", "230", "231", "232", "233", "234",
]


def get_record(record_name: str) -> wfdb.Record:
    if record_name not in _record_cache:
        _record_cache[record_name] = wfdb.rdrecord(record_name, pn_dir="mitdb")
    return _record_cache[record_name]


def get_annotation(record_name: str) -> wfdb.Annotation:
    if record_name not in _ann_cache:
        _ann_cache[record_name] = wfdb.rdann(record_name, "atr", pn_dir="mitdb")
    return _ann_cache[record_name]


def lead_signal(record_name: str):
    """First channel (MLII where present, matching the slides' pipeline)."""
    record = get_record(record_name)
    channel_names = [c.upper() for c in record.sig_name]
    idx = channel_names.index("MLII") if "MLII" in channel_names else 0
    return record.p_signal[:, idx], record.fs
