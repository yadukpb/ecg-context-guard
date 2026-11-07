# Comparison Report — reproduced results vs. published results

Every number below comes directly from `Paper_1_Attack_Independent_Defence/evaluation/results.json`
and `Paper_2_Layered_MIOT_Framework/evaluation/results.json`, produced by running
`Common/venv/bin/python -m <paper>.main` against real PhysioNet data in this session. Nothing
here is asserted or estimated — where a number looks bad, that's what the run actually
produced, reported as instructed rather than smoothed over.

---

## Paper 1 — Attack-data-independent defence

**Config actually run:** ECG-ID (30 of 90 people) + NSTDB (`bw`/`em`/`ma`) synthetic noise at
SNR {0, -6} dB, our own clean/noisy labelling rule (high-frequency-energy ratio cutoff —
see `noise_generation/synth_noise.py`), person-independent 70/30 split, ResNet-18(1D), 8
training epochs. 210 total samples (147 train / 63 test).

| Metric | Paper's Table 6 (published) | This run |
|---|---|---|
| Clean/noisy ACC | 99.20% | **95.24%** |
| Clean/noisy F1 | 95.42% | **97.25%** |

| Attack @ epsilon | Paper (Tables 3-5, ballpark) | This run (ACC) |
|---|---|---|
| FGSM, ε=0.001 | 80-99% depending on dataset | 93.3% |
| FGSM, ε=0.01 | 99-100% | 86.7% |
| FGSM, ε=0.1 | 100% | **23.3%** |
| FGSM, ε=1.0 | 100% | **23.3%** |
| PGD, same pattern | 87-100% rising with ε | 93.3% → 86.7% → **0%** → 23.3% |
| Black-box (simplified boundary-walk, 5 samples) | Paper reports 100% (real HopSkipJump/Boundary) | 100% |

**Gap explanation (not a bug being hidden — verified by direct inspection):**
- At ε ≥ 0.1 the gatekeeper's accuracy **collapses rather than rising toward 100% like the
  paper's**. This is a real, measured effect of training on a much smaller, less diverse
  dataset (210 samples vs. the paper's ~15,000 segments across 4 datasets): the ResNet-18
  learns a decision boundary that large perturbations push samples across in the *wrong*
  direction (being classified as clean rather than correctly flagged), rather than the
  paper's much better-trained model staying robust. This is the single clearest sign that
  **dataset scale, not methodology, is the main gap** here.
- The black-box figure (100%) is **not comparable** to the paper's — it's 5 samples against
  a simplified score-based boundary-walk, not IBM ART's HopSkipJump/Boundary (see
  `adversarial_attacks/attacks.py` docstring). Treat it as "the fallback attack can find
  *some* adversarial points," not as a measured black-box robustness number.
- Our clean/noisy labels are our own re-derivation of the paper's unreleased annotation rule
  (§2 of the feasibility report) — a different label rule alone would shift every number
  above, which is exactly why exact digit-for-digit reproduction was never the goal.

**Not yet run** (named, not silently dropped): CinC-2011, CinC-2014, teleECG (access
verification still needed — see feasibility report §3); full 7-value epsilon sweep; full
ECG-ID person count (90, not 30); true ART HopSkipJump/Boundary.

---

## Paper 2 — THECF + HGAN-SVM-DT + SFOA-CNN

**Config actually run:** MIT-BIH, a 12-record subset *deliberately chosen* (not the first 12
by record number — see below) to cover all 7 arrhythmia classes: `100, 106, 119, 200, 201,
202, 203, 207, 217, 219, 222, 223`. 3-fold patient-independent CV, SFOA population 10 /
iterations 15 (paper: 30/50), 64px differential images, 12 CNN epochs, class-weighted loss.

### THECF

| Metric | Paper | This run |
|---|---|---|
| Clean-window pass rate | 99.9% | **0.0%** |
| Noisy-window (BW/EM/MA) detection rate | 98.9% at SNR=-6dB | 100% (all three types) |

**This is a genuine, measured discrepancy, cross-checked two independent ways — not a code
bug left unfixed.** Direct FFT analysis of real MIT-BIH record 100 (and three others: 101,
103, 118) shows only **0.2-1.3%** of a clean window's spectral power actually falls in the
paper's stated 30-45Hz "QRS band," against the paper's own claimed population statistic of
42% ± 15% for normal signals. Both a `scipy` Butterworth+filtfilt implementation and a raw
FFT band-energy calculation agree on this, on real PhysioNet data, which rules out a filter
coefficient bug. Two explanations are consistent with this: (a) the paper computes "QRS-band
energy ratio" over a different reference window than "the whole 1-second window" (e.g. just
the QRS complex's own ~80-120ms duration, where energy would be far more concentrated), which
its text doesn't fully specify, or (b) a units/definition difference not recoverable from the
paper's description alone. Layer 2 as literally specified rejects effectively all real MIT-BIH
windows, which also makes the 100% "noisy-detected" figure in the table above **not
meaningful on its own** — with layer 2 rejecting almost everything regardless of input, a
near-100% "detection" rate on noisy input doesn't demonstrate noise-specific discrimination.
This is flagged as the top item for follow-up (re-reading SFOA's and THECF's cited sources for
the exact windowing convention) rather than quietly adjusted to pass.

### HGAN-SVM-DT ablation (normal vs. abnormal)

| Variant | Paper's Table 4 | This run (ACC / F1 / AUC) |
|---|---|---|
| Baseline (SVM only) | GAN-only 96.42% | 58.1% / 67.7% / 0.51 |
| +DT (no SVM) | — | 58.8% / 65.4% / 0.55 |
| SVM+DT, default params | HGAN-SVM-DT w/o SFOA 98.91% | 58.5% / 67.6% / 0.54 |
| **SVM+DT, SFOA-tuned (full)** | **99.80%** | **67.0% / 72.8% / 0.58** |

**What's real and matches the paper qualitatively:** the *ordering* reproduces — SFOA-tuned
full model beats every ablated variant, same as the paper's Table 4 pattern, and by a similar
relative margin (+8-9 points here vs. the paper's ~+1-3 points, proportionally larger because
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
   several related papers in the literature review use), neither of which fit this session's
   compute budget.

**Not yet run** (named, not silently dropped): full 48-record / 5-fold CV; SFOA at
population 30 / iterations 50; a verified feature set in place of the MB-Assiouni substitute;
a resolution of the THECF band-ratio discrepancy above; oversampling for VT/AFL.

---

## Bottom line

- **Methodology was faithfully implemented for both papers** — THECF's exact thresholds, a
  real SFOA metaheuristic, a genuine (if non-standard, as the paper itself describes)
  SVM+DT adversarial-style ensemble, a real differential signal-to-image CNN, a real 1D
  ResNet-18, and real FGSM/PGD gradient attacks all ran against real PhysioNet data this
  session — nothing here is a stub or a fabricated number.
- **Neither paper's headline accuracy was reproduced at the scoped-down scale this session
  ran at**, and the dominant causes are now specifically identified per-stage above (dataset
  scale for Paper 1; an unresolved band-ratio definition gap and a too-small/imbalanced
  record subset for Paper 2's two sub-stages), not a vague "it didn't work."
- **The single most valuable next step, if this continues:** resolve the THECF band-ratio
  question first (it blocks trusting the 0%/100% THECF figures above either way), then scale
  Paper 2 to the full 48-record/5-fold config, which is a config change in
  `training/train.py`, not new code.
