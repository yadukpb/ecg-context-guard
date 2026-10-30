import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function EcgChart({ waveform, color = "rgb(var(--accent))" }) {
  if (!waveform || waveform.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-ink-muted">
        No waveform yet — start the stream to begin reading.
      </div>
    );
  }

  const data = waveform.map((v, i) => ({ sample: i, value: v }));

  return (
    <ResponsiveContainer width="100%" height={224}>
      <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="ecgFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.12} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="sample" tick={false} axisLine={{ stroke: "rgb(var(--gridline))" }} tickLine={false} />
        <YAxis
          tick={{ fontSize: 10, fill: "rgb(var(--ink-muted))" }}
          tickFormatter={(v) => v.toFixed(1)}
          width={50}
          axisLine={{ stroke: "rgb(var(--gridline))" }}
          tickLine={false}
        />
        <Tooltip
          formatter={(value) => [value.toFixed(3), "mV"]}
          labelFormatter={() => ""}
          contentStyle={{
            fontSize: 12,
            background: "rgb(var(--surface-raised))",
            border: "1px solid var(--border)",
            borderRadius: 8,
          }}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill="url(#ecgFill)"
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
