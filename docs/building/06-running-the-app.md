# 06 — Running the app

## One-time setup

```bash
cd ecg-context-guard

# Mongo (mapped to host port 27018, not the default 27017 — see "Port collision" below)
docker compose up -d

# Node workspaces (apps/api + apps/web)
npm install
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# Python detector service
cd services/detector
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
cd ../..

# Seed one demo clinician + one demo patient (record 100)
npm run seed --workspace apps/api
```

## Every time you run it (3 terminals)

```bash
# Terminal 1
cd services/detector && ./venv/bin/uvicorn app.main:app --port 8000

# Terminal 2
npm run dev:api

# Terminal 3
npm run dev:web
```

Open http://localhost:5173, log in with `demo@ecg-guard.local` / `demo1234` (shown on the
login page itself too), open the demo patient, click **Start stream**.

First time you stream a given MIT-BIH record, the detector fetches it from PhysioNet — needs
internet, takes a few seconds. Calibration (15 windows × 2s ≈ 30s) runs before the first
verdict appears; a detector restart skips recalibration since Express persisted the baseline.

## Driving a live demo

1. Start the stream, wait for the verdict badge to stop saying "Calibrating…" and show
   `GENUINE`.
2. Pick an attack type (RR-interval stretch or Segment replay flip verdicts fastest/most
   reliably in testing; Amplitude drift is subtler — see `05-detection-algorithm.md`), set
   intensity, click **Simulate attack**.
3. Watch the verdict badge flip, the waveform color change, and a new row appear on the
   Alerts page within a couple of seconds.
4. To re-demo a different attack type while streaming, click **Stop attack simulation**,
   change the dropdown, then **Simulate attack** again — the dropdown alone doesn't push the
   change to the running stream.

## Static report figures (no servers needed)

```bash
cd services/detector
./venv/bin/python scripts/generate_report_figures.py
```

Writes `docs/figures/waveform_comparison.png` and `docs/figures/detection_timeline.png`.

## Running the detector's test suite

```bash
cd services/detector && ./venv/bin/python -m pytest -q
```

## Known environment quirks

- **Mongo port collision**: `docker-compose.yml` maps Mongo to host port **27018** instead
  of the default 27017, in case another Mongo instance is already using 27017 on your
  machine. If you know 27017 is free, you can change it back to `27017:27017` and update
  `MONGO_URI` in both `.env` files and `apps/api/src/config/env.js`'s default.
- If `pip install` fails partway through downloading a large package, just re-run the same
  command — pip resumes partial downloads rather than starting over, so this usually fixes a
  transient network interruption.
