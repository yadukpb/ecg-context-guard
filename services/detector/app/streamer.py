"""Per-patient background replay loop — simulates one patient's live IoMT device.

One running asyncio task per active patient. Each tick: pull the next window off their
assigned record, preprocess, (optionally) attack, score, encrypt, push to Express. A
patient is backed by either a MIT-BIH record (ECG only — cross-sensor uses the synthetic
stand-in in cross_sensor.py) or a BIDMC record (real concurrent ECG+PPG — cross-sensor uses
the genuine PPG-derived pulse rate in signal_proc.extract_ppg_hr), distinguished by the
"bidmc:" prefix on record_id. See docs/building/01-architecture.md for the full per-window
sequence this implements.
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field

import httpx

from . import bidmc, mitdb
from .attack import AttackType, apply_attack
from .baseline import BaselineBuilder, BaselineProfile
from .config import BIDMC_FS_HZ, CALIBRATION_WINDOWS, EXPRESS_BASE_URL, FS_HZ, ROLLING_HISTORY_SIZE, WINDOW_SEC
from .crypto_channel import encrypt_json
from .cross_sensor import CrossSensorState, new_state, next_secondary_hr
from .detector import score_window
from .signal_proc import WindowFeatures, extract_ppg_hr, preprocess, extract_features

# A real PPG reading that jumps more than this many bpm from this same patient's last
# accepted reading, in a single 2s tick, is treated as a sensor artifact (e.g. a dicrotic
# notch double-counted as a beat) rather than real physiology — real heart rate cannot swing
# this fast. Confirmed empirically against real BIDMC recordings during development: without
# this check, rare peak-detection errors occasionally produced a spurious "manipulated"
# verdict on genuine, unattacked data (see docs/mistakes-log.md).
_MAX_PPG_JUMP_BPM = 20.0


def _is_bidmc_record(record_id: str) -> bool:
    return record_id.startswith("bidmc:")


def _bidmc_number(record_id: str) -> str:
    return record_id.split(":", 1)[1]


@dataclass
class PatientStream:
    patient_id: str
    record_id: str
    cursor: int = 0
    baseline_builder: BaselineBuilder = field(default_factory=BaselineBuilder)
    baseline: BaselineProfile | None = None
    history: deque = field(default_factory=lambda: deque(maxlen=ROLLING_HISTORY_SIZE))
    cross_state: CrossSensorState | None = None
    last_valid_ppg_hr: float | None = None  # continuity check for the real-sensor path only
    attack_type: AttackType = AttackType.NONE
    attack_intensity: float = 0.0
    attack_enabled: bool = False
    running: bool = False
    task: asyncio.Task | None = None


_streams: dict[str, PatientStream] = {}


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=EXPRESS_BASE_URL, timeout=5.0)


async def _fetch_existing_baseline(patient_id: str) -> BaselineProfile | None:
    try:
        async with _client() as client:
            resp = await client.get(f"/api/patients/{patient_id}/baseline")
        if resp.status_code == 200 and resp.json().get("baseline"):
            return BaselineProfile.from_dict(resp.json()["baseline"])
    except httpx.HTTPError:
        pass
    return None


async def _push_baseline(patient_id: str, baseline: BaselineProfile) -> None:
    try:
        async with _client() as client:
            await client.post(f"/api/patients/{patient_id}/baseline", json={"baseline": baseline.to_dict()})
    except httpx.HTTPError:
        pass


async def _push_ingest(patient_id: str, payload: dict) -> None:
    blob = encrypt_json(payload)
    try:
        async with _client() as client:
            await client.post("/api/ingest", json={"patient_id": patient_id, "blob": blob})
    except httpx.HTTPError:
        pass


def _window_slice(signal, cursor: int, window_samples: int):
    """Return the next window and the advanced cursor, wrapping around the record so a
    demo patient can stream indefinitely from a finite recording."""
    n = len(signal)
    if cursor + window_samples > n:
        cursor = 0
    window = signal[cursor : cursor + window_samples]
    return window, cursor + window_samples


def _real_secondary_hr(stream: PatientStream, ppg_window, fs: int) -> float:
    """Pulse rate from this tick's real PPG window, with a continuity check against this
    same patient's last accepted reading — rejects isolated sensor artifacts (e.g. a
    dicrotic notch double-counted as a beat) that the per-window plausibility check in
    extract_ppg_hr can't see, since it has no memory between windows."""
    raw = extract_ppg_hr(ppg_window, fs)
    if raw <= 0:
        return 0.0
    if stream.last_valid_ppg_hr is not None and abs(raw - stream.last_valid_ppg_hr) > _MAX_PPG_JUMP_BPM:
        return 0.0
    stream.last_valid_ppg_hr = raw
    return raw


