# Research Feasibility and Technical Implementation Report

**Dissertation:** *Context-Aware Detection of Semantic Data Manipulation Attacks in Remote
ECG-Based Cardiac Patient Monitoring Systems.*

**Status:** This is Stage 1 output only (document analysis + feasibility), produced per the
project requirements' own instruction: *"Start with document analysis and the feasibility
report only... wait until the research methodology and implementation plan are established
before generating code."* No training code has been written yet. This document is the gate
before Stage 2.

**Sources read in full:** both reference papers, cover-to-cover (11 and 24 pages
respectively), and the project's own review slide deck. Dataset claims below were
additionally checked against live PhysioNet / Harvard Dataverse pages, not just the papers'
own citations.

---

## 1. Executive Summary

Two things are true at once, and the rest of this report follows from holding both:

1. **The Semester-1 platform this dissertation needed already exists and runs.** This repo
   *is* the "secure monitoring and attack-simulation platform" the review slides' own
   conclusion assigns to Semester 1: real MIT-BIH/BIDMC ECG replay, patient-specific
   baseline, temporal + cross-sensor scoring, attack simulation, and a dashboard. It is not
   what this new scope is asking for.
2. **The two reference papers describe a separate, much larger piece of work**:
   independently reproducing two *existing* published papers (Paper 1's ResNet-18 adversarial
   gatekeeper, Paper 2's THECF + HGAN-SVM-DT + SFOA-CNN layered MIoT pipeline) end-to-end,
   with real training and an honest accuracy comparison against their reported numbers. This
   is new — nothing in the repo touches adversarial attacks, THECF, GAN/SVM/DT, SFOA, or image-
   based arrhythmia CNNs. It is also **not** the dissertation's own proposed system; it is
   closer to a "related-work reproduction" chapter that would sit alongside it.

**Headline feasibility call, per paper:**

| | Paper 1 (ResNet-18 adversarial gatekeeper) | Paper 2 (THECF+HGAN-SVM-DT+SFOA-CNN) |
|---|---|---|
| Methodology reproducible? | Yes, with caveats | Yes, closely |
| Datasets fully public? | 3 of 4 — see §3 | Yes, both on PhysioNet |
| Compute fits this machine (CPU only, no GPU)? | Workable but slow; original used a V100 | Yes — **original paper itself ran on a 2.67GHz CPU laptop with 3.86GB RAM** |
| Exact published accuracy reproducible? | Unlikely to match digit-for-digit (see §2) | Plausible to approach, not guaranteed to match |
| Biggest blocker | Their exact noisy/clean *labels* were hand-annotated and never released | None structural; mainly effort/time |

Net: **Paper 2 is the more tractable reproduction on this machine.** Paper 1 is reproducible
in spirit and method, but its headline accuracy numbers depend on a manual annotation
protocol the authors applied themselves and did not release, so our own re-annotation will
introduce label drift that the original authors' numbers can't account for.

---

## 2. Published-Accuracy Reproduction Feasibility

| Paper | Published headline accuracy | Required dataset | Required architecture | Reproduction feasibility | Missing details |
|---|---|---|---|---|---|
| **Paper 1** | 99.20% ACC / 95.42% F1 overall (Table 6); near-100% at ε≥0.03 for most attack/dataset combos (Tables 3–5) | ECG-ID, CINC-2011, CINC-2014, teleECG | ResNet-18 (described layer-by-layer, but **1D vs 2D input is never stated explicitly** — inferred 1D given inputs are raw 10 s segments, not images) | **Medium** — architecture and attacks (FGSM/PGD/HopSkipJump/Boundary) are standard and implementable with existing libraries (`adversarial-robustness-toolbox`, `foolbox`). The leave-one-dataset-out protocol is clear. | The "noisy vs noise-free" ground truth was **manually annotated by the authors** per their own stated rule (QRS+T visible → clean; BW/EM/MA/PLI distortion → noisy) and never published (`Data availability: No data was used`). We cannot get their exact label file — we'd re-derive our own under the same rule, which will not reproduce their numbers bit-for-bit. |
| **Paper 2** | Detection: 99.80% ACC / 99.88% recall / 99.83% F1. Classification: 99.56% ACC / 98.97% recall / 99.23% F1. Energy reduction 85.2%. | MIT-BIH Arrhythmia DB (+ NSTDB for noise robustness) | THECF (fully specified thresholds) + HGAN-SVM-DT (SVM+DT adversarially tuned by SFOA) + CNN on differential-image representations, both stages SFOA-optimized | **Medium-High** — THECF's three thresholds are given as exact numbers (§3 below) and are pure signal processing, no training required. SFOA is a real, citable 2024 metaheuristic (Zhong et al.), implementable from its own publication. The "HGAN" is **not a conventional neural GAN** — it's SVM-as-generator / DT-as-discriminator in an adversarial *training loop*, which is non-standard and under-specified (see §15). | Exact 32 DWT/morphological features reference "the MB Assiouni method" with no further citation findable — a named feature set we could not identify; we'll need to substitute a documented, equivalent 32-feature DWT+morphology set and flag it as a labelled assumption, not the original. Processed data ("upon request") isn't published either. |

**Important framing for the dissertation panel:** neither paper exposes its processed
dataset or exact feature/label files. Reproduction here means *faithful re-implementation of
the stated methodology*, evaluated honestly against the *same metrics*, not byte-identical
numbers. This is explicitly what the project requirements themselves require ("Never manipulate test data or
labels to achieve the published accuracy... If exact accuracy cannot be reproduced, explain
the technical reasons").

---

## 3. Original Dataset Investigation (highest priority, verified live)

| Dataset | Official source | Format | Size | Physiological signals | Sampling rate | Annotations | License/access | Suitability | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| **MIT-BIH Arrhythmia DB** | `physionet.org/content/mitdb/1.0.0/` | WFDB (`.dat`/`.hea`/`.atr`) | 48 half-hour 2-channel records, 47 subjects | ECG only (modified-lead-II + V1/V2/V5 variably) | 360 Hz | Full beat + rhythm annotations by ≥2 cardiologists | ODC-BY, fully open | **Already integrated** in this repo (`services/detector/app/mitdb.py`, via `wfdb.rdrecord(..., pn_dir="mitdb")`) | Single/dual-channel only; no second vital sign |
| **MIT-BIH Noise Stress Test DB (NSTDB)** | `physionet.org/content/nstdb/1.0.0/` | WFDB | 12 half-hour noisy records + 3 noise records (bw, em, ma) | ECG + isolated noise traces | 360 Hz | Noise type labelled by record | ODC-BY, open | Used by Paper 2 for THECF robustness testing | Noise-only stress records, not full clinical diversity |
| **ECG-ID Database** | `physionet.org/content/ecgiddb/1.0.0/` | WFDB | 310 recordings, 90 subjects | ECG only, single lead I | 500 Hz | 10 annotated beats/record; no noise/clean label | ODC Attribution v1.0, open (DOI 10.13026/C2J01F) | Confirmed public; matches Paper 1's stated use | **No built-in noisy/clean label** — Paper 1's noise annotation is the authors' own manual pass, not part of the released dataset |
| **CinC Challenge 2011** | `physionet.org/content/challenge-2011/` (current) / mirrored at `archive.physionet.org/pn3/challenge/2011/` | WFDB, 12-lead, `set-a`/`set-b`/`set-c` | set-a ≈103MB, set-b ≈51MB | ECG (12-lead), designed for *signal-quality* classification (acceptable/unacceptable), not noise-type labelling | 500 Hz | Per-record quality label (not BW/EM/MA breakdown) | Open, PhysioNet terms | Usable, but again needs re-mapping from "quality label" to Paper 1's noise taxonomy | Same manual-remapping caveat as ECG-ID |
| **CinC Challenge 2014** | `physionet.org/content/challenge-2014/1.0.0/` | WFDB, multimodal (ECG + other signals) | ~111MB archive | ECG + up to 8 signals/record ("Robust Detection of Heart Beats in Multimodal Data") | Varies | Beat annotations only (no beat-type distinction) | Open, PhysioNet terms | Usable for ECG channel extraction | Multimodal complexity beyond what's needed; again no noise-type label |
| **teleECG** | **Not on PhysioNet.** Identified as the UNSW "TELE ECG Database" — 250 lead-I, 30 s recordings from home-dwelling COPD/CHF patients, hosted on **Harvard Dataverse**, DOI `10.7910/DVN/QTG0EP` | Per Dataverse record (not yet opened directly) | 250 short recordings | ECG only, telehealth dry-electrode | Not confirmed (check Dataverse page) | QRS + artifact masks (UNSW detector), no BW/EM/MA/PLI label | Needs direct verification on Dataverse before download scripting | Likely usable, but **this is the one real gap**: the paper cites it as if PhysioNet-hosted; it is not | Must verify Dataverse access terms before building a download script — do not assume open access until checked |

**Additional physiological channels requested in the project requirements (HR, SpO₂, BP, respiration)**: none
of the six datasets above carry synchronized SpO₂/BP/respiration alongside ECG. The only
PhysioNet resource in this space already in use by this project is **BIDMC** (`bidmc`,
real concurrent ECG + PPG — already wired into `ecg-context-guard`'s cross-sensor module).
BIDMC is **not** one of the six datasets named in either paper, but it remains the best
candidate already on hand for the dissertation's own cross-sensor-context idea (§4, §7).

**Bottom line on §3:** 5 of 6 named datasets are real, public, and already-known-good access
patterns (same `wfdb.rdrecord(..., pn_dir=...)` approach already proven in this repo for
MIT-BIH and BIDMC). teleECG is the one dataset that needs a different access path
(Dataverse, not PhysioNet) and should be verified before anything is built around it. None of
the four Paper-1 datasets ship with a usable noisy/clean label — that annotation step is
something we would have to redo ourselves, using the paper's stated rule, as a clearly labelled
re-derivation, not a recovered original.

---

## 4. New Derived Dataset Generation Feasibility (for the dissertation's own semantic-manipulation detector — separate from reproducing Papers 1 & 2)

The dissertation's actual contribution (per the review slides) is detecting **subtle, clinically
plausible manipulation** that stays inside normal-looking ranges — a different problem from
either paper's "noise vs clean" (Paper 1) or "abnormal vs normal rhythm" (Paper 2)
framing. Neither paper's dataset contains this label, so a derived dataset is required
regardless of whether Papers 1/2 get reproduced.

- **Base data:** MIT-BIH (ECG-only patients, synthetic second vital — already built) + BIDMC
  (real concurrent ECG+PPG patients — already built), both already integrated in
  `ecg-context-guard`.
- **Valid transformations** (already partially implemented in `services/detector/app/attack.py`
  per `docs/building/05-detection-algorithm.md`): amplitude drift, RR-interval stretch —
  these are exactly the "physiologically plausible manipulation" category the project requirements ask
  about. Replay attacks and cross-sensor-inconsistency attacks (feed stale/mismatched PPG
  against live ECG) are natural next additions and straightforward given the existing
  architecture.
- **Ground-truth/leakage discipline:** the existing repo already separates calibration
  windows (baseline) from live/attacked windows per patient, and the detection algorithm doc
  (`docs/building/05-detection-algorithm.md`) covers the exact pitfalls hit when real sensor
  noise was introduced (false positives from genuine two-sensor disagreement) — this
  experience directly answers the project requirements' "how to prevent data leakage / how
  to validate the derived dataset" questions; it does not need to be solved from scratch.
- **Conclusion:** yes, a derived dataset built on MIT-BIH + BIDMC with the existing
  attack-simulation module, extended with 2–3 more attack types, is the right path for the
  dissertation's own semantic-manipulation detector. This is **separate budget/time** from
  reproducing Papers 1 and 2, and should not be conflated with them in the final report
  structure.

---

## 5. Proposed System Analysis (from the review slides) vs. the Two Papers

The review slides are explicit (slide 21, Conclusion) that:
- Semester 1 → secure monitoring + attack-simulation platform (**done**, this repo).
- Semester 2 → the proposed **context-aware detection mechanism** (patient-specific baseline +
  temporal + cross-sensor) — not yet built as an ML/DL model; currently a documented,
  inspectable weighted-threshold scheme (`docs/building/05-detection-algorithm.md`), by
  deliberate design choice already recorded in this repo ("Why not ML/DL" section).

Papers 1 and 2 are **literature-review entries** (Article 4 and Article 2 on the review slides' own
Literature Review slides), explicitly limitation-flagged by the review slides themselves:
- Paper 1: *"does not specifically model patient-specific physiological behaviour or semantic
  manipulation."*
- Paper 2: *"mainly detects abnormal/faulty signals; evaluation relies heavily on benchmark
  data; real-world diverse patient validation still needed."*

So: reproducing them is legitimate **related-work grounding** — it lets the dissertation make
an evidence-backed novelty claim ("we reproduced X and Y; here is exactly what they still
don't cover") rather than an asserted one. It should **not** replace the proposed system, and
should not be presented as the dissertation's own contribution.

---

## 6. Research Gap

Confirmed from the papers + review slides, not invented:

- Paper 1 solves: filtering out noisy/adversarially-perturbed ECG before storage, attack-data-
  independent (gatekeeper trained without seeing adversarial examples).
- Paper 2 solves: energy-efficient edge/cloud split for anomaly detection + 7-class arrhythmia
  classification, with a sensor-fault pre-filter (THECF).
- Neither solves: **attacks that stay inside clinically plausible ranges** (both frameworks
  assume the corruption shows up as noise-like signal distortion or outright abnormal rhythm —
  exactly the gap the review slides' own Research Gap slide states). Neither uses **patient-specific
  historical baselines**, neither does **cross-sensor consistency checking**, and neither
  targets **temporal plausibility within a single session** (a value that's "normal" for the
  population but abruptly wrong for *this* patient right now).
- This is a real, literature-supported gap, not a novelty claim made without evidence — it
  matches what the already-built detector in this repo targets.

---

## 7. Proposed Technical Architecture (Semester 2 target, reusing Semester 1 platform)

| Module | Input | Processing | Algorithm(s) | Output | Reuse from Papers 1/2? |
|---|---|---|---|---|---|
| ECG acquisition | Raw MIT-BIH/BIDMC stream | Replay at native rate | `wfdb.rdrecord` | Windowed signal | — (already built) |
| Preprocessing | Raw window | Filter, resample, normalize | Median + band-pass filter (reuse **THECF's exact filter spec** from Paper 2 as a documented, cited choice) | Clean window | Paper 2 (THECF filters) |
| Patient-specific baseline | Calibration windows | Per-patient HR/RR/QRS stats | Already implemented (`baseline.py`) | z-score reference | — (already built) |
| Temporal analysis | Live window vs. own history | Weighted z-score, sudden-change detection | Already implemented (`detector.py`) | Temporal score | — (already built) |
| Cross-sensor context | ECG-HR vs. PPG-HR (BIDMC) or synthetic stand-in | Disagreement z-score | Already implemented (`cross_sensor.py`) | Cross-sensor score | — (already built) |
| Semantic attack simulation | Clean window | Inject amplitude drift / RR stretch / (new) replay / cross-sensor mismatch | Already implemented (`attack.py`), extend with 2 new types | Labelled attack window | — (already built, extend) |
| Context-aware detection | 3 scores above | Weighted combination → verdict | Current: documented threshold scheme. Semester-2 option: train a lightweight classifier (e.g. SVM/DT, **borrowing Paper 2's SVM+DT idea but on the dissertation's own 3 context features**, not image/DWT features) | genuine / suspicious / manipulated | Paper 2 (SVM/DT as a *technique*, not its feature set) |
| Classification/decision | Verdict stream | Alerting rules | — | Alert | — |
| Alert/dashboard | Verdicts | Visualize | Already implemented (React dashboard) | UI | — (already built) |

**What's reusable vs. new, stated plainly:** THECF's exact, numeric filter/threshold design
(Paper 2) is directly reusable as a documented preprocessing stage, independent of whether
the full HGAN-SVM-DT/SFOA/CNN pipeline is separately reproduced. The adversarial-attack
*concept* (Paper 1) is a candidate 4th attack type for the dissertation's own attack simulator
(an "adversarial-style" perturbation distinct from amplitude-drift/RR-stretch), but Paper 1's
own ResNet-18 defence model is not reusable for the dissertation's context-aware problem,
since it detects noise/attack *distortion*, not *semantic plausibility*.

---

## 8. Experimental Design

Three **non-overlapping** experiment tracks (the project requirements explicitly warn against mixing them):

1. **Independent reproduction of Paper 1** — ResNet-18 gatekeeper, same 4 datasets (minus the
   teleECG caveat), same 4 attacks, same leave-one-dataset-out protocol, report ACC/F1/
   confusion matrix/ROC-AUC/FPR/FNR, and an explicit side-by-side table against Tables 3–6 of
   the original with a written explanation of any gap (most likely driver: re-annotated
   noisy/clean labels, per §2).
2. **Independent reproduction of Paper 2** — THECF (pure signal processing, no training) →
   HGAN-SVM-DT (SFOA-tuned) → differential-image CNN, same MIT-BIH 5-fold patient-independent
   CV, same metrics, same ablation structure as their Table 4, side-by-side against their
   Table 2/3/4.
3. **Dissertation's own proposed system** — baseline (current threshold scheme, already
   validated per `docs/building/05-detection-algorithm.md`) vs. a Semester-2 ML variant,
   evaluated with its own ablations (baseline-only vs. +temporal vs. +cross-sensor vs. full),
   patient-independent, reporting accuracy/precision/recall/F1/specificity/sensitivity/
   ROC-AUC/FPR/FNR/attack-detection-rate/inference time, **and** comparing against Track 1 and
   Track 2's detectors run *as baselines* on the dissertation's own semantic-manipulation test
   set (this is the legitimate, non-mixing way to show "existing methods miss this; ours
   doesn't" — run their reproduced models on a task they were never designed for and report
   that honestly, rather than reusing their self-reported numbers on their own task).

---

## 9. Implementation Feasibility (this machine, checked directly)

- **Internet access:** confirmed working (PhysioNet reachable, HTTP 200).
- **GPU:** none present (`nvidia-smi` fails — no NVIDIA driver). CPU-only.
- **Python ML stack:** not yet installed (`torch` missing) — needs a fresh `venv` (same
  pattern as `services/detector`), `requirements.txt` per the project requirements' list (numpy, pandas,
  scipy, wfdb, scikit-learn, pytorch or tensorflow, matplotlib, seaborn, neurokit2), plus
  `adversarial-robustness-toolbox` or `foolbox` for Paper 1's four attacks.
- **Hardware fit, per paper:**
  - Paper 2's own authors trained on an **Intel i5 laptop, 3.86GB RAM, no GPU** — this
    machine is a strictly better fit for Paper 2 than the original paper's own setup was.
    Their own quoted wall-clock (45–65 min edge-model training, 90–120 min CNN training, with
    SFOA population 30 / 50 iterations) is a realistic planning number here too.
  - Paper 1's authors used a **Tesla V100** for ResNet-18 + 4-attack generation across ~15K
    segments total. On CPU, this is still tractable (ResNet-18 is small; total data is in the
    thousands of 10-second segments, not millions) but meaningfully slower — budget multiple
    hours per leave-one-dataset-out fold rather than minutes, and expect adversarial-example
    generation (especially iterative PGD/HopSkipJump across 7 epsilon values) to dominate
    wall-clock time, not model training itself.
- **Recommended environment:** isolate as `research/Common/venv`, mirroring the existing
  `services/detector` Python-isolation convention already used in this repo, rather than
  touching the Node/Express/React app at all.

---

## 10–17. Condensed: Report Format, Architecture, Experimental Design, Requirements, Limitations, Roadmap, Deliverables

Folded into the sections above per topic, rather than repeated as separate boilerplate
sections, to keep this report decision-useful rather than padded. The one item not yet
covered:

**Potential challenges/limitations, stated plainly:**
- Paper 1's noisy/clean labels must be re-derived by us (§2, §3) — flag every result as
  "our re-annotation," never claim it's their original label set.
- Paper 2's "32 DWT/morphological features via the MB Assiouni method" — this exact named
  method could not be identified from any source checked; we will substitute a documented,
  cited, equivalent 32-feature DWT + morphology set and label it as a justified substitution,
  per the project requirements' own instruction ("propose a clearly labelled, justified implementation
  assumption" when a detail is missing).
- Paper 2's "HGAN" is SVM+DT in an SFOA-tuned adversarial loop, not a neural GAN — this is
  unusual enough that it should be implemented exactly as described (not swapped for a
  conventional GAN) and flagged to a reviewer as a notable, slightly non-standard design
  choice in the original paper itself.
- teleECG access path differs from the other three Paper-1 datasets (Dataverse, not
  PhysioNet) — verify terms before scripting a downloader.
- No GPU means Paper 1's attack-generation step, not model training, is the likely time
  sink — plan accordingly rather than assuming training dominates.

---

## 18. Implementation Roadmap

| Stage | Input | Tasks | Output | Done when |
|---|---|---|---|---|
| 1. Paper analysis (this report) | 2 reference papers + review slides | Extract specs, assess feasibility | This document | You've reviewed and approved scope/sequencing below |
| 2. Dataset acquisition & validation | §3 | Script `wfdb.rdrecord` pulls for MIT-BIH/NSTDB/ECG-ID/CinC2011/CinC2014; verify teleECG's Dataverse access; re-derive noisy/clean labels for Paper 1 under its stated rule | `research/Common/datasets/` cache + a written label-derivation note | Every dataset loads and is spot-checked against the paper's stated record counts (Table 2) |
| 3. Paper 1 implementation | Stage 2 data | ResNet-18 (1D), 4 attacks via ART/foolbox, leave-one-dataset-out training | `research/Paper_1_Attack_Independent_Defence/` | Metrics computed on held-out folds, compared to Tables 3–6 |
| 4. Paper 1 evaluation | Stage 3 | Confusion matrices, ROC, FPR/FNR, comparison table + gap analysis | Report section | Comparison table written, gaps explained |
| 5. Paper 2 — THECF + preprocessing | §3 data | Implement 3-layer threshold detector exactly as specified | `research/Paper_2_Layered_MIOT_Framework/THECF/` | Matches paper's accuracy ballpark (99.9% clean / 98.9% at SNR=-6dB) on our own NSTDB run |
| 6. Paper 2 — HGAN-SVM-DT + SFOA | Stage 5 | Implement SFOA from its own publication; SVM+DT adversarial loop | `.../HGAN_SVM_DT/`, `.../SFOA/` | Ablation table structurally matches their Table 4 pattern (each component adds a measurable increment) |
| 7. Paper 2 — differential image + CNN | Stage 6 | `ecg2image` port to Python, 7-class CNN | `.../differential_transformation/`, `.../CNN_classifier/` | 5-fold patient-independent CV run completes |
| 8. Paper 2 evaluation | Stage 7 | Same metrics as paper, comparison table | Report section | Comparison table written, gaps explained |
| 9. Derived dataset + proposed system (Semester 2 track) | §4, §7 | Extend `attack.py` with 2 new attack types; decide threshold-vs-ML for context-aware detector | Updated `ecg-context-guard` detector | Ablation (baseline/+temporal/+cross-sensor/full) run and documented, same rigor as `docs/building/05-detection-algorithm.md` already shows |
| 10. Dissertation documentation | All above | Assemble final comparison (Papers 1 & 2 reproduction + proposed system), write up for panel | Final report | Ready for review |

---

## 19. Final Recommendations

1. **Keep the three tracks separate** in the repo and in the write-up: Paper 1 reproduction,
   Paper 2 reproduction, and the dissertation's own proposed system. Do not let Paper 2's
   SVM/DT or Paper 1's ResNet-18 quietly become "the proposed system" — the review slides' own
   Research Gap slide is explicit that neither paper covers the dissertation's actual target
   problem.
2. **Start with Paper 2, not Paper 1**, if sequencing matters for time budget — it's the more
   tractable reproduction on this CPU-only machine (the original authors' own hardware was
   weaker than this machine), has fully-public datasets, and its THECF stage is immediately
   reusable in the existing `ecg-context-guard` preprocessing regardless of whether the rest
   of Paper 2 gets reproduced.
3. **Treat Paper 1's and Paper 2's reported accuracy as reference targets, not contractual
   outputs** — per the project requirements' own instruction. Report actual numbers from actual training
   runs, with an honest gap analysis grounded in the specific missing details identified in
   §2–§3 (re-annotated labels for Paper 1; a substituted feature set for Paper 2), not a
   promise to match them.
4. **Verify teleECG's Dataverse access terms before writing any downloader for it** — it is
   the one dataset in this whole brief that is not where the source paper implies it is.
5. **Do not begin Stage 3 (Paper 1 code) or Stage 5 (Paper 2 code) until you confirm**: (a) this
   scope and sequencing, (b) where this work should live (recommended:
   ``research/`, kept separate from the Node/React app, mirroring
   the existing `services/detector` Python-isolation pattern), and (c) whether both papers are
   in scope for this semester or whether time constraints mean picking one.
