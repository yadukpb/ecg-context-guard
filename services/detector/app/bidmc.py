"""Loading BIDMC PPG and Respiration Database records, with an in-memory cache.

Why this dataset exists alongside MIT-BIH: MIT-BIH only has ECG channels, so the detector's
"cross-sensor consistency" check had nothing real to compare the ECG-derived heart rate
against (see cross_sensor.py's synthetic stand-in, used for MIT-BIH-backed patients, and
disclosed as a limitation). BIDMC, also on PhysioNet, contains real simultaneous ECG (lead
II) *and* PPG (pulse oximeter waveform) recordings from the same patient on the same
timebase — a genuine second sensor. For patients backed by a BIDMC record, the streamer
computes the secondary heart rate by peak-detecting the actual PPG channel (see
signal_proc.extract_ppg_hr), not by simulating one.

``wfdb.rdrecord(f"bidmc{nn}", pn_dir="bidmc")`` streams the record directly from PhysioNet,
same pattern as mitdb.py. Each record is 8 minutes at 125Hz — small enough to fetch and hold
in memory per process, same tradeoff as the MIT-BIH loader.
"""
from __future__ import annotations

import wfdb

_cache: dict[str, wfdb.Record] = {}


def _wfdb_name(record_number: str) -> str:
    """Public record ids look like "bidmc:01"; PhysioNet's own record names are "bidmc01"."""
    return f"bidmc{record_number}"


def get_record(record_number: str) -> wfdb.Record:
    """Return the full BIDMC record (ECG + PPG + respiration + metadata), fetching it from
    PhysioNet if this process hasn't already."""
    name = _wfdb_name(record_number)
    if name in _cache:
        return _cache[name]

    record = wfdb.rdrecord(name, pn_dir="bidmc")
    _cache[name] = record
    return record


def _channel(record: wfdb.Record, name: str):
    # BIDMC's own channel labels carry a trailing comma (e.g. "II," not "II") — a quirk of
    # how the .hea files were authored, confirmed by inspecting record.sig_name directly.
    names = [c.strip().rstrip(",").upper() for c in record.sig_name]
    idx = names.index(name.upper())
    return record.p_signal[:, idx]


def ecg_signal(record_number: str):
    """The real ECG channel (lead II) for this BIDMC patient."""
    return _channel(get_record(record_number), "II")


def ppg_signal(record_number: str):
    """The real PPG (pulse-oximeter) channel for this same patient, same timebase as the
    ECG — the genuine second sensor the cross-sensor check compares against."""
    return _channel(get_record(record_number), "PLETH")
