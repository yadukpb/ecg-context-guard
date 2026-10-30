# 00 — Overview

## What this is

A working prototype for the Review-1 project *"Context-Aware Detection of Semantic Data
Manipulation Attacks in Remote ECG-Based Cardiac Patient Monitoring Systems"*. The slides
(`/home/yadu/Downloads/01.Review 1 ppt.pdf`) propose detecting ECG tampering that stays
"clinically plausible" — i.e. doesn't trip a naive out-of-range alarm — by checking a
patient's data against their own historical baseline, its temporal behavior, and consistency
with a second vital-sign channel, instead of a single global threshold.

This repo turns that proposal into something that actually runs: real MIT-BIH ECG records
replayed as a simulated live device stream, through preprocessing, a simulated secure
transmission channel, patient-specific baseline modeling, an attack simulator that injects
exactly the kind of "plausible" manipulation the slides describe, and a detector that scores
each incoming window as `genuine` / `suspicious` / `manipulated`, surfaced on a dashboard.

## Why this stack

Matches the conventions of two of the user's existing full-stack projects
(`adhd-screener`, `job-portal`):

- **Express + Mongoose + React/Vite/Tailwind/Recharts**, JWT-in-cookie auth, Mongo via a
  minimal `docker-compose.yml` — same shape as `adhd-screener`.
- **One isolated Python service for the one step that needs real scientific-computing
  libraries** (MIT-BIH decoding via `wfdb`, filtering/peak-detection via `scipy`) — same idea
  as `job-portal` isolating its one LLM-dependent step into its own service file, rather than
  forcing everything into Node.

## Repo layout

```
apps/web/        React dashboard
apps/api/        Express API — auth, patients, ingest, alerts, control passthrough
services/detector/  Python FastAPI — signal processing, baseline, attack sim, detection
docker-compose.yml  Mongo only
docs/building/   This documentation trail, one numbered file per step
docs/mistakes-log.md  Append-only log of things that broke and how they were fixed
docs/figures/    Static PNG plots for the written report / next review
data/mitdb/      Local cache of downloaded MIT-BIH records (gitignored)
```

## Reading order for this docs/building/ series

1. `00-overview.md` — this file
2. `01-architecture.md` — how the three services talk to each other, and the full data flow
3. `02-detector-service.md` — the Python signal-processing/detection service in detail
4. `03-backend-api.md` — Express models, routes, auth, the ingest/decrypt path
5. `04-frontend.md` — the React dashboard
6. `05-detection-algorithm.md` — exactly how the genuine/suspicious/manipulated verdict is
   computed, and the honest limitations of the approach
7. `06-running-the-app.md` — how to actually start everything and drive a live demo

Known limitation, stated up front (also noted when reviewing the original slides): MIT-BIH
has no second vital-sign channel, so "cross-sensor" analysis uses a synthetically generated
correlated vital standing in for e.g. a pulse oximeter. This is disclosed, not hidden — see
`05-detection-algorithm.md` for how it's generated and why that's still a meaningful check.
