"""Loading MIT-BIH Arrhythmia Database records, with an in-memory cache.

``wfdb.rdrecord(..., pn_dir="mitdb")`` streams a record directly from PhysioNet (no
``dl_record`` exists in this wfdb version — confirmed by inspecting the installed package,
see docs/mistakes-log.md). We cache the parsed ``Record`` in memory per record name so each
one is only fetched over the network once per detector-service process lifetime, which is
enough for a demo (a handful of records, read once each into memory, then replayed locally).
"""
from __future__ import annotations

import wfdb

_cache: dict[str, wfdb.Record] = {}


def get_record(record_name: str) -> wfdb.Record:
    """Return the full MIT-BIH record (signal + metadata), fetching it from PhysioNet if
    this process hasn't already."""
    if record_name in _cache:
        return _cache[record_name]

    record = wfdb.rdrecord(record_name, pn_dir="mitdb")
    _cache[record_name] = record
    return record


def lead_ii_signal(record_name: str):
    """Return the MLII (lead II analogue) channel as a 1D float array, the lead the
    slides' preprocessing/feature-extraction pipeline is built around.
    """
    record = get_record(record_name)
    channel_names = [c.upper() for c in record.sig_name]
    if "MLII" in channel_names:
        idx = channel_names.index("MLII")
    else:
        idx = 0  # fall back to the first channel for records without MLII
    return record.p_signal[:, idx]
