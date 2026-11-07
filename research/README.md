# ECG research reproductions (Paper 1 & Paper 2)

Independent reproductions of the two uploaded research papers, per
`FEASIBILITY_REPORT.md` and the approved implementation plan. Kept separate from the
Node/React `ecg-context-guard` app — same Python-isolation convention as
`services/detector` (own venv, own `requirements.txt`).

- **Paper 1** (`Paper_1_Attack_Independent_Defence/`) — ResNet-18(1D) clean/noisy ECG
  gatekeeper, trained without adversarial examples, evaluated against FGSM/PGD (true
  white-box) and a simplified boundary-walk stand-in for HopSkipJump/Boundary (see
  `adversarial_attacks/attacks.py` docstring for exactly why it's a stand-in, not IBM ART).
  Scoped to ECG-ID + NSTDB-derived synthetic noise for this pass.
- **Paper 2** (`Paper_2_Layered_MIOT_Framework/`) — THECF fault screening -> HGAN-SVM-DT
  (SFOA-tuned) anomaly detection -> differential-image CNN arrhythmia classification, on
  MIT-BIH.
- **Common/** — shared venv, dataset loaders (`wfdb.rdrecord(..., pn_dir=...)`, same pattern
  as `services/detector/app/mitdb.py`), and the SFOA optimizer both papers' pipelines use.

## Run it

```bash
cd research
Common/venv/bin/python -m Paper_2_Layered_MIOT_Framework.main
Common/venv/bin/python -m Paper_1_Attack_Independent_Defence.main
Common/venv/bin/pytest
```

Each `main.py` prints its metrics and writes them to `<paper>/evaluation/results.json`.
Every number in `COMPARISON_REPORT.md` traces back to one of those two files — see
`FEASIBILITY_REPORT.md` for what's scoped down vs. the papers' full-scale config, and why.
