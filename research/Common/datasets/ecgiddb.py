"""ECG-ID Database loader (PhysioNet ``ecgiddb``).

310 short (~20s) single-lead-I recordings from 90 people, 500 Hz, raw + filtered signal per
record. Confirmed live on PhysioNet during the feasibility pass (not a dataset that needs a
Dataverse-style access check, unlike teleECG — see research/FEASIBILITY_REPORT.md section 3).
"""
from __future__ import annotations

import wfdb

_cache: dict[str, wfdb.Record] = {}

NUM_PERSONS = 90


def _record_path(person: int, recording: int) -> str:
    return f"Person_{person:02d}/rec_{recording}"


def get_record(person: int, recording: int) -> wfdb.Record:
    """``wfdb.rdrecord`` builds its PhysioNet URL from ``pn_dir`` alone and the bare record
    name — a subdirectory given as part of ``record_name`` (e.g. ``"Person_01/rec_1"``) is
    silently dropped, producing a 404 for ``.../rec_1.hea`` instead of
    ``.../Person_01/rec_1.hea`` (confirmed by inspecting the actual request URL in the
    resulting traceback). The subdirectory has to be folded into ``pn_dir`` instead:
    ``pn_dir="ecgiddb/1.0.0/Person_01"``, ``record_name="rec_1"``.
    """
    key = _record_path(person, recording)
    if key not in _cache:
        pn_dir = f"ecgiddb/1.0.0/Person_{person:02d}"
        _cache[key] = wfdb.rdrecord(f"rec_{recording}", pn_dir=pn_dir)
    return _cache[key]


def filtered_signal(person: int, recording: int = 1):
    """Return the filtered ECG channel (index 1 — raw is index 0) and sampling rate."""
    record = get_record(person, recording)
    return record.p_signal[:, 1], record.fs
