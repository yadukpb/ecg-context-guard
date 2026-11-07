# ECG Context Guard

A working prototype for the dissertation project *"Context-Aware Detection of Semantic Data
Manipulation Attacks in Remote ECG-Based Cardiac Patient Monitoring Systems"* — plus,
alongside it, independent reproductions of two published papers from that same project's
literature review.

This README explains, from scratch, what this repo is, what problem it solves, what's
actually been built and measured, and how to run every part of it. If you're new here, read
this top to bottom before touching code.

---

## 1. The problem this project is about

Remote ECG monitoring (a patient wears a device at home, it streams readings to a clinician
dashboard) is vulnerable to more than just noise. A naive monitoring system flags *out-of-range*
values — but a more dangerous attack injects a reading that looks **clinically plausible**: a
heart rate that's wrong for *this specific patient right now*, but not so extreme that a
simple global threshold would ever catch it. For example, stretching the timing between
beats (`rr_stretch`) or nudging the signal amplitude (`amplitude_drift`) by an amount that
still looks like "a heart" to a naive check.

The dissertation's proposed answer: instead of one global threshold, compare every incoming
reading against **three kinds of context**, specific to that patient:

1. Their own historical baseline (calibrated from their own earlier, trusted readings).
2. Temporal plausibility (did this just change abruptly, with no real-world cause?).
3. Cross-sensor consistency (does a second, independent vital-sign reading agree?).

## 2. What's actually in this repo

Two genuinely separate pieces of work live here, on purpose kept apart (see
`docs/building/00-overview.md` and `research/README.md` for why they must not be conflated):

| | What it is | Status |
|---|---|---|
| **The app** (`apps/`, `services/`) | The dissertation's own proposed system, Semester 1 deliverable: a full working platform that replays real ECG data, simulates attacks, and runs the context-aware detector described above, on a live dashboard. | Built and runs locally end-to-end. Not yet deployed live (see §6). |
| **The research** (`research/`) | Independent reproductions of two *existing* published papers, done as literature-review grounding for the dissertation — not the dissertation's own contribution. | Both papers implemented and evaluated against real data; results are honestly compared to the papers' published numbers, gaps included. |

### 2a. The app, in one paragraph

Real MIT-BIH / BIDMC ECG recordings (from PhysioNet, a real public clinical database) are
replayed as if they were a live device stream. A Python service (`services/detector`)
preprocesses the signal, builds each patient's personal baseline during a calibration phase,
can inject one of several "plausible" attacks on demand, and scores every window as
`genuine` / `suspicious` / `manipulated` using the three-context scheme above — see
`docs/building/05-detection-algorithm.md` for the exact formula and its honestly-stated
limitations. An Express API (`apps/api`) sits in front of Mongo, handles auth and patient
records, and relays encrypted (AES-GCM) windows between the detector and a React dashboard
(`apps/web`) that shows live waveforms, verdicts, and alerts.

### 2b. The research, in one paragraph

Two papers were cited as related work in the dissertation's own literature review:

- **Paper 1** — *an attack-data-independent ResNet-18 "gatekeeper"* that learns to tell
  clean ECG from noisy/adversarially-perturbed ECG without ever training on adversarial
  examples itself, then gets attacked with FGSM/PGD/boundary-walk methods to see how well it
  holds up.
- **Paper 2** — *a layered MIoT (medical IoT) framework*: a cheap signal-processing
  pre-filter (THECF) screens out faulty/noisy sensor windows first, then a tuned
  SVM+DT ensemble (optimized by a metaheuristic called SFOA) flags anomalies, then a CNN run
  on an image-like transform of the signal classifies the specific arrhythmia type.

