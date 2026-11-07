"""PhysioNet/CinC Challenge 2011 loader ("Improving the Quality of ECGs...").

1000 twelve-lead, 10-second, 500Hz ECG recordings in ``set-a`` (plus a disjoint ``set-b``,
not used here — one set is enough to extend Paper 1's dataset mix). Confirmed live:
``pn_dir="challenge-2011/1.0.0/set-a"``, record names are 7-digit numeric IDs (e.g.
``"1002603"``), listed via ``wfdb.get_record_list("challenge-2011/1.0.0/set-a")``. Same
in-memory-cache pattern as every other loader in this repo.
"""
from __future__ import annotations

import wfdb

_cache: dict[str, wfdb.Record] = {}
_records_cache: list[str] | None = None

PN_DIR = "challenge-2011/1.0.0/set-a"


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
    """Lead II where present (matches the MIT-BIH/MLII convention used elsewhere in this
    repo), else the first available channel — this dataset's own quality-grading task
    doesn't name a canonical lead for classifiers, so the choice is ours."""
    record = get_record(record_name)
    channel_names = [c.upper() for c in record.sig_name]
    idx = channel_names.index("II") if "II" in channel_names else 0
    return record.p_signal[:, idx], record.fs
