/**
 * Meter / progress-track component (dataviz skill, Tier 1): fill carries severity,
 * the unfilled track is a lighter step of the accent ramp so state reads across the
 * whole bar. Threshold ticks are text-labeled, never color-only.
 */
const MAX = 6;
const THRESHOLDS = [
  { value: 2.0, label: "Suspicious" },
  { value: 3.5, label: "Manipulated" },
];

export function ScoreMeter({ score = 0 }) {
  const pct = Math.min(1, Math.max(0, score / MAX)) * 100;
  const zoneColor =
    score >= 3.5 ? "rgb(var(--critical))" : score >= 2.0 ? "rgb(var(--warning))" : "rgb(var(--good))";

  return (
    <div>
      <div
        className="relative h-3 w-full overflow-hidden rounded-full"
        style={{ background: "rgb(var(--accent-wash))" }}
      >
        <div
          className="h-3 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, background: zoneColor }}
        />
        {THRESHOLDS.map((t) => (
          <div
            key={t.value}
            className="absolute top-0 h-3 w-px bg-ink-primary/20"
            style={{ left: `${(t.value / MAX) * 100}%` }}
          />
        ))}
      </div>
      <div className="relative mt-1.5 h-4">
        {THRESHOLDS.map((t) => (
          <span
            key={t.value}
            className="absolute -translate-x-1/2 text-[10px] font-medium text-ink-muted"
            style={{ left: `${(t.value / MAX) * 100}%` }}
          >
            {t.label} ≥{t.value}
          </span>
        ))}
      </div>
    </div>
  );
}
