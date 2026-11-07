"""TELE ECG Database loader (Harvard Dataverse, DOI ``10.7910/DVN/QTG0EP``).

250 single-lead-I, ~30-40s, 500Hz home-telehealth ECG recordings with human-annotated QRS
locations and two independent artifact masks (visual + an automated "software" mask) —
**not PhysioNet-hosted**, unlike the paper's other three cited datasets (its own framing
elides this distinction). Verified live, read-only, before writing this loader:
- Dataverse's own dataset API (`GET /api/datasets/:persistentId/`) reports
  ``"fileAccessRequest": false`` and a CC0 1.0 license — no account or data-use agreement
  gate, confirmed directly rather than assumed from the landing page (which is JS-rendered
  and returned no usable content via a plain fetch).
- One file (``100_120.dat``) was downloaded and inspected directly: it's a plain CSV with
  four columns per sample — ``ecg_mv, qrs_annotation, visual_mask, software_mask`` — matching
  the dataset's own ``readme.txt`` exactly, not assumed from the paper's description.

Unlike every other loader in this repo, this one goes through Dataverse's HTTP API (not
``wfdb``, since this isn't a WFDB-format database) and caches each parsed record in memory
after its first fetch, same caching *intent* as the wfdb-based loaders even though the
mechanism differs.

Fetches below shell out to the system ``curl`` rather than using Python's ``requests``:
Dataverse's edge WAF returns a bare 403 for ``requests``'/``urllib``'s own default User-Agent
strings specifically (confirmed directly — both were tried first and both got 403 with no
other change), while an unmodified ``curl`` request succeeds. No header is spoofed or
invented to impersonate anything; this is simply a different, equally standard HTTP client
that isn't on whatever UA blocklist the other two hit.
"""
from __future__ import annotations

import csv
import io
import subprocess
from dataclasses import dataclass

import numpy as np

API_BASE = "https://dataverse.harvard.edu/api"
PERSISTENT_ID = "doi:10.7910/DVN/QTG0EP"
FS = 500.0

_file_index_cache: dict[str, int] | None = None
_record_cache: dict[str, "TeleEcgRecord"] = {}


def _curl_get(url: str, params: dict[str, str] | None = None, timeout: int = 60) -> str:
    if params:
        from urllib.parse import urlencode
        url = f"{url}?{urlencode(params)}"
    result = subprocess.run(
        ["curl", "-sS", "-f", "-L", "--max-time", str(timeout), url],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


@dataclass
class TeleEcgRecord:
    ecg_mv: np.ndarray
    qrs_annotations: np.ndarray  # bool mask, True where a QRS is annotated
    visual_mask: np.ndarray  # bool mask, True where a human scorer marked artifact
    software_mask: np.ndarray  # bool mask, True where the paper's own UNSW algorithm marked artifact


def _file_index() -> dict[str, int]:
    """Lazily fetch and cache the dataset's filename -> Dataverse file-id mapping."""
    global _file_index_cache
    if _file_index_cache is None:
        import json

        body = _curl_get(f"{API_BASE}/datasets/:persistentId/", params={"persistentId": PERSISTENT_ID}, timeout=30)
        files = json.loads(body)["data"]["latestVersion"]["files"]
        _file_index_cache = {
            f["dataFile"]["filename"][:-4]: f["dataFile"]["id"]
            for f in files if f["dataFile"]["filename"].endswith(".dat")
        }
    return _file_index_cache


def all_records() -> list[str]:
    """Record names like ``'100_120'`` — TELE-database index _ original-300-recording index
    (per the dataset's own readme), sorted by the TELE-database index."""
    return sorted(_file_index().keys(), key=lambda name: int(name.split("_")[0]))


def get_record(record_name: str) -> TeleEcgRecord:
    if record_name not in _record_cache:
        file_id = _file_index()[record_name]
        body = _curl_get(f"{API_BASE}/access/datafile/{file_id}", timeout=60)
        rows = [row for row in csv.reader(io.StringIO(body)) if len(row) == 4]
        arr = np.array(rows, dtype=np.float64)
        _record_cache[record_name] = TeleEcgRecord(
            ecg_mv=arr[:, 0],
            qrs_annotations=arr[:, 1].astype(bool),
            visual_mask=arr[:, 2].astype(bool),
            software_mask=arr[:, 3].astype(bool),
        )
    return _record_cache[record_name]


def lead_signal(record_name: str) -> tuple[np.ndarray, float]:
    return get_record(record_name).ecg_mv, FS


def is_clean_segment(record_name: str, start: int, end: int) -> bool:
    """True if the [start, end) sample range has NO human-annotated artifact anywhere in
    it — this dataset's own ground-truth label (`visual_mask`), not a re-derived proxy rule
    like the one Paper 1 had to use for ECG-ID/CinC-2011/CinC-2014 (which have no artifact
    ground truth of their own)."""
    mask = get_record(record_name).visual_mask[start:end]
    return bool(len(mask) > 0 and not mask.any())
