# 02 — Detector service (`services/detector`)

Python/FastAPI service. Owns every bit of signal math; knows nothing about users or auth.

## Modules

- `app/mitdb.py` — fetches a MIT-BIH record from PhysioNet via `wfdb.rdrecord(name,
  pn_dir="mitdb")` and caches the parsed `Record` in memory (per detector-process lifetime).
  Originally tried a `wfdb.dl_record(...)`-based on-disk cache; that function doesn't exist
  in the installed wfdb version — see `docs/mistakes-log.md`.
- `app/signal_proc.py` — `preprocess()` (baseline-wander removal + bandpass filter),
  `detect_r_peaks()` (simplified Pan-Tompkins), `extract_features()` → `WindowFeatures`
  (heart rate, RR mean/std, QRS amplitude mean/std, beat count).
- `app/baseline.py` — `BaselineBuilder` accumulates calibration-window features;
  `.build()` freezes a `BaselineProfile` (per-patient mean/SD for HR, RR, amplitude), with a
  floor on each SD so a too-uniform calibration window can't make later z-scores explode.
- `app/cross_sensor.py` — synthetic secondary-vital generator standing in for a real second
  sensor (MIT-BIH has none). Produces an HR reading that tracks the *true, pre-attack*
  physiology plus its own independent slow drift + noise. See `05-detection-algorithm.md`
  for why this is a meaningful check despite being synthetic.
- `app/attack.py` — `apply_attack(window, attack_type, intensity)`: `amplitude_drift`,
  `rr_stretch`, `segment_replay`. Each is bounded so even at `intensity=1.0` the output stays
  inside a documented "clinically plausible" range.
- `app/detector.py` — `score_window()` combines baseline deviation, sudden within-session
  change, and cross-sensor mismatch into a `genuine`/`suspicious`/`manipulated` verdict.
- `app/crypto_channel.py` — AES-GCM encrypt/decrypt for the simulated secure channel; must
  stay byte-compatible with `apps/api/src/services/cryptoChannel.js` (same key derivation,
  same nonce+ciphertext+tag framing).
- `app/streamer.py` — one asyncio task per active patient: pulls the next window, runs it
  through preprocessing → (optional) attack → feature extraction → detection, and pushes the
  encrypted result to Express.
- `app/main.py` — FastAPI control surface: `/health`, `/records`, `/stream/start`,
  `/stream/stop`, `/stream/{id}/status`, `/attack`.

## Running it standalone

```
cd services/detector
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
./venv/bin/uvicorn app.main:app --port 8000
```

First call that touches a given MIT-BIH record fetches it from PhysioNet (needs internet
once per record per process). `pytest` exercises the same fetch against record "100".

## A subtlety worth calling out: `async def` matters here

`/stream/start` must be declared `async def`, not plain `def`. FastAPI runs plain `def`
endpoints in a worker thread with no running event loop; `streamer.start_stream()` calls
`asyncio.create_task(...)`, which needs one. Got bitten by this once — see
`docs/mistakes-log.md`.
