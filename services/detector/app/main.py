"""FastAPI app exposing control over per-patient ECG streams.

No auth, no database — this service only knows "patient id + record id + attack config" for
whatever streams are currently running in memory. Express is the only caller (forwarding
dashboard actions), and owns every concept of users/persistence. See
docs/building/01-architecture.md.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import streamer
from .config import DEFAULT_BIDMC_RECORDS, DEFAULT_RECORDS

app = FastAPI(title="ECG Context Guard — Detector Service")

_ALL_RECORD_IDS = set(DEFAULT_RECORDS) | set(DEFAULT_BIDMC_RECORDS)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/records")
def list_records() -> dict:
    """Which records are available to assign to a new demo patient — MIT-BIH (ECG only,
    cross-sensor check uses a disclosed synthetic stand-in) and BIDMC (real concurrent
    ECG+PPG, cross-sensor check uses the genuine PPG channel). See streamer.py."""
    records = [
        {"id": r, "label": f"MIT-BIH record {r}", "dataset": "mitdb", "cross_sensor": "synthetic"}
        for r in DEFAULT_RECORDS
    ] + [
        {
            "id": r,
            "label": f"BIDMC patient {r.split(':')[1]} (real ECG + PPG)",
            "dataset": "bidmc",
            "cross_sensor": "real",
        }
        for r in DEFAULT_BIDMC_RECORDS
    ]
    return {"records": records}


class StartRequest(BaseModel):
    patient_id: str
    record_id: str


@app.post("/stream/start")
async def stream_start(req: StartRequest) -> dict:
    # Must be `async def`: FastAPI runs plain `def` endpoints in a worker thread with no
    # running event loop, and starting a stream needs asyncio.create_task() on the loop
    # that will actually run it (see docs/mistakes-log.md).
    if req.record_id not in _ALL_RECORD_IDS:
        raise HTTPException(400, f"record_id must be one of {sorted(_ALL_RECORD_IDS)}")
    streamer.start_stream(req.patient_id, req.record_id)
    return {"started": True, "patient_id": req.patient_id}


class StopRequest(BaseModel):
    patient_id: str


@app.post("/stream/stop")
def stream_stop(req: StopRequest) -> dict:
    streamer.stop_stream(req.patient_id)
    return {"stopped": True, "patient_id": req.patient_id}


@app.get("/stream/{patient_id}/status")
def stream_status(patient_id: str) -> dict:
    status = streamer.get_status(patient_id)
    if status is None:
        return {"running": False}
    return status


class AttackRequest(BaseModel):
    patient_id: str
    enabled: bool
    attack_type: str = "none"
    intensity: float = 0.5


@app.post("/attack")
def set_attack(req: AttackRequest) -> dict:
    ok = streamer.set_attack(req.patient_id, req.enabled, req.attack_type, req.intensity)
    if not ok:
        raise HTTPException(404, "No active stream for this patient — start one first")
    return {"updated": True}
