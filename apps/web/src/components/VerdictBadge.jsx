import { Loader2 } from "lucide-react";
import { verdictMeta } from "../lib/verdict";

export function VerdictBadge({ verdict, calibrating, size = "md" }) {
  if (calibrating) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1.5 text-sm font-medium text-ink-secondary">
        <Loader2 size={14} className="animate-spin" />
        Calibrating baseline…
      </span>
    );
  }

  const meta = verdictMeta(verdict);
  const Icon = meta.icon;
  const isLg = size === "lg";
  const pulse = verdict === "manipulated" ? "animate-pulse" : "";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold ${
        isLg ? "px-4 py-2 text-base" : "px-3 py-1.5 text-sm"
      } ${pulse}`}
      style={{ color: meta.color, backgroundColor: meta.wash }}
    >
      <Icon size={isLg ? 18 : 14} />
      {meta.label}
    </span>
  );
}
