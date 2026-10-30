# 03 — Backend API (`apps/api`)

Express + Mongoose. System of record: auth, patients, alerts, and the ingest/decrypt path.
Knows about the Python detector service only as an HTTP client (`src/services/detectorClient.js`)
it calls to start/stop a stream or toggle an attack.

## Models

- `User` — clinician accounts (email, bcrypt password hash, name)
- `Patient` — name, cardiac history, assigned `mitbihRecordId`, owning clinician, and the
  persisted `baseline` profile (so a detector-service restart doesn't lose it — see below)
- `Segment` — one ingested window: waveform, features, secondary-vital HR, calibration
  state, attack state, and (once calibrated) the detection result
- `Alert` — created whenever an ingested segment's verdict isn't `genuine`

## Auth

JWT in an httpOnly cookie (`token`), 7-day expiry, `requireAuth` middleware reads/verifies
it. No refresh-token flow, no password reset — deliberately out of scope for a prototype.

## The ingest path (`POST /api/ingest`)

Receives `{ patient_id, blob }` from the detector's streamer, no auth (this endpoint *is* the
simulated secure device channel — see `01-architecture.md`). Decrypts `blob` with
`services/cryptoChannel.js` (must stay byte-compatible with the Python side's
`crypto_channel.py` — same SHA-256-derived key, same `base64(nonce).base64(ciphertext+tag)`
framing), stores a `Segment`, and creates an `Alert` if the verdict isn't `genuine`.

## Baseline persistence (`GET`/`POST /api/patients/:id/baseline`)

Also unauthenticated, also service-to-service only. The detector service owns the signal
math that *builds* a baseline, but Express persists the result so it survives a detector
restart: on `/stream/start`, the detector first asks Express for an existing baseline before
falling back to a fresh calibration run.

## Control passthrough (`src/routes/control.js`)

`POST /api/patients/:id/start|stop|attack` — all `requireAuth`, all just verify the patient
belongs to the calling clinician, then forward to `detectorClient`. The dashboard never
talks to the Python service directly.

## Running it standalone

```
cd apps/api
cp .env.example .env   # TRANSPORT_SECRET must match services/detector/.env
npm install
npm run seed   # creates demo@ecg-guard.local / demo1234 + one demo patient
npm run dev
```
