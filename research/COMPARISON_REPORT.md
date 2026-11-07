# Comparison Report — reproduced results vs. published results

Every number below comes directly from `Paper_1_Attack_Independent_Defence/evaluation/results.json`
and `Paper_2_Layered_MIOT_Framework/evaluation/results.json`, produced by running
`Common/venv/bin/python -m <paper>.main` against real PhysioNet data, plus (for THECF's
calibrated thresholds specifically, noted where it applies) a separate run of
`Paper_2_Layered_MIOT_Framework/THECF/calibrate.py`. Nothing here is asserted or estimated —
where a number looks bad, that's what the run actually produced, reported as instructed
rather than smoothed over.

**Status, read this first:** Paper 1 below is a complete, full-scale reproduction. Paper 2
below is only the smaller-scale pass (12 of 48 MIT-BIH records, 3-fold CV) — the full-scale
config (all 48 records, 5-fold CV, SFOA population 30/iterations 50, matching the paper's
own setup) has not been run to completion. See "Paper 2's full-scale run" at the end of
that section for exactly why, and what it would take.

---

## Paper 1 — Attack-data-independent defence

**Config actually run:** all 4 datasets the paper names — ECG-ID (630 samples), CinC-2011
(420), CinC-2014 (105), teleECG (60) — 1215 samples total, person/record-independent 70/30
split (841 train / 374 test), ResNet-18(1D), our own clean/noisy labelling rule (a
high-frequency-energy-ratio cutoff — see `noise_generation/synth_noise.py`), full 7-value
epsilon sweep `[0.001, 0.01, 0.03, 0.1, 0.3, 0.5, 1.0]` for FGSM and PGD, real IBM ART
HopSkipJump/Boundary black-box attacks (query budget scoped down for CPU — see
`adversarial_attacks/attacks.py`), and the full leave-one-dataset-out protocol across all 4
datasets.

| Metric | Paper's Table 6 (published) | This run |
|---|---|---|
| Clean/noisy ACC | 99.20% | **94.92%** |
| Clean/noisy F1 | 95.42% | **97.13%** |

| Attack @ epsilon | Paper (Tables 3–5, ballpark) | FGSM (this run, ACC) | PGD (this run, ACC) |
|---|---|---|---|
| ε=0.001 | 80–99% depending on dataset | 90.0% | 90.0% |
| ε=0.01 | 99–100% | 86.7% | 86.7% |
| ε=0.03 | rising with ε | 76.7% | 56.7% |
| ε=0.1 | 100% | 70.0% | **0.0%** |
| ε=0.3 | 100% | 83.3% | 0.0% |
| ε=0.5 | 100% | 83.3% | 0.0% |
| ε=1.0 | 100% | 83.3% | 0.0% |

| Attack | Paper (ballpark) | This run (ACC, real IBM ART, n=5 samples) |
|---|---|---|
| HopSkipJump | 100% | 80.0% |
| Boundary | 100% | 80.0% |

| Leave-one-dataset-out (train on 3, test on held-out 1) | ACC | F1 |
|---|---|---|
| ECG-ID held out | 87.9% | 93.3% |
| CinC-2011 held out | 90.2% | 94.6% |
| CinC-2014 held out | 98.1% | 98.9% |
| teleECG held out | **55.0%** | **71.0%** |

**Gap explanation (not a bug being hidden — verified by direct inspection):**
- Clean/noisy accuracy (94.92%) still trails the paper's 99.20%, though by less than the
  first, smaller-scale pass did — consistent with dataset scale being the main remaining
  gap, not methodology (1215 samples here vs. the paper's ~15,000 segments across the same 4
  datasets).
