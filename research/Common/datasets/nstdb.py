"""MIT-BIH Noise Stress Test Database (NSTDB) loader.

Three pure noise records (``bw``, ``em``, ``ma`` — baseline wander, electrode motion, muscle
artefact) plus 12 noisy composite records (``118e_*``, ``119e_*``). Same
``wfdb.rdrecord(..., pn_dir=...)`` in-memory-cache pattern as ``mitdb.py``.
"""
from __future__ import annotations

import wfdb

_cache: dict[str, wfdb.Record] = {}

NOISE_RECORDS = ["bw", "em", "ma"]
NOISY_COMPOSITE_RECORDS = [
    "118e24", "118e18", "118e12", "118e06", "118e00", "118e_6",
    "119e24", "119e18", "119e12", "119e06", "119e00", "119e_6",
]


def get_record(record_name: str) -> wfdb.Record:
    if record_name not in _cache:
        _cache[record_name] = wfdb.rdrecord(record_name, pn_dir="nstdb")
    return _cache[record_name]


def noise_trace(noise_type: str):
    """Return a 1D noise trace (``bw``/``em``/``ma``) and its sampling rate."""
    if noise_type not in NOISE_RECORDS:
        raise ValueError(f"Unknown NSTDB noise type: {noise_type}")
    record = get_record(noise_type)
    return record.p_signal[:, 0], record.fs
