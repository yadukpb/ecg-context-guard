/**
 * Stat tile (dataviz skill, Tier 1 figure contract): label + value + optional
 * baseline delta. Delta stays in neutral ink, never a status color — a reading
 * being above or below baseline isn't inherently "good" or "bad" on its own.
 */
export function StatTile({ icon: Icon, label, value, unit, baseline, caption }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-card">
      <div className="mb-2 flex items-center gap-1.5 text-ink-muted">
        {Icon && <Icon size={13} />}
        <span className="text-[11px] font-semibold uppercase tracking-wide">{label}</span>
      </div>
      <div className="font-mono-figures text-2xl font-bold text-ink-primary">
        {value}
        {unit && <span className="ml-1 text-sm font-medium text-ink-secondary">{unit}</span>}
      </div>
      <div className="mt-1 text-xs text-ink-muted">{baseline != null ? `baseline ${baseline}` : caption != null ? caption : " "}</div>
    </div>
  );
}
