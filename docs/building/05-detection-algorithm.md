# 05 — Detection algorithm, in full, and its honest limitations

This is the part a review panel will actually probe, so it gets its own writeup rather than
being buried in code comments.

## Inputs to one verdict

For each post-calibration window, the detector (`app/detector.py`) computes three numbers:

1. **Baseline deviation** — weighted z-score of this window's heart rate, RR-interval mean,
   and QRS amplitude against the *patient's own* calibration-phase baseline
   (`0.4·z_hr + 0.3·z_rr + 0.3·z_amp`).
2. **Sudden change** — the same weighted z-score, but against the patient's own last 10
   windows rather than their long-run baseline. This is what catches an attack that hasn't
   yet pulled the patient outside their *historical* normal range but represents an abrupt,
   physiologically implausible jump within the current session.
3. **Cross-sensor score** — z-score of the disagreement between the ECG-derived heart rate
   and the independent secondary-vital reading. The noise floor used depends on whether that
   reading is real or synthetic (see "Honest limitations" below): 2 bpm for the synthetic
   stand-in, 5 bpm for a real independent PPG sensor, which genuinely disagrees more.

These combine as:

```
temporal_score  = 0.4 · baseline_deviation + 0.6 · sudden_change
combined_score  = 0.6 · temporal_score + 0.4 · cross_sensor_score

verdict = manipulated  if combined_score >= 3.5
          suspicious   if combined_score >= 2.0
          genuine      otherwise
```

Sudden change is weighted higher than long-run baseline deviation deliberately: a patient's
rhythm drifting slowly over many real sessions is normal (exercise, medication, time of
day); an abrupt jump within one streaming session, with no corresponding real-world event,
is the signature an injected attack leaves.

## Why not ML/DL

The slides' own Scope slide defers "ML/DL-based detection methods" to a future extension.
This semester's detector is an inspectable, documented weighted-threshold scheme instead —
every number above is visible and arguably defensible in front of a panel, which matters
more at this stage than squeezing out marginal accuracy with a model that would also need
its own training-data and evaluation story.

## Honest limitations (say these before a reviewer asks)

- **Real cross-sensor data exists for some patients, not others — and this is disclosed per
  patient, not glossed over.** MIT-BIH only has ECG channels, so patients backed by a
  MIT-BIH record still use a synthetically generated secondary vital
  (`app/cross_sensor.py`) that tracks the *true, pre-attack* heart rate plus its own
  independent slow drift and noise — a genuine check in the sense that an attacker who only
  touches the ECG channel can't retroactively alter it, but still synthetic data, not a real
  sensor stream. Patients backed by a **BIDMC** record instead get a real, independently
  measured secondary vital: BIDMC (also on PhysioNet) contains concurrent ECG *and* PPG
  (pulse-oximeter) recordings from the same patient on the same timebase, and the detector
  peak-detects the actual PPG channel (`app/signal_proc.extract_ppg_hr`) rather than
  simulating a reading. The dashboard labels each patient's secondary-HR tile "real PPG
  sensor" or "synthetic stand-in" accordingly, and `/records` tags every offered record with
  which kind it is.

  Getting the real path working against actual noisy clinical data surfaced two things worth
  stating plainly: (1) real PPG occasionally misdetects a beat (dicrotic-notch
  double-counting, missed beats from poor perfusion) badly enough to swing the computed rate
  by tens of bpm in a single 2-second window — fixed with a continuity check against the
  patient's last accepted reading, a minimum-peaks confidence bar, and a wider expected-noise
  tolerance (5 bpm vs. the synthetic path's 2 bpm) that still leaves real attacks (an 18-20
  bpm shift, sustained) clearly distinguishable from sensor noise; (2) five of the first
  twenty BIDMC records tested still occasionally cross the "suspicious"/"manipulated"
  threshold on clean, unattacked data because of genuine sensor/short-window noise in those
  specific recordings — handled by curating the five offered demo records (`bidmc:05`-`09`)
  by actually stress-testing each one against ~100 genuine windows rather than by further
  loosening the detector's thresholds. See `docs/mistakes-log.md` for the full investigation.
- **Thresholds (2.0 / 3.5) are reasoned defaults, not fit to labeled attack data.** They were
  chosen so that normal variation in real MIT-BIH windows reads comfortably under 2.0 (see
  `docs/figures/detection_timeline.png`: all pre-attack points sit under 1.0) and an injected
  attack clears 3.5 within one window (same figure: the score jumps from ~0.4 to ~3.8 the
  instant the attack switches on). They have not been tuned against a large labeled attack
  dataset, which would be natural next-semester work.
- **Attack intensity matters.** A subtle attack at low intensity may legitimately score as
  `genuine` for a window or two — observed live: `amplitude_drift` at intensity 0.7 did not
  trip the detector in one manual test run, while `rr_stretch` at the same intensity did
  within one window. This is a real property of the detector (amplitude drift genuinely
  produces a smaller z-score shift than a timing attack at comparable intensity), not a bug,
  and is worth stating plainly rather than tuning thresholds down until every attack trips
  on window one regardless of real-world false-positive cost.
- **Single-channel MIT-BIH only.** No motion artifact modeling, no multi-lead voting, no
  patient-reported context (e.g. "I was exercising"). All reasonable Semester-2 extensions.