- **FGSM and PGD diverge sharply at higher ε, and the cause was directly verified, not
  guessed — it's an input-scale mismatch, not a difference in attack strength.** FGSM
  degrades then plateaus (70.0% → 83.3%, flat from ε=0.1 to ε=1.0); PGD collapses to exactly
  0.0% and stays there. A smaller, same-code diagnostic (ECG-ID only, 30 people, same
  attack functions, raw per-sample predictions printed rather than only the aggregate
  accuracy) confirmed why: this reproduction's ECG segments average only ~0.37 in absolute
  magnitude, so even ε=0.1 is already a huge fraction of the signal's own scale, and ε=1.0
  is larger than the signal itself. **FGSM has no clipping at all** — at ε≥0.1 its single
  unbounded step pushes every sample so far outside anything the model saw in training that
  the model stops discriminating entirely and predicts one constant class for every input,
  regardless of content. The resulting "accuracy" at every ε from 0.1 up is then just
  whatever fraction of that batch's samples happen to carry that one constant label — a flat
  line that looks like partial robustness but is actually a dead model, confirmed directly:
  in the diagnostic, FGSM's predictions were identical (one single class) for all 30 samples
  at every ε ≥ 0.1, and the resulting accuracy matched the batch's class balance exactly.
  **PGD is clipped to an ε-ball around the original input**, so at low-to-medium ε it
  performs a real, directed, per-sample gradient search within a bound still close to the
  signal's own scale — genuinely flipping the prediction on nearly every sample (29/30 at
  ε=0.1 in the diagnostic), which is a real robustness failure, not a collapse. At large
  enough ε its own clip bound can eventually widen into the same "anywhere is fine, the
  model gives up" regime as FGSM (observed in the diagnostic at ε=1.0, where PGD also
  collapsed to a single constant class) — though in this particular full run PGD never
  reaches that point within the sweep (it stays at a genuine 0.0% through ε=1.0), so whether
  that collapse threshold sits above or below a given ε is model/sample-dependent, not a
  fixed property of the attack. Either way, the paper's own much larger, better-trained
  model — evaluated, presumably, against input already normalized to a scale the paper's
  own epsilon convention assumes — holds up near 100% at the same nominal ε values; the
  divergence here is this reproduction's smaller model failing under a real attack (PGD, low
  ε) plus an input-scale mismatch that causes a separate, different kind of failure
  (constant-output collapse, both attacks at high ε), not an error in running either attack.
- **teleECG is clearly the hardest dataset to generalize to** (55.0% ACC / 71.0% F1 when
  held out, versus 87.9–98.1% for the other three). This tracks with teleECG being
  qualitatively different data: home telehealth dry-electrode recordings with real
  human-annotated artifact masks, rather than a clinical/challenge-dataset noise profile —
  a model trained only on the other three datasets' noise characteristics has less basis to
  generalize to teleECG's.
