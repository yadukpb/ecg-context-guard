# 04 — Frontend (`apps/web`)

React + Vite + Tailwind + Recharts, same stack shape as the user's `adhd-screener` project
(light/dark theme via a `useTheme` hook backed by `localStorage`, JWT-cookie auth via
`credentials: "include"` on every fetch).

## Pages

- `Login` — login/register toggle, shows the seeded demo credentials inline so a reviewer
  doesn't need to dig through docs to log in
- `PatientList` — list + create-patient form (name, cardiac history, MIT-BIH record picker
  populated from `GET /api/patients/meta/records`, which just proxies the detector's
  `/records` list)
- `PatientDashboard` — the main view: start/stop stream, attack type + intensity + toggle,
  verdict badge, live ECG chart (color-coded by verdict), baseline-vs-current stat cards,
  detection-score timeline
- `Alerts` — cross-patient alert feed with acknowledge

## Live updates: polling, not websockets

`usePolling()` (`src/hooks/usePolling.js`) polls `GET /api/patients/:id/latest` every 2s and
`GET /api/patients/:id/history` every 4s. This is a deliberate v1 simplification over
websockets/SSE — simpler to build and completely sufficient at a 2s device-window cadence.
Noted as a stretch goal in `01-architecture.md`.

## Verified manually in-browser (2026-10-29)

Logged in as the seeded demo user, opened the demo patient, started the stream — it picked
up the already-persisted baseline instead of recalibrating (confirms the
Express-persists/detector-asks-on-start baseline design works across restarts). Toggled the
amplitude-drift attack at intensity 0.7: verdict stayed `genuine` — a real, legitimate result
showing that attack type is comparatively subtle at that intensity, not a bug. Switched to
RR-interval stretch at the same intensity: verdict flipped to `suspicious` within one window,
heart rate read 64bpm against a 74bpm baseline, RR interval read 0.94s against a 0.81s
baseline — exactly the mechanism `attack.py`'s `rr_stretch` is supposed to produce. The
Alerts page showed the resulting alerts in real time with working Acknowledge buttons.

## UI v2 — redesigned for presenting to a review panel

After the initial build, the whole frontend was redesigned for visual polish and to add a
fifth page the first three didn't have: an in-depth project explainer.

- **Design tokens** (`src/index.css` + `tailwind.config.js`): adopted the dataviz skill's
  validated reference palette — fixed, mode-invariant `good`/`warning`/`critical` status
  colors (always paired with an icon + label, never color alone) for the three verdicts,
  plus light/dark surface, ink, and accent tokens as CSS custom properties. `Inter` +
  `JetBrains Mono` via Google Fonts.
- **Layout**: a left `Sidebar` (collapsible to a top bar + slide-over on mobile) replaced the
  old top navbar, with a new nav item for the project-overview page.
- **New page — `ProjectOverview`** (now the post-login landing page at `/`): the "what are we
  trying to do, in depth" page requested for panel presentations. Covers the problem
  statement, research gap, aim, a system architecture diagram (plain CSS grid + lucide
  arrows, not an image), the full 9-step workflow as a stepper, the detection algorithm's
  exact formula and weights, the three attack types with the real `waveform_comparison.png`
  embedded, a "live evidence" section embedding `detection_timeline.png` plus the actual
  numbers from a live test run, dataset facts, tech stack, honest limitations, and the
  semester roadmap. Figures are copied into `apps/web/public/figures/` from
  `docs/figures/` (regenerate both from the same source:
  `services/detector/scripts/generate_report_figures.py`, then re-copy).
- **Charts**: rebuilt `EcgChart` and `ScoreTimeline` per the dataviz skill's mark specs —
  thin 2px lines, a soft area wash under the ECG line, and labeled background zones
  (genuine/suspicious/manipulated) on the score timeline instead of coloring individual
  points, so a single series never needs a legend.
- **New components**: `Card`, `StatTile`, `ScoreMeter` (a labeled threshold meter for the
  combined score), and a redesigned `VerdictBadge` (icon + label + pulse animation on
  `manipulated`) — see `src/lib/verdict.js` for the single source of truth each of these
  reads from.

A real bug surfaced during this redesign and is logged in `docs/mistakes-log.md`: new
Tailwind color tokens silently stopped generating mid-session (stale PostCSS watcher state),
making native form inputs render with the browser's default white background instead of the
theme. Fixed by restarting the Vite dev server; verified by checking the served CSS directly
rather than trusting how the page looked.

## UI v3 — code walkthrough + demo walkthrough on the Overview page

Added two more sections to `ProjectOverview`, both inserted into the existing TOC:

- **Code walkthrough** (`#code`, after Detection algorithm) — six verbatim excerpts from the
  actual source (`signal_proc.py`, `baseline.py`, `attack.py`, `detector.py`,
  `crypto_channel.py`, and `cryptoChannel.js`), each rendered with real syntax highlighting
  via the new `CodeBlock` component (`prism-react-renderer`, `themes.nightOwl`, always
  dark regardless of the page's own light/dark toggle — a deliberate "code editor" look) and
  followed by a plain-English explanation of what the snippet is actually doing and why.
  `CODE_SNIPPETS` in `ProjectOverview.jsx` is the single array driving it — keep it in sync
  by hand if the underlying functions change, it's copied text, not auto-extracted.
- **How to run this demo** (`#howto`, after Attack simulation) — an 8-step card grid covering
  the literal click-path a reviewer (or a viewer with no code context at all) can follow in
  the running app: log in, open a patient, start the stream, watch it read genuine, pick an
  attack, trigger it, check the Alerts page, stop the stream.

## UI v4 — plain-language pass + a guide on the dashboard itself

Two follow-up changes, both direct feedback:

- Reworded several section intros/eyebrows that leaned on "this is not X, it's Y" phrasing
  (`#code`'s old eyebrow "Not pseudo-code", `#evidence`'s old "Not just a diagram — it runs",
  and a few sentences like "nothing here is simplified for the slide") into plain, direct
  statements instead. Also expanded the `#dataset` section with a "What is MIT-BIH?"
  paragraph explaining what the database actually is for a reader with no prior context, and
  added a pointer to it from the workflow's first step.
- Added `src/components/DashboardGuide.jsx`, rendered at the very bottom of
  `PatientDashboard` only (every other page and the rest of that page is untouched) — a
  glossary of every element on the page (verdict badge, ECG window, score meter, score
  timeline, stat tiles, stream control, attack simulation) plus a short numbered "how to test
  it" sequence, written for someone with zero prior context on ECGs or this project.
