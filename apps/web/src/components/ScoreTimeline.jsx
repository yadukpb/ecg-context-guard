import {
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { verdictMeta } from "../lib/verdict";

const MAX = 6;

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  const meta = verdictMeta(point.verdict);
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs"
      style={{ background: "rgb(var(--surface-raised))", borderColor: "var(--border)" }}
    >
      <div className="font-semibold" style={{ color: meta.color }}>
        {meta.label}
      </div>
      <div className="text-ink-muted">score {point.score.toFixed(2)}</div>
    </div>
  );
}

export function ScoreTimeline({ segments }) {
  const data = (segments || [])
    .filter((s) => s.detection)
    .map((s, i) => ({ index: i, score: s.detection.combined_score, verdict: s.detection.verdict }));

  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-ink-muted">
        No detection history yet — scores appear once calibration finishes.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={208}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
        <ReferenceArea y1={0} y2={2.0} fill="rgb(var(--good))" fillOpacity={0.06} />
        <ReferenceArea
          y1={2.0}
          y2={3.5}
          fill="rgb(var(--warning))"
          fillOpacity={0.08}
          label={{ value: "Suspicious", position: "insideTopRight", fontSize: 10, fill: "rgb(var(--ink-muted))" }}
        />
        <ReferenceArea
          y1={3.5}
          y2={MAX}
          fill="rgb(var(--critical))"
          fillOpacity={0.08}
          label={{ value: "Manipulated", position: "insideTopRight", fontSize: 10, fill: "rgb(var(--ink-muted))" }}
        />
        <XAxis dataKey="index" tick={false} axisLine={{ stroke: "rgb(var(--gridline))" }} tickLine={false} />
        <YAxis
          domain={[0, MAX]}
          tick={{ fontSize: 10, fill: "rgb(var(--ink-muted))" }}
          tickFormatter={(v) => v.toFixed(0)}
          width={28}
          axisLine={{ stroke: "rgb(var(--gridline))" }}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="score"
          stroke="rgb(var(--accent))"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 5, stroke: "rgb(var(--surface))", strokeWidth: 2 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
