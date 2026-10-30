import { ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";

/**
 * Single source of truth for how a verdict is represented across the whole app
 * (badge, charts, alert rows, stat chips) — status colors from the validated
 * palette (good/warning/critical), always paired with an icon + text label,
 * never color alone.
 *
 * Colors are wrapped in rgb(var(...)) rather than a bare var(--x): the CSS
 * variables themselves are stored as "R G B" channels (so Tailwind's /NN
 * opacity modifiers work — see tailwind.config.js), which is not a valid
 * standalone CSS color on its own.
 */
export const VERDICT_META = {
  genuine: {
    label: "Genuine",
    icon: ShieldCheck,
    color: "rgb(var(--good))",
    wash: "rgb(var(--good-wash))",
  },
  suspicious: {
    label: "Suspicious",
    icon: ShieldAlert,
    color: "rgb(var(--warning))",
    wash: "rgb(var(--warning-wash))",
  },
  manipulated: {
    label: "Manipulated",
    icon: ShieldX,
    color: "rgb(var(--critical))",
    wash: "rgb(var(--critical-wash))",
  },
};

export function verdictMeta(verdict) {
  return VERDICT_META[verdict] || VERDICT_META.genuine;
}

export function scoreZone(score) {
  if (score >= 3.5) return "manipulated";
  if (score >= 2.0) return "suspicious";
  return "genuine";
}
