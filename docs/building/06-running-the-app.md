# 06 — Running the app

## One-time setup

No Docker, no manually-installed database — `scripts/setup.js` handles Node dependencies,
the Python virtual environment, and `.env` files; the database is self-managed on first
start (see `apps/api/src/config/db.js`).

```bash
cd ecg-context-guard
npm run setup
```

## Every time you run it (one terminal)

```bash
npm start
```

Runs the detector (Python/FastAPI), the API (Express), and the web dashboard (Vite)
together via `concurrently`, each line prefixed `[detector]` / `[api]` / `[web]`. The API
starts a self-contained MongoDB instance automatically the first time (downloads a real
MongoDB binary once, caches it, stores data in `apps/api/.mongo-data`, gitignored) and
creates the demo account + demo patients if they don't already exist — both persist across
restarts. Ctrl+C once stops all three.

Equivalent manual version, in three separate terminals, if you want the services' output
separated instead:

```bash
# Terminal 1
cd services/detector && ./venv/bin/uvicorn app.main:app --port 8000   # Windows: venv\Scripts\uvicorn

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

- **Prefer a real/external MongoDB instead of the self-managed one?** Set `MONGO_URI` in
  `apps/api/.env` (commented out by default) to any MongoDB connection string — a local
  `docker compose up -d` (see `docker-compose.yml`), one already running on your machine, or
  a MongoDB Atlas cluster. If it's set, `config/db.js` connects to it directly instead of
  starting its own embedded instance.
- If `pip install` fails partway through downloading a large package, just re-run the same
  command — pip resumes partial downloads rather than starting over, so this usually fixes a
  transient network interruption.