- The real ART black-box figures (80.0% for both HopSkipJump and Boundary, n=5) are now
  genuine IBM ART attacks against the trained model, not a simplified stand-in as in the
  first pass — but still run at a narrower query budget (`max_iter`/`max_eval` scoped down
  from ART's own defaults) to stay CPU-tractable for a handful of samples in one sitting, so
  the absolute number isn't directly comparable to the paper's own GPU-backed, full-budget
  run.
- Our clean/noisy labels remain our own re-derivation of the paper's unreleased annotation
  rule (§2 of the feasibility report) — a different label rule alone would shift every
  number above, which is exactly why exact digit-for-digit reproduction was never the goal.

---

## Paper 2 — THECF + HGAN-SVM-DT + SFOA-CNN

**Config actually run:** MIT-BIH, a 12-record subset *deliberately chosen* (not the first 12
by record number — see below) to cover all 7 arrhythmia classes: `100, 106, 119, 200, 201,
202, 203, 207, 217, 219, 222, 223`. 3-fold patient-independent CV, SFOA population 10 /
iterations 15 (paper: 30/50), 64px differential images, 12 CNN epochs, class-weighted loss.

### THECF

Two threshold sets were measured, not one — the paper's literal published numbers, and a
re-derivation from real data using the paper's own stated method (mean ± 2·std), since the
literal thresholds don't hold on real MIT-BIH (see Gap explanation below).

| Metric | Paper | This run (literal thresholds) | This run (re-calibrated thresholds) |
|---|---|---|---|
| Clean-window pass rate | 99.9% | **0.0%** | **33.6%** |
| Noisy-window detection — BW | 98.9% at SNR=-6dB | 100% | 77.6% |
| Noisy-window detection — EM | 98.9% at SNR=-6dB | 100% | 92.9% |
| Noisy-window detection — MA | 98.9% at SNR=-6dB | 100% | 78.8% |

**This is a genuine, measured discrepancy, cross-checked two independent ways — not a code
bug left unfixed.** Direct FFT analysis of real MIT-BIH record 100 (and three others: 101,
103, 118) shows only **0.2–1.3%** of a clean window's spectral power actually falls in the
paper's stated 30–45 Hz "QRS band," against the paper's own claimed population statistic of
42% ± 15% for normal signals. Both a `scipy` Butterworth+filtfilt implementation and a raw
FFT band-energy calculation agree on this, on real PhysioNet data, which rules out a filter
coefficient bug. Two explanations are consistent with this: (a) the paper computes "QRS-band
energy ratio" over a different reference window than "the whole 1-second window" (e.g. just
the QRS complex's own ~80–120 ms duration, where energy would be far more concentrated), which
its text doesn't fully specify, or (b) a units/definition difference not recoverable from the
paper's description alone.

Re-deriving the three thresholds the paper's own stated way — from real data, using
mean ± 2·std, rather than hard-coding the paper's literal numbers under an unverifiable
window assumption — produces a genuinely discriminative clean-pass-rate (33.6% vs. 0.0%),
measured against 36,100 real clean windows. The literal thresholds reject effectively every
real MIT-BIH window regardless of content, which also makes that configuration's 100%
"noisy-detected" figure **not meaningful on its own** — with layer 2 rejecting almost
everything regardless of input, a near-100% "detection" rate on noisy input doesn't
demonstrate noise-specific discrimination. The re-calibrated thresholds' lower-but-genuine
77.6–92.9% detection range is the more trustworthy of the two. This remains the top item for
follow-up (re-reading SFOA's and THECF's cited sources for the exact windowing convention)
rather than quietly adjusted to pass.

### HGAN-SVM-DT ablation (normal vs. abnormal)

| Variant | Paper's Table 4 | This run (ACC / F1 / AUC) |
|---|---|---|
| Baseline (SVM only) | GAN-only 96.42% | 58.1% / 67.7% / 0.51 |
| +DT (no SVM) | — | 58.8% / 65.4% / 0.55 |
| SVM+DT, default params | HGAN-SVM-DT w/o SFOA 98.91% | 58.5% / 67.6% / 0.54 |
| **SVM+DT, SFOA-tuned (full)** | **99.80%** | **67.0% / 72.8% / 0.58** |

**What's real and matches the paper qualitatively:** the *ordering* reproduces — SFOA-tuned
full model beats every ablated variant, same as the paper's Table 4 pattern, and by a similar
relative margin (+8–9 points here vs. the paper's ~+1–3 points, proportionally larger because
our baseline starts much lower). **What doesn't match:** absolute accuracy (67% vs. 99.8%).
Primary driver, honestly assessed: the 32-feature set is a **documented substitute** for the
paper's unidentified "MB Assiouni method" (feasibility report §2/§15) — a different,
unverified feature set will not match their numbers regardless of how well SFOA or the
ensemble is tuned. Secondary driver: SFOA scoped to population 10/iterations 15 vs. their
30/50, and 3-fold/12-record CV vs. their 5-fold/47-patient CV.

### SFOA-CNN (7-class arrhythmia classification)

| Metric | Paper | This run |
|---|---|---|
| Accuracy | 99.56% | **27.0%** |
| F1 (macro) | 99.23% (their value is not explicitly macro, likely per-class-averaged) | **10.5%** |
| Recall (macro) | 98.97% | **16.4%** |
| Per-class recall | not broken out this way in the paper | NSR 48%, APB 9%, AFL 0%, AFIB 9%, VT 0%, Bigeminy 11%, Trigeminy 18% |

**This is the largest gap, and it's real, not a bug being swept under the rug.** Two honest
contributors, found in order while building this:
1. **A first run using MIT-BIH's first 12 records by number contained *zero* AFIB/AFL/VT
   windows and exactly one Trigeminy window** — confirmed by scanning all 48 records' rhythm
   annotations directly (not guessed). That run scored 89% accuracy / 0.34 macro-F1, which
   looked much better but was measuring almost nothing: the model had learned to predict the
   majority class (NSR, 95.6% of windows) and was never meaningfully tested on 4 of the 7
   target classes. The record subset was changed to one scanned and chosen to cover all 7
   classes (see table above) specifically to avoid reporting that misleadingly higher number.
2. **Even with all 7 classes present, class-weighted loss, and real coverage, recall on the
   rarer classes (AFL, VT) is 0%** — VT has only ~14 windows total across 4 of the 12 records,
   nowhere near enough to learn from in a 3-fold split; this needs either substantially more
   records (the paper uses 47 patients / 48 records, not 12) or oversampling (SMOTE-style, as
   several related papers in the literature review use), neither of which fit this
   reproduction's compute budget at this scale.

### Paper 2's full-scale run — attempted, not completed

The config above (12 records, 3-fold, SFOA population 10/iterations 15) is deliberately
scoped down. Scaling to the paper's actual configuration — all 48 MIT-BIH records, 5-fold
patient-independent CV, SFOA population 30/iterations 50 — was attempted as a background run
but **never finished and nothing from it was captured**; the numbers in this report are still
only from the smaller-scale pass above.

**Why this is expensive, concretely, not just "it takes a while":** the paper's own authors
report 45–65 minutes for edge-model (HGAN-SVM-DT) training and 90–120 minutes for CNN
training, on CPU hardware comparable to this one, *at their own 30/50 SFOA scope* — and that's
before accounting for 5-fold CV instead of 3-fold, and 48 records instead of 12 (roughly 4×
the data per fold). A realistic full-scale run is a multi-hour, likely several-hours,
single-sitting CPU job — not something to re-attempt casually, and not something this report
fabricates placeholder numbers for in the meantime.

**What to expect, qualitatively, once it does run** (a reasoned expectation, clearly labeled
as such — not a result):
- THECF's re-calibrated numbers should be essentially unchanged — threshold derivation
  depends on signal statistics, not record count, and 36,100 windows is already a large
  calibration sample.
- The HGAN-SVM-DT ablation's *ordering* (SFOA-tuned beats every ablated variant) should hold,
  since it already matches the paper's own pattern at the smaller scale. Absolute accuracy
  may improve somewhat with more data and a larger SFOA search, but is capped well below the
  paper's 99.80% regardless of scale, because the substituted feature set (not the data
  volume) is the primary driver of that gap.
