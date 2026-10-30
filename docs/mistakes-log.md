# Mistakes log

Append-only. Each entry: what broke, what the actual cause was, what fixed it. Newest at the
bottom.

---

### `pip install -r requirements.txt` failed downloading scipy

**What broke:** `./venv/bin/pip install -r requirements.txt` failed with
`incomplete-download` on the scipy wheel after 6 retry attempts, each failing DNS resolution
for `files.pythonhosted.org` partway through.

**Cause:** Transient network interruption on this machine during the ~39MB scipy wheel
download, not a problem with the requirements themselves.

**Fix:** Re-ran the same `pip install -r requirements.txt` command; pip resumes partial
downloads by default so the retry didn't restart from zero.

---

### `wfdb.dl_record` doesn't exist

**What broke:** `pytest` failed every test with
`AttributeError: module 'wfdb' has no attribute 'dl_record'. Did you mean: 'rdrecord'?` —
the original `app/mitdb.py` was written assuming a `wfdb.dl_record(name, pn_dir=..., dl_dir=...)`
helper for downloading one record to a local cache directory, based on memory of the wfdb
API rather than the actually-installed version (wfdb 4.1.2).

**Cause:** That function name doesn't exist in this version of the package (confirmed via
`dir(wfdb)`: only `dl_database` and `dl_files` exist for bulk/explicit-file downloads).

**Fix:** Switched to `wfdb.rdrecord(record_name, pn_dir="mitdb")`, which streams the record
directly from PhysioNet without needing a separate download step, and dropped the on-disk
cache directory (`data/mitdb/`) in favor of an in-memory cache keyed by record name — each
record is now fetched once per detector-service process instead of once ever, which is a
fine tradeoff for a prototype replaying a handful of demo patients.

---

### "Simulate attack" button effectively invisible (and every `/NN` opacity modifier on a custom color was silently broken)

**What broke:** The user reported the Simulate attack button looked hidden. It wasn't
hidden — it rendered with near-white text on a near-white background, in both light and
dark mode, because its class was `bg-ink-primary/80`. The same root cause silently affected
every other custom-color opacity modifier in the app (`border-accent/40`, `bg-accent-wash/60`,
`border-good/30`, `border-critical/30`, `border-warning/30`, `hover:bg-critical/90`): borders
and hover tints that should have been faint were just missing.

**Cause:** `src/index.css` defined each design-token CSS variable as a hex string (e.g.
`--accent: #2a78d6;`), and `tailwind.config.js` mapped `colors.accent` straight to
`"var(--accent)"`. Tailwind's `/NN` opacity-modifier syntax needs to inject an alpha channel
into the color value at generation time — it does this by emitting `rgb(var(--x) / NN%)`,
which requires `--x` to already be bare `R G B` channel numbers, not a hex string or a
pre-built `var(...)` reference. With a hex variable, that emitted CSS is invalid, so the
browser drops the whole declaration and the element falls back to no background/border at
all — which looked like "the button is see-through" rather than an obvious error anywhere.

**Fix:** Two parts. (1) Converted every token in `index.css` to space-separated `R G B`
channels and added a `withOpacity(variable)` helper in `tailwind.config.js` that emits
`rgb(var(--x) / <alpha>)` — the documented Tailwind pattern for CSS-variable theming with
opacity support. (2) That alone broke every place in JS/inline-styles that referenced
`var(--x)` directly as a complete color (`lib/verdict.js`, `ScoreMeter.jsx`, `EcgChart.jsx`,
`ScoreTimeline.jsx`) since a bare channel string isn't a valid standalone color either —
wrapped each as `rgb(var(--x))`. Also separately replaced the button's own
`bg-ink-primary/80`/`hover:bg-ink-primary` with a fixed `bg-slate-700 hover:bg-slate-600`:
`ink-primary` is a token that deliberately flips between near-black (light mode) and
near-white (dark mode) for *text*, so using it as a button *background* would have stayed
broken in dark mode even after the opacity fix (white text on a near-white button).
Re-verified every chart, badge, and button in both themes afterward rather than just the
one reported button, since the bug class could have been anywhere `/NN` was used.

---

### Mongo port 27017 already taken

**What broke:** `docker compose up -d` failed: `Bind for 0.0.0.0:27017 failed: port is
already allocated`.

**Cause:** The user's other project, `adhd-screener`, already runs its own Mongo container
bound to host port 27017.

**Fix:** Remapped this project's compose file to `27018:27017` (host:container) and updated
`MONGO_URI` in `apps/api/.env.example` and its default in `src/config/env.js` to match.
These two projects can now run their own Mongo containers side by side.

---

### `RuntimeError: no running event loop` on `/stream/start`

**What broke:** `POST /stream/start` returned 500 with
`RuntimeError: no running event loop` from inside `asyncio.create_task(...)`.

**Cause:** FastAPI runs plain `def` endpoint functions in a worker thread pool, not on the
event loop — fine for normal request handling, but `asyncio.create_task()` requires a
running loop on the *calling* thread, which a worker thread doesn't have.

**Fix:** Changed `stream_start` in `app/main.py` to `async def`. An async endpoint runs
directly on the event loop, so `create_task()` inside `streamer.start_stream()` works.

---

### New Tailwind color tokens silently stopped generating

**What broke:** After the UI redesign added custom color tokens to `tailwind.config.js`
(`surface`, `ink.primary`, `accent`, `good`/`warning`/`critical`, etc.), several pages —
checked via `document.styleSheets` in the browser — had **zero** CSS rules for classes like
`.bg-surface` or `.text-ink-primary`. Native inputs/selects rendered with the browser's
default white background instead of the themed one; divs looked "accidentally" correct only
because they inherited the dark page background from `body`.

