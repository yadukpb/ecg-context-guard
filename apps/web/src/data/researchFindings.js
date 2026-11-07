/**
 * Real numbers from the Paper 1 / Paper 2 reproduction in `research/` (a separate Python
 * project in this same repo — not the live detector this web app otherwise presents).
 *
 * Every non-null value here was copied from an actual run's printed output or its
 * `results.json` this session — never typed from memory or guessed to "look right". A field
 * is `null` with a `pending` note when the run that produces it was still in progress at the
 * time this file was written; replace it from the corresponding `results.json` once that run
 * finishes, and remove the pending note — don't leave stale nulls once real numbers exist.
 *
 * Source files:
 *  - research/Paper_1_Attack_Independent_Defence/evaluation/results.json
 *  - research/Paper_2_Layered_MIOT_Framework/evaluation/results.json
 *  - research/COMPARISON_REPORT.md ("Bottom line" — the `gaps` array below)
 */

export const thecf = {
  literal: {
    cleanPassRate: 0.0,
    noisyDetectedRateByType: { bw: 1.0, em: 1.0, ma: 1.0 },
  },
  calibrated: {
    cleanPassRate: 0.3360664819944598,
    noisyDetectedRateByType: { bw: 0.775623268698061, em: 0.9285318559556787, ma: 0.7878116343490305 },
  },
  calibrationDerivation: {
    nCleanWindows: 36100,
    energyMean: 0.4294608381829024,
    energyStd: 0.5239660944802597,
    qrsRatioMean: 0.005744799408660143,
    qrsRatioStd: 0.007416005364233275,
    nccMean: -0.008860815970966517,
    nccStd: 0.2174333566673125,
    thresholds: {
      energyLow: 0.0,
      energyHigh: 1.4773930271434217,
      qrsRatioLow: 0.0,
      qrsRatioHigh: 0.020576810137126693,
      nccAccept: 0.0,
    },
  },
};

// pending: full 48-record / 5-fold / SFOA-30/50 run still in progress — see
// research/Paper_2_Layered_MIOT_Framework/evaluation/results.json once it finishes.
export const paper2 = {
  config: {
    records: "all 48 MIT-BIH records",
    folds: 5,
    sfoaPopulation: 30,
    sfoaIterations: 50,
  },
  detectionAblation: null, // pending — { svmOnly, dtOnly, svmPlusDtDefault, svmPlusDtSfoa }
  classification: null, // pending — { accuracy, f1Macro, recallMacro, perClassRecall }
};

export const paper1 = {
  datasets: {
    total: 1215,
    noisyFraction: 0.861,
    perDataset: { ecgid: 630, cinc2011: 420, cinc2014: 105, teleecg: 60 },
  },
  split: { train: 841, test: 374, kind: "person/record-independent" },
  cleanVsNoisy: { accuracy: 0.9491978609625669, f1: 0.9712556732223904 },
  attacks: {
    fgsm: {
      0.001: { accuracy: 0.9, f1: 0.9433962264150944 },
      0.01: { accuracy: 0.8666666666666667, f1: 0.9230769230769231 },
      0.03: { accuracy: 0.7666666666666667, f1: 0.8571428571428571 },
      0.1: { accuracy: 0.7, f1: 0.8085106382978723 },
      0.3: { accuracy: 0.8333333333333334, f1: 0.9090909090909091 },
      0.5: { accuracy: 0.8333333333333334, f1: 0.9090909090909091 },
      1.0: { accuracy: 0.8333333333333334, f1: 0.9090909090909091 },
    },
    pgd: {
      0.001: { accuracy: 0.9, f1: 0.9433962264150944 },
      0.01: { accuracy: 0.8666666666666667, f1: 0.9230769230769231 },
      0.03: { accuracy: 0.5666666666666667, f1: 0.723404255319149 },
      0.1: { accuracy: 0.0, f1: 0.0 },
      0.3: { accuracy: 0.0, f1: 0.0 },
      0.5: { accuracy: 0.0, f1: 0.0 },
      1.0: { accuracy: 0.0, f1: 0.0 },
    },
    // real IBM ART attacks, max_iter/max_eval scoped down from ART's defaults to stay
    // CPU-tractable for 5 samples — see adversarial_attacks/attacks.py
    hopskipjumpArt: { 0.0: { accuracy: 0.8, f1: 0.8888888888888888, nSamples: 5 } },
    boundaryArt: { 0.0: { accuracy: 0.8, f1: 0.8888888888888888, nSamples: 5 } },
  },
  // train on 3 of 4 datasets, test on the held-out one — the paper's own protocol (§5.2)
  leaveOneDatasetOut: {
    ecgid: { accuracy: 0.8793650793650793, f1: 0.9330985915492958 },
    cinc2011: { accuracy: 0.9023809523809524, f1: 0.9461235216819974 },
    cinc2014: { accuracy: 0.9809523809523809, f1: 0.9888888888888889 },
    teleecg: { accuracy: 0.55, f1: 0.7096774193548387 },
  },
};

export const gaps = [
  {
    title: "Paper 2's HGAN-SVM-DT feature set is a documented substitute",
    body: "The paper's \"MB Assiouni method\" feature extractor was never identified from the text. The 32-feature DWT + morphological set used here is a reasonable, declared stand-in — a different, unverified feature set will not match their absolute accuracy regardless of how well SFOA or the ensemble is tuned.",
  },
  {
    title: "Paper 1's clean/noisy labels are a re-derivation, not a recovery",
    body: "The paper's own manual annotation rule for \"noisy vs. clean\" was never released. A quantitative proxy (high-frequency energy ratio) approximates their stated definition but isn't the same label rule — this caps how close the absolute numbers can get even with more and more diverse data.",
  },
  {
    title: "THECF's literal thresholds don't hold on real MIT-BIH",
    body: "Two independent measurements (Butterworth+filtfilt and raw FFT) confirmed real clean ECG has ~0.2-1.3% spectral power in the paper's stated 30-45Hz \"QRS band\", not the paper's claimed ~42%. Thresholds re-derived from our own real data (the paper's own stated mean ± 2·std method) produce a genuinely discriminative, if much lower, clean-pass-rate — reported alongside, not instead of, the literal-threshold result.",
  },
  {
    title: "The real ART black-box attacks are scoped down in query budget",
    body: "HopSkipJump/Boundary run with max_iter/max_eval well below ART's own defaults, to keep a handful of samples CPU-tractable in one sitting — a narrower query budget than the paper's own GPU-backed run, not a different algorithm.",
  },
];