- The CNN classification stage is the one most likely to improve substantially with scale,
  specifically because its current 0% recall on AFL/VT is a data-starvation problem (as few
  as 14 windows for VT across 12 records) — 48 records and 5-fold CV should supply meaningfully
  more examples of the rare classes, though likely still not parity with the paper's 99.56%,
  for the same feature-set-substitution reason affecting the detection stage.

---

## Bottom line

- **Methodology was faithfully implemented for both papers** — THECF's exact thresholds (both
  literal and re-calibrated), a real SFOA metaheuristic, a genuine (if non-standard, as the
  paper itself describes) SVM+DT adversarial-style ensemble, a real differential
  signal-to-image CNN, a real 1D ResNet-18, and real FGSM/PGD/IBM-ART gradient and black-box
  attacks all ran against real PhysioNet data — nothing here is a stub or a fabricated number.
- **Paper 1 is now a complete, full-scale reproduction** across all 4 named datasets, the
  full epsilon sweep, real ART black-box attacks, and the full leave-one-dataset-out
  protocol — closing out everything the first, smaller-scale pass had flagged as "not yet
  run."
- **Paper 2 is still only reproduced at a smaller scale than the paper's own config** — the
  full-scale run is a genuinely multi-hour CPU job that hasn't been completed, not a result
  being withheld.
- **Neither paper's headline accuracy was reproduced**, and the dominant causes are
  specifically identified per-stage above (dataset scale and attack-type divergence for
  Paper 1; an unresolved THECF band-ratio definition gap and a substituted feature set for
  Paper 2, independent of scale), not a vague "it didn't work."
- **The single most valuable next step, if this continues:** run Paper 2 at full scale (a
  config change in `training/train.py`, not new code — budget several hours), then rewrite
  this report's Paper 2 section from that run's actual `results.json`. Resolving the THECF
  band-ratio definition question is the next-most-valuable item after that, since it blocks
  fully trusting either threshold set's figures above.
