# ECG Context Guard

Working prototype for *"Context-Aware Detection of Semantic Data Manipulation Attacks in
Remote ECG-Based Cardiac Patient Monitoring Systems."*

Real MIT-BIH / BIDMC ECG data → Python preprocessing, patient baselining, attack simulation,
and detection → AES-GCM encrypted transport → Express API → React dashboard.

## Run it locally

**Prerequisites:** Docker, Node.js 18+, Python 3.10+, internet access (streams real ECG data
from PhysioNet on first use).

```bash
git clone https://github.com/yadukpb/ecg-context-guard.git
cd ecg-context-guard

# 1. Mongo (mapped to host port 27018, not the default 27017 — see
#    docs/mistakes-log.md if you ever need to change it back)
docker compose up -d

# 2. Node workspaces (apps/api + apps/web)
npm install
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# 3. Python detector service
cd services/detector
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
cd ../..

# 4. Seed one demo clinician account + one demo patient
npm run seed --workspace apps/api
```

Then, in three separate terminals:

```bash
# Terminal 1 — detector service (Python/FastAPI)
cd services/detector && ./venv/bin/uvicorn app.main:app --port 8000

# Terminal 2 — API (Express)
npm run dev:api

# Terminal 3 — frontend (React/Vite)
npm run dev:web
```

Open **http://localhost:5173**, log in with `demo@ecg-guard.local` / `demo1234` (also shown
on the login page), open the demo patient, click **Start stream**.

Run the Python test suite with `cd services/detector && ./venv/bin/python -m pytest -q`.

## Deploying it (free)

See [`docs/building/07-deployment.md`](docs/building/07-deployment.md) — Vercel (frontend) +
Render (both backends) + MongoDB Atlas, all free tier, no credit card.

## More docs

Start at [`docs/building/00-overview.md`](docs/building/00-overview.md) — it links to
everything else, including a deeper run-it guide
([`06-running-the-app.md`](docs/building/06-running-the-app.md)) and the detection algorithm
in full ([`05-detection-algorithm.md`](docs/building/05-detection-algorithm.md)).

Things that broke while building this, and how they were fixed: [`docs/mistakes-log.md`](docs/mistakes-log.md).