Both were re-implemented from their published methodology (architecture, thresholds,
attacks, optimizer) against the **same real PhysioNet datasets** the papers themselves used,
then evaluated with the same metrics the papers report, so the numbers can be compared
side by side, honestly — not adjusted to make them match. This exists to let the
dissertation make an *evidence-backed* novelty claim ("we reproduced X and Y; here's
concretely what they still miss") instead of an asserted one. See §5 for the actual
numbers.

## 3. How this fits together — the full picture

```
                              ┌─────────────────────────────┐
                              │   research/  (separate work) │
                              │   Paper 1 + Paper 2           │
                              │   reproductions, Python-only, │
                              │   own venv, no shared code     │
                              │   with the app below           │
                              └─────────────┬────────────────┘
                                            │ findings feed into
                                            ▼
┌──────────────┐  encrypted   ┌─────────────────────┐   HTTP   ┌──────────────┐
│ services/     │  windows     │  apps/api            │  JSON    │  apps/web     │
│ detector      │ ───────────▶│  (Express + Mongo)    │─────────▶│  (React/Vite) │
│ (FastAPI,     │              │  auth, patients,      │          │  dashboard,   │
│ Python)       │◀──control────│  ingest, alerts        │◀──data──│  "Research    │
│               │              │                       │          │  Findings"    │
│ real ECG data │              └──────────────────────┘          │  page shows   │
│ from PhysioNet│                                                 │  §5 below      │
└───────────────┘                                                └──────────────┘
```

The web app actually has a **"Research findings" page** (`/research` in the sidebar,
`apps/web/src/pages/ResearchFindings.jsx`) that renders the Paper 1/Paper 2 comparison data
(`apps/web/src/data/researchFindings.js`) as charts and tables, so the research results are
browsable from the same dashboard as the live detector demo — not just buried in markdown
reports.

## 4. Goals and scope

The instruction behind the `research/` work was explicit, and is worth repeating here so
nobody mistakes this for a sales pitch: **reproduce both papers' methodology faithfully
against real data, report whatever accuracy that actually produces, and explain — don't
hide — any gap versus the papers' published numbers.** Nothing in `research/` was tuned,
cherry-picked, or re-labeled to chase the papers' headline accuracy. Where a number looks
bad below, that's what the run produced.

Two feasibility findings shaped scope before any training code was written (full detail in
`research/FEASIBILITY_REPORT.md`):

- Neither paper publishes its exact processed dataset or label file. Paper 1's "noisy vs.
  clean" ground truth was hand-annotated by its own authors and never released; Paper 2
  cites a "32-feature MB Assiouni method" that isn't identifiable from any public source.
  Both gaps are flagged, not silently worked around.
- This machine is CPU-only. Paper 2's original authors trained on a weaker machine than
  this one (an Intel i5 laptop, 3.86GB RAM) so that reproduction was fully in budget; Paper
  1's authors used a Tesla V100, so that reproduction was deliberately scoped down (fewer
  datasets, smaller epsilon sweep, a simplified black-box attack stand-in) rather than left
  to run for an unrealistic number of hours.

## 5. Results — what actually happened

Full detail, every number sourced directly from `research/Paper_*/evaluation/results.json`,
lives in `research/COMPARISON_REPORT.md`. Headlines:

### Paper 1 — attack-data-independent defence (ResNet-18 gatekeeper)

