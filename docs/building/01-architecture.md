# 01 — Architecture & data flow

## Services and ports

| Service              | Tech                        | Port  | Role |
|-----------------------|------------------------------|-------|------|
| `services/detector`   | Python, FastAPI              | 8000  | device simulation + signal math |
| `apps/api`            | Node, Express + Mongoose     | 4000  | system of record: auth, patients, alerts |
| `apps/web`            | React + Vite                 | 5173  | dashboard |
| Mongo (docker-compose)| MongoDB 7                    | 27017 | storage |

The detector service does **not** talk to Mongo directly and has no concept of users/auth —
it only knows "patient id + MIT-BIH record id + attack config". Express owns persistence and
auth; the detector is a disposable signal-processing worker Express drives over HTTP.

## Why Python pushes to Express, not Express pulling from Python

The detector runs a background replay loop per active patient (one window every N seconds,
simulating a live device). Rather than Express polling Python for "is there a new window yet",
Python **pushes** each encrypted window to Express's `POST /api/ingest` as soon as it's ready.
This also lets the "Secure Data Transmission" step be literal: the push is the simulated wire
transfer, and encryption happens right before the push, decryption right after receipt —
matching the slides' workflow step order (collect → preprocess → **transmit securely** →
baseline/analyze → detect).

## End-to-end flow for one window

```
[services/detector] streamer.py, one tick for patient P:
  1. read next 2s window from P's assigned MIT-BIH record      (ECG Data Collection)
  2. bandpass filter + baseline-wander removal                 (Preprocessing & Noise Removal)
  3. if P.attack_enabled: attack.py mutates the window          (Attack Simulation)
  4. extract features (HR, RR intervals, QRS amplitude)         (feeds baseline + detection)
  5. generate the synthetic cross-sensor vital for this window  (feeds Cross-Sensor Analysis)
  6. compare features to P's stored baseline + recent history:
       -> temporal_score, cross_sensor_score, verdict           (Temporal + Cross-Sensor + Detection)
  7. AES-GCM encrypt {waveform, features, verdict, scores}      (Secure Data Transmission)
  8. POST encrypted blob to Express /api/ingest

[apps/api] POST /api/ingest:
  1. decrypt blob with shared secret
  2. if P still in calibration window: feed features into baseline builder, store baseline
  3. else: store Segment{features, verdict, scores, waveform}
  4. if verdict != genuine: create Alert, link to Segment
  5. respond 200

[apps/web] PatientDashboard, polling every ~2s:
  GET /api/patients/:id/latest  -> waveform + verdict + stat cards
  GET /api/patients/:id/alerts  -> alert feed
```

The baseline itself is built *inside* the detector service (it owns the signal math) but
Express persists the resulting baseline profile per patient so it survives detector restarts;
the detector asks Express for a patient's stored baseline when it starts that patient's stream
again (`GET /api/patients/:id/baseline`, called by Python, read-only, no auth required since
it's service-to-service on localhost — see `03-backend-api.md` for why that's an acceptable
simplification here and not in a real deployment).

## Control path (starting/stopping a stream, triggering an attack)

The dashboard doesn't talk to the Python service directly. It calls Express
(`POST /api/patients/:id/control/start|stop|attack`), and Express forwards that to the Python
service's own control endpoints. This keeps auth in one place (Express) and keeps the Python
service with no concept of logged-in users at all.

## Secure transmission detail

A single shared `TRANSPORT_SECRET` (env var, same value in both services' `.env`) is used to
derive an AES-GCM key. This is a **simulation** of a secure channel for the purposes of the
"Secure Data Transmission" module in the slides — not a production key-management design (no
rotation, no per-device keys). That tradeoff is intentional and stated here rather than left
implicit.
