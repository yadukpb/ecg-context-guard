import {
  Activity,
  Bug,
  Gauge,
  HeartPulse,
  HelpCircle,
  Play,
  Radio,
  TrendingUp,
  Waves,
} from "lucide-react";

const GLOSSARY = [
  {
    icon: HeartPulse,
    term: "Verdict badge",
    body: "Top right of the page. The detector's current opinion on the latest reading: Genuine (green) looks like this patient's own normal heartbeat, Suspicious (yellow) is borderline, Manipulated (red) is strong evidence of tampering. \"Calibrating baseline…\" means it hasn't learned this patient's normal yet.",
  },
  {
    icon: Activity,
    term: "Live ECG window",
    body: "The actual 2-second ECG waveform currently arriving from the simulated device, refreshing automatically about every 2 seconds. Its color matches the current verdict.",
  },
  {
    icon: Gauge,
    term: "Combined detection score",
    body: "One number summarizing how abnormal the current reading is. Below 2.0 reads as genuine, 2.0–3.5 as suspicious, above 3.5 as manipulated — the colored bar beneath it shows exactly where the current score sits against those two thresholds.",
  },
  {
    icon: TrendingUp,
    term: "Detection score over time",
    body: "The same score plotted across recent windows, with the three zones shaded in the background, so you can see at a glance when (if ever) it crossed into suspicious or manipulated territory.",
  },
  {
    icon: Waves,
    term: "Heart rate / RR interval / QRS amplitude / Secondary vital tiles",
    body: "The key measurements the detector actually computes from the signal each window, shown beside this patient's own calibrated baseline so you can judge how far the current reading has drifted from their normal.",
  },
  {
    icon: Play,
    term: "Stream control",
    body: "Starts or stops the simulated live device feed for this patient, built from the real MIT-BIH ECG recording (a public, cardiologist-labeled patient dataset) assigned to them.",
  },
  {
    icon: Bug,
    term: "Attack simulation",
    body: "Lets you deliberately inject one of three kinds of signal tampering — amplitude drift, RR-interval stretch, or segment replay — at an adjustable intensity, to see whether the detector catches it.",
  },
];

const STEPS = [
  "Click Start stream. If this patient has a saved baseline, readings begin right away; otherwise the badge shows \"Calibrating baseline…\" for about 30 seconds while it learns their normal heart rate and rhythm.",
  "Once it says Genuine, watch the ECG trace and score chart for a few windows — this is the real recording, untouched.",
  "In the Attack simulation panel, pick a type and an intensity (0 is off, 1 is strongest).",
  "Click Simulate attack. Within a window or two the verdict should flip to Suspicious or Manipulated, the score should cross the marked thresholds, and a new entry should appear on the Alerts page.",
  "Click Stop attack simulation to go back to genuine readings, or Stop stream to end the session entirely — the baseline stays saved either way.",
];

export function DashboardGuide() {
  return (
    <div className="mt-8 rounded-xl border border-border bg-surface p-6 shadow-card">
      <div className="mb-4 flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-wash text-accent">
          <HelpCircle size={16} />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-ink-primary">New here? What this page shows, and how to test it</h2>
          <p className="text-xs text-ink-muted">
            Written for a first-time reader — no prior knowledge of ECGs or this project assumed.
          </p>
        </div>
      </div>

      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">What each part means</h3>
      <div className="mb-6 grid gap-3 sm:grid-cols-2">
        {GLOSSARY.map(({ icon: Icon, term, body }) => (
          <div key={term} className="flex gap-3 rounded-lg border border-border bg-page p-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent-wash text-accent">
              <Icon size={14} />
            </div>
            <div>
              <div className="text-xs font-semibold text-ink-primary">{term}</div>
              <p className="mt-0.5 text-xs leading-relaxed text-ink-secondary">{body}</p>
            </div>
          </div>
        ))}
      </div>

      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">How to test it, step by step</h3>
      <ol className="space-y-3">
        {STEPS.map((step, i) => (
          <li key={step} className="flex gap-3 text-sm text-ink-secondary">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-white">
              {i + 1}
            </span>
            <span className="leading-relaxed">{step}</span>
          </li>
        ))}
      </ol>

      <p className="mt-5 flex items-center gap-2 text-xs text-ink-muted">
        <Radio size={12} />
        For the full picture — why this approach, the detection formula, and the underlying
        code — see the Project overview page.
      </p>
    </div>
  );
}
