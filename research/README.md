# ECG research reproductions (Paper 1 & Paper 2)

Independent reproductions of two published ECG-security papers, done as literature-review
grounding for the dissertation project this repo also builds (the live detector app under
`apps/` and `services/`) — **not** that dissertation's own contribution. Kept separate on
purpose: own Python virtual environment, own `requirements.txt`, no shared code with the
Node/React app, same isolation convention as `services/detector`.

## What each paper does, and what was reproduced

- **Paper 1** (`Paper_1_Attack_Independent_Defence/`) — an attack-data-independent ResNet-18
  "gatekeeper": a model trained to tell clean ECG from noisy/adversarially-perturbed ECG
  *without ever training on adversarial examples itself*, then evaluated against FGSM, PGD,
  and real IBM ART HopSkipJump/Boundary black-box attacks across a 7-value epsilon sweep, and
  against a leave-one-dataset-out protocol across all 4 datasets the paper names.
- **Paper 2** (`Paper_2_Layered_MIOT_Framework/`) — a layered medical-IoT pipeline: THECF
  (a cheap signal-processing pre-filter) screens out faulty/noisy sensor windows first, then
  an SFOA-tuned SVM+DT ensemble ("HGAN-SVM-DT" in the paper's own terminology) flags
  anomalies, then a CNN run on an image-like transform of the signal classifies the specific
  arrhythmia type.
- **`Common/`** — the shared venv, the dataset loaders described below, and the SFOA
  metaheuristic optimizer both papers' pipelines use.

## Status, as of the last run (read this before trusting any report's numbers)

| | Status |
|---|---|
| **Paper 1** | Complete at full scale: all 4 datasets, the full 7-value epsilon sweep, real ART attacks, full leave-one-dataset-out. Current numbers are in `Paper_1_Attack_Independent_Defence/evaluation/results.json`. |
| **Paper 2** | Only the small-scale pass is complete (12 of 48 MIT-BIH records, 3-fold CV). A full-scale run (all 48 records, 5-fold CV, SFOA population 30/iterations 50 — the paper's actual config) was started once and never finished; nothing from that run was captured. |
| **`COMPARISON_REPORT.md`** | **Stale for Paper 1** — it still describes an earlier, smaller Paper 1 run (210 samples, 2 datasets, a 4-value epsilon sweep), not the full run above. Accurate for Paper 2, since the full-scale run above never landed. |

If you're picking this up: finish Paper 2's full-scale run, then rewrite
`COMPARISON_REPORT.md` from both papers' current `results.json` files — that closes out
everything named below as "not yet run."

## The datasets — what they are, where they're from, who uses which

Every dataset is fetched live over the network (via `wfdb.rdrecord(..., pn_dir=...)` for the
WFDB-format ones, or a direct HTTP call for teleECG), cached in memory per record for the
life of the process, and never committed to this repo. First use of any record needs
internet access; after that it's cached until the process restarts.

| Dataset | Loader | Source | What it actually is | License | Used by |
|---|---|---|---|---|---|
| **MIT-BIH Arrhythmia DB** | `Common/datasets/mitdb.py` | PhysioNet (`pn_dir="mitdb"`) | 48 half-hour, 2-channel ECG recordings from 47 subjects, 360 Hz, full beat + rhythm annotations by ≥2 cardiologists | ODC-BY, fully open | Paper 2 (THECF, HGAN-SVM-DT, CNN classification) |
| **MIT-BIH Noise Stress Test DB (NSTDB)** | `Common/datasets/nstdb.py` | PhysioNet | 3 pure noise traces (`bw`/`em`/`ma` — baseline wander, electrode motion, muscle artifact) + 12 noisy composite records | ODC-BY, open | Paper 1 (synthetic clean/noisy labels) and Paper 2 (THECF noise-robustness check) |
| **ECG-ID Database** | `Common/datasets/ecgiddb.py` | PhysioNet | 310 short (~20s) single-lead recordings from 90 people, 500 Hz | ODC Attribution v1.0, open | Paper 1 |
| **CinC Challenge 2011** | `Common/datasets/cinc2011.py` | PhysioNet (`challenge-2011/1.0.0/set-a`) | 1000 twelve-lead, 10-second, 500 Hz recordings, originally a signal-quality (acceptable/unacceptable) classification task | Open, PhysioNet terms | Paper 1 |
| **CinC Challenge 2014** | `Common/datasets/cinc2014.py` | PhysioNet (`challenge-2014/1.0.0/set-p`) | 100 long (~10 min), multi-signal, 250 Hz recordings; the first signal is always ECG | Open, PhysioNet terms | Paper 1 |
| **TELE ECG Database** | `Common/datasets/teleecg.py` | **Harvard Dataverse** (DOI `10.7910/DVN/QTG0EP`) — *not PhysioNet, unlike the other four* | 250 single-lead, ~30-40s, 500 Hz home-telehealth recordings with human-annotated QRS locations and two independent artifact masks | CC0 1.0 (confirmed directly against Dataverse's own dataset API — no account or data-use agreement needed) | Paper 1 |

Two things worth knowing before working with this data:

- **Neither paper's "noisy vs. clean" or feature-set ground truth is public.** Paper 1's
  clean/noisy label rule was hand-annotated by its own authors and never released — this
  repo re-derives an equivalent rule (a high-frequency-energy-ratio cutoff) rather than
  recovering the original. Paper 2's "32-feature MB Assiouni method" couldn't be identified
  from any public source, so a documented, equivalent DWT+morphology feature set stands in
  for it. Both are flagged, not silently worked around — see `FEASIBILITY_REPORT.md` §2 for
  the full reasoning.
- **teleECG needed its own access check** because the paper cites it as if it were
  PhysioNet-hosted, and it isn't. That check (live, against Dataverse's own API, not assumed
  from the paper) is recorded in `Common/datasets/teleecg.py`'s own docstring.

## Run it

**Windows (PowerShell):**

```powershell
cd research
python -m venv Common\venv
Common\venv\Scripts\pip install -r Common\requirements.txt

# Each one prints its metrics and writes them to <paper>/evaluation/results.json
Common\venv\Scripts\python -m Paper_1_Attack_Independent_Defence.main
Common\venv\Scripts\python -m Paper_2_Layered_MIOT_Framework.main

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

Every number in `COMPARISON_REPORT.md` traces back to one of the two `results.json` files
above — see `FEASIBILITY_REPORT.md` for exactly what's scoped down versus each paper's
full-scale configuration, and why (dataset subsets, SFOA population size, epoch counts, all
named, none silent).