**Cause:** The long-running `vite` dev server's PostCSS/Tailwind watcher got into a stale
state after several rapid `tailwind.config.js` and dependency edits (including installing
`lucide-react` mid-session) and stopped regenerating utilities for the new color tokens,
without printing any error.

**Fix:** Killed and restarted the `npm run dev:web` process. Confirmed with
`curl http://localhost:5173/src/index.css | grep bg-surface` before and after — 0 matches,
then 1. If new Tailwind theme colors ever don't seem to apply, restart the dev server and
check the served CSS directly before assuming the component code is wrong.

---

### Cross-sensor check was fully synthetic — replaced with a real one, which then needed its own fixes

**What broke:** Nothing was "broken" — a user review flagged that the "Cross-Sensor Analysis"
step claimed in the slides' own workflow was, in this build, entirely synthetic: MIT-BIH has
no second vital-sign channel, so `app/cross_sensor.py` generated a fake secondary HR
mathematically derived from the same ECG-computed heart rate. That's disclosed as a
limitation, but it meant the "independent sensor" could never actually disagree with the ECG
in a way that reflected anything real.

**Fix, part 1 — get a real second sensor.** BIDMC (PhysioNet's "PPG and Respiration
Database") has real, concurrent ECG *and* PPG recordings from the same patient on the same
timebase — confirmed via `wfdb.rdrecord("bidmc01", pn_dir="bidmc")`. Added `app/bidmc.py`
(same `rdrecord`-with-in-memory-cache pattern as `mitdb.py`, with one quirk: BIDMC's own
channel labels carry a trailing comma, e.g. `"II,"` not `"II"`) and
`signal_proc.extract_ppg_hr` (peak-detect the PPG waveform, same Pan-Tompkins-adjacent
approach as the ECG side but tuned to PPG's slower, broader pulse shape). Patients backed by
a `bidmc:NN` record now get this real reading instead of the synthetic one; MIT-BIH-backed
patients are unchanged. Verified first with a standalone script against real data before
wiring anything into the streamer (`extract_ppg_hr` tracked the ECG-derived HR within
~0.6-2bpm on clean windows) — this is the same lesson as the `wfdb.dl_record` mistake above:
check the actual data/API before building on assumptions about it.

**Fix, part 2 — the real sensor surfaced real noise, which then produced false positives.**
Stress-testing the first five BIDMC records (01-05) against sustained genuine (unattacked)
replay found occasional spurious "manipulated" verdicts — a problem the synthetic path could
never have, since it's mathematically incapable of strongly disagreeing with the ECG. Root
causes, found by tracing specific flagged windows rather than guessing:
  1. A PPG window with only 2 detected peaks (1 interval) sometimes halved/doubled the
     computed rate if a beat was missed or a dicrotic notch double-counted. Fixed by
     requiring 3+ peaks, using the median interval instead of the mean, and rejecting
     implausible results (`signal_proc.extract_ppg_hr`).
  2. Isolated sensor artifacts (e.g. one window reporting 176bpm against a patient steady at
     ~88bpm — a doubled dicrotic notch) still slipped through the above. Fixed with a
     continuity check in the streamer: a reading that jumps >20bpm from this same patient's
     last accepted reading is rejected (`streamer._real_secondary_hr`).
  3. Even with (1) and (2), a genuinely independent two-sensor comparison over a short
     2-second window naturally disagrees more than the synthetic path's tight,
     mathematically-derived noise — scoring real sensor noise against the synthetic path's
     2bpm expected-std routinely false-flagged clean data. Gave the real path its own, wider
     expected-std (5bpm) in `detector.py`. Confirmed this doesn't blind the detector to real
     attacks: an attack shifts ECG-derived HR by ~18-20bpm while the untouched real PPG
     channel stays at the true rate, so attacks remain far above the new, wider noise floor
     (new test: `test_attack_on_bidmc_ecg_is_still_flagged_despite_wider_real_sensor_tolerance`).
  4. A first attempt — zeroing the cross-sensor score whenever the ECG side had fewer than 3
     beats in its own window, by the same logic as fix 1 — looked right but broke real attack
     detection: the `rr_stretch` attack itself legitimately *reduces* the apparent beat count
     by time-warping the window, so this gate silently defeated detection of exactly that
     attack on BIDMC's lower sample rate (confirmed by a failing test before this was
     caught — `test_attack_on_bidmc_ecg_is_still_flagged...` went from failing-as-expected to
     a different, wrong kind of failing). Reverted; the beat-count fragility is a property of
     short low-sample-rate windows in general (visible on the ECG side too, not just PPG),
     better handled by which records get offered as demo patients than by a blanket
     detector-logic gate that can't tell "sensor glitch" from "attack symptom" apart.
  5. After (1)-(3), stress-tested a wider pool of 20 BIDMC records (~100 genuine windows
     each, ~3.3 minutes per record) rather than patching further — records 01-04, 10, and 17
     still occasionally crossed the manipulated/suspicious threshold on clean data (real,
     patient-specific sensor/rhythm noise, not a bug), while 05-09, among others, stayed
     comfortably under both thresholds throughout. Swapped the five offered demo records from
     01-05 to 05-09 rather than keep loosening the detector to accommodate the noisiest ones.

**Lesson:** the synthetic stand-in wasn't just "less realistic" than a real sensor — it was
silently *masking* the whole class of real-world noise and edge cases a genuine second sensor
actually has. Building the real path immediately surfaced work (steps 1-5 above) that the
synthetic path's existence had made invisible. Both paths now co-exist, each clearly labeled
in the UI and `/records` response, rather than quietly replacing one disclosed limitation
with an undisclosed new one.

---