| Metric | Paper (published) | This reproduction |
|---|---|---|
| Clean/noisy accuracy | 99.20% | **95.24%** |
| Clean/noisy F1 | 95.42% | **97.25%** |
| FGSM ε=0.001 accuracy | 80–99% | 93.3% |
| FGSM ε=0.1 accuracy | ~100% | **23.3%** (collapses, doesn't rise) |

**Why the gap:** the paper trained on ~15,000 segments across 4 datasets; this run used 210
samples from 2 datasets. At large attack strength the model's decision boundary collapses
rather than holding — a real, measured effect of dataset scale, confirmed by direct
inspection, not a methodology error.

### Paper 2 — THECF + HGAN-SVM-DT + SFOA-CNN (layered MIoT framework)

| Stage | Metric | Paper | This reproduction |
|---|---|---|---|
| THECF (fault screening) | Clean-window pass rate | 99.9% | **0.0%** |
| HGAN-SVM-DT (SFOA-tuned, full) | Accuracy | 99.80% | **67.0%** |
| SFOA-CNN (7-class arrhythmia) | Accuracy | 99.56% | **27.0%** |

**Why the gaps:** THECF's 0% is a genuine, two-ways-cross-checked discrepancy — direct FFT
analysis of real MIT-BIH signal shows far less energy in the paper's stated frequency band
than the paper's own claimed population statistic, which is flagged as the single most
valuable open question if this work continues (see report for the two possible
explanations). The HGAN-SVM-DT gap traces mainly to a necessarily-substituted feature set
(the paper's own feature method isn't identifiable, see §4). The CNN's gap is partly a
too-small, class-imbalanced record subset (12 of 48 records; some arrhythmia classes had as
few as 14 training windows) — named explicitly as "not yet run at full scale," not hidden.

**What *did* reproduce correctly in both papers:** the *shape* of the result. Paper 2's
ablation ordering (SFOA-tuned beats every simpler variant) matches the paper's own Table 4
pattern. Paper 1's qualitative attack-sensitivity trend is right even where the absolute
numbers aren't. The methodology itself — THECF's exact thresholds, a real SFOA
metaheuristic, a real adversarial-style SVM+DT ensemble, a real differential-image CNN, a
real 1D ResNet-18, real FGSM/PGD gradient attacks — was faithfully implemented and run
against real PhysioNet data; nothing above is a stub or a fabricated number.

## 6. The website

There is no live public URL yet. The app is fully built and documented for free-tier
deployment (Vercel for the frontend, Render for both backend services, MongoDB Atlas for the
database — see `docs/building/07-deployment.md` and `render.yaml`), but that deploy hasn't
been completed and pushed live. Right now, "the site" means **running it locally** (§7) —
anyone who wants a public link should finish the Vercel/Render/Atlas steps in that doc first.

## 7. How to run it

This section assumes nothing is installed yet — if you already have Git, Node.js, Python,
and Docker set up, skip straight to §7c.

### 7a. Get the code

- **With Git installed:** open a terminal in the folder where you want the project, then
  run `git clone <this repository's URL>` followed by `cd ecg-context-guard`. You'll find
  the exact clone URL on this repository's own page — look for the green **"Code"** button
  and copy the HTTPS link it shows.
- **Without Git:** on the repository's page, click the green **"Code"** button → **"Download
  ZIP"**, then extract the ZIP file anywhere on your computer and open a terminal inside the
  extracted folder.

### 7b. Install the prerequisites (first time only)

If this is a fresh **Windows** laptop with none of these tools installed, follow all four
steps below in order, restarting PowerShell after each install so it picks up the new PATH.
(On macOS/Linux, the same four tools are needed — Git, Node.js, Python 3.10+, and Docker —
installed via your usual method, e.g. Homebrew on macOS or your distro's package manager on
Linux; the verification commands at the end of each step are identical.)

1. **Git** (to download/update the code)
   - Go to **git-scm.com**, download "Git for Windows", and run the installer — the default
     options are fine everywhere, just click "Next" through the whole wizard.
   - Open **PowerShell** (press the Windows key, type `PowerShell`, press Enter) and check:
     ```
     git --version
     ```

2. **Node.js** (runs the API and the web dashboard)
   - Go to **nodejs.org** and download the version labeled **"LTS"** / "Recommended for most
     users".
   - Run the installer with default options. On the "Tools for Native Modules" step, you can
     leave that checkbox unchecked.
   - Open a **new** PowerShell window and check:
     ```
     node --version
     npm --version
     ```

3. **Python** (runs the signal-processing service and the research reproduction)
   - Go to **python.org/downloads** and download Python 3.10 or newer.
   - **Important:** on the installer's first screen, tick **"Add python.exe to PATH"** before
     clicking "Install Now" — this is the single most common thing people forget, and
     without it none of the `python` commands below will work.
   - Open a new PowerShell window and check:
     ```
     python --version
     pip --version
     ```
     (If Windows says it doesn't recognize `python`, try `py --version` instead — some
     Windows installs only register the `py` launcher. If that's the case for you,
     substitute `py` for `python` in every command in this README.)

4. **Docker Desktop** (runs the MongoDB database — only needed for §7c, not for the research
   reproduction in §7d)
   - Go to **docker.com**, find **Docker Desktop**, and download the Windows version.
   - The installer may ask to enable **WSL2** and restart your computer — accept both if
     prompted.
   - After installing, open Docker Desktop from the Start menu once and wait until it shows
     "Docker Desktop is running" (the whale icon in the system tray stops animating).
   - Check:
     ```
     docker --version
     docker compose version
     ```

Once all of the above commands print a version number instead of an error, you're ready.

### 7c. Run the app (dashboard + live ECG detection demo)

Needs internet access the first time each ECG record is used (it streams real data from
PhysioNet). Run this once, from inside the project folder:

**Windows (PowerShell):**

```powershell
cd ecg-context-guard

# 1. Start the database
docker compose up -d

# 2. Install Node dependencies, set up env files
npm install
Copy-Item apps\api\.env.example apps\api\.env
Copy-Item apps\web\.env.example apps\web\.env

# 3. Python detector service — its own virtual environment
cd services\detector
python -m venv venv
venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
cd ..\..

# 4. Seed one demo account + one demo patient
npm run seed --workspace apps/api
```

**macOS / Linux:**

```bash
cd ecg-context-guard

# 1. Start the database (mapped to host port 27018 instead of the default 27017, in case
#    another Mongo instance is already using 27017 on your machine)
docker compose up -d

# 2. Install Node dependencies, set up env files
npm install
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# 3. Python detector service — its own virtual environment
cd services/detector
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
cd ../..

# 4. Seed one demo account + one demo patient
npm run seed --workspace apps/api
```

Then, in three separate terminal windows (PowerShell commands shown; drop `venv\Scripts\`
in favor of `./venv/bin/` on macOS/Linux, as above):

```powershell
# Window 1 — detector service (Python/FastAPI)
cd services\detector
venv\Scripts\uvicorn app.main:app --port 8000

# Window 2 — API (Express)
npm run dev:api

# Window 3 — frontend (React/Vite)
npm run dev:web
```

Open **http://localhost:5173**, log in with `demo@ecg-guard.local` / `demo1234` (also shown
on the login page), open the demo patient, and click **Start stream**. The sidebar's
**"Research findings"** page shows the §5 results rendered as charts.

Run the Python test suite with `venv\Scripts\pytest -q` (Windows) or
`./venv/bin/python -m pytest -q` (macOS/Linux) from inside `services/detector`.

### 7d. Run the research (reproducing both papers yourself)

Separate virtual environment, separate dependencies, lives entirely under `research/` and
never touches the Node/React app.

**Windows (PowerShell):**

```powershell
cd research
python -m venv Common\venv
Common\venv\Scripts\pip install -r Common\requirements.txt

# Each one prints its metrics and writes them to <paper>/evaluation/results.json
Common\venv\Scripts\python -m Paper_1_Attack_Independent_Defence.main
Common\venv\Scripts\python -m Paper_2_Layered_MIOT_Framework.main

# Test suite for both papers' implementations
Common\venv\Scripts\pytest
```

**macOS / Linux:**

```bash
cd research
python3 -m venv Common/venv
Common/venv/bin/pip install -r Common/requirements.txt

Common/venv/bin/python -m Paper_1_Attack_Independent_Defence.main
Common/venv/bin/python -m Paper_2_Layered_MIOT_Framework.main

Common/venv/bin/pytest
```

Every number in `research/COMPARISON_REPORT.md` traces directly back to one of those two
`results.json` files — rerun the commands above and you'll regenerate (and can diff against)
the same report. Read `research/FEASIBILITY_REPORT.md` first for exactly what's scoped down
versus each paper's full-scale configuration, and why (dataset subsets, SFOA population
size, epoch counts, etc. — all named, none silent).

Note: the `Common/venv` folder is intentionally excluded from the repository (it's several
GB once PyTorch and the adversarial-attack libraries are installed) — the commands above
rebuild it locally in a few minutes.

## 8. Where to read more

- [`docs/building/00-overview.md`](docs/building/00-overview.md) — start here for the app;
  links to the rest of the `docs/building/` series (architecture, detector service, backend
  API, frontend, the detection algorithm in full detail, running the app, deployment).
- [`docs/building/05-detection-algorithm.md`](docs/building/05-detection-algorithm.md) — the
  exact genuine/suspicious/manipulated formula and its known limitations.
- [`research/README.md`](research/README.md) — how the two-paper reproduction is organized.
- [`research/FEASIBILITY_REPORT.md`](research/FEASIBILITY_REPORT.md) — full dataset
  investigation, feasibility call per paper, and the implementation roadmap that was
  followed.
- [`research/COMPARISON_REPORT.md`](research/COMPARISON_REPORT.md) — every reproduced number,
  side by side with the papers' published numbers, with gap explanations.