async def _run(stream: PatientStream) -> None:
    is_bidmc = _is_bidmc_record(stream.record_id)

    if is_bidmc:
        number = _bidmc_number(stream.record_id)
        ecg_raw = bidmc.ecg_signal(number)
        ppg_raw = bidmc.ppg_signal(number)
        fs = BIDMC_FS_HZ
    else:
        ecg_raw = mitdb.lead_ii_signal(stream.record_id)
        ppg_raw = None
        fs = FS_HZ
        stream.cross_state = new_state(stream.patient_id)

    window_samples = WINDOW_SEC * fs

    while stream.running:
        tick_start = time.monotonic()
        tick_cursor = stream.cursor  # same starting sample for both channels this tick
        window, stream.cursor = _window_slice(ecg_raw, tick_cursor, window_samples)
        genuine = preprocess(window, fs)
        true_features = extract_features(genuine, fs)

        if is_bidmc:
            # ppg_raw and ecg_raw are the same patient's concurrent recordings on the same
            # timebase, so slicing at the same starting sample gives the simultaneous PPG
            # window for this tick's ECG window.
            ppg_window, _ = _window_slice(ppg_raw, tick_cursor, window_samples)
            secondary_hr = _real_secondary_hr(stream, ppg_window, fs)
            cross_sensor_source = "real_ppg"
        else:
            secondary_hr, stream.cross_state = next_secondary_hr(true_features.heart_rate_bpm, stream.cross_state)
            cross_sensor_source = "synthetic"

        transmitted = (
            apply_attack(genuine, stream.attack_type, stream.attack_intensity)
            if stream.attack_enabled
            else genuine
        )
        features: WindowFeatures = extract_features(transmitted, fs)

        base_payload = {
            "waveform": transmitted.tolist(),
            "features": features.to_dict(),
            "secondary_hr_bpm": secondary_hr,
            "cross_sensor_source": cross_sensor_source,
            "attack_enabled": stream.attack_enabled,
            "attack_type": stream.attack_type.value,
        }

        if stream.baseline is None:
            stream.baseline_builder.add(features)
            if stream.baseline_builder.n_windows >= CALIBRATION_WINDOWS:
                stream.baseline = stream.baseline_builder.build()
                await _push_baseline(stream.patient_id, stream.baseline)
            await _push_ingest(
                stream.patient_id,
                {
                    **base_payload,
                    "calibrating": True,
                    "calibration_progress": stream.baseline_builder.n_windows,
                    "calibration_total": CALIBRATION_WINDOWS,
                },
            )
        else:
            result = score_window(
                features, stream.baseline, list(stream.history), secondary_hr, cross_sensor_is_real=is_bidmc
            )
            stream.history.append(features)
            await _push_ingest(
                stream.patient_id,
                {**base_payload, "calibrating": False, "detection": result.to_dict()},
            )

        elapsed = time.monotonic() - tick_start
        await asyncio.sleep(max(0.0, WINDOW_SEC - elapsed))


def start_stream(patient_id: str, record_id: str) -> PatientStream:
    existing = _streams.get(patient_id)
    if existing and existing.running:
        return existing

    stream = PatientStream(patient_id=patient_id, record_id=record_id, running=True)
    _streams[patient_id] = stream
    stream.task = asyncio.create_task(_bootstrap_and_run(stream))
    return stream


async def _bootstrap_and_run(stream: PatientStream) -> None:
    existing_baseline = await _fetch_existing_baseline(stream.patient_id)
    if existing_baseline is not None:
        stream.baseline = existing_baseline
    await _run(stream)


def stop_stream(patient_id: str) -> None:
    stream = _streams.get(patient_id)
    if stream:
        stream.running = False
        if stream.task:
            stream.task.cancel()
        del _streams[patient_id]


def set_attack(patient_id: str, enabled: bool, attack_type: str, intensity: float) -> bool:
    stream = _streams.get(patient_id)
    if not stream:
        return False
    stream.attack_enabled = enabled
    stream.attack_type = AttackType(attack_type)
    stream.attack_intensity = intensity
    return True


def get_status(patient_id: str) -> dict | None:
    stream = _streams.get(patient_id)
    if not stream:
        return None
    return {
        "running": stream.running,
        "record_id": stream.record_id,
        "calibrating": stream.baseline is None,
        "attack_enabled": stream.attack_enabled,
        "attack_type": stream.attack_type.value,
        "attack_intensity": stream.attack_intensity,
    }
