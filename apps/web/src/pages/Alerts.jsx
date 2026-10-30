import { useState } from "react";
import { Link } from "react-router-dom";
import { Bell, Check, ShieldOff } from "lucide-react";
import { usePolling } from "../hooks/usePolling";
import { api } from "../api/client";
import { VerdictBadge } from "../components/VerdictBadge";

const TABS = [
  { value: "all", label: "All" },
  { value: "suspicious", label: "Suspicious" },
  { value: "manipulated", label: "Manipulated" },
];

export function Alerts() {
  const [tab, setTab] = useState("all");
  const { data, error } = usePolling(() => api.listAlerts(100), 3000, true, []);
  const alerts = (data?.alerts || []).filter((a) => tab === "all" || a.verdict === tab);

  async function acknowledge(alertId) {
    await api.acknowledgeAlert(alertId);
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-wash text-accent">
          <Bell size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Security alerts</h1>
          <p className="text-sm text-ink-muted">Every window a patient's stream scored above genuine.</p>
        </div>
      </div>

      <div className="mb-4 flex gap-1 rounded-lg border border-border bg-surface p-1 w-fit">
        {TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
              tab === t.value ? "bg-accent-wash text-accent" : "text-ink-muted hover:text-ink-primary"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <p className="mb-4 text-sm text-critical">{error.message}</p>}

      <div className="space-y-2">
        {alerts.map((a) => (
          <div
            key={a._id}
            className={`flex items-center justify-between rounded-xl border border-border bg-surface p-4 shadow-card transition ${
              a.acknowledged ? "opacity-50" : ""
            }`}
          >
            <div className="min-w-0">
              <Link to={`/patients/${a.patient?._id}`} className="font-semibold text-ink-primary hover:text-accent">
                {a.patient?.name || "Unknown patient"}
              </Link>
              <div className="mt-0.5 font-mono-figures text-xs text-ink-muted">
                score {a.combinedScore.toFixed(2)} · {new Date(a.createdAt).toLocaleString()}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <VerdictBadge verdict={a.verdict} />
              {!a.acknowledged && (
                <button
                  onClick={() => acknowledge(a._id)}
                  className="flex items-center gap-1 rounded-lg border border-border px-2.5 py-1.5 text-xs font-medium text-ink-secondary hover:bg-accent-wash/60"
                >
                  <Check size={12} /> Acknowledge
                </button>
              )}
            </div>
          </div>
        ))}
        {alerts.length === 0 && (
          <div className="rounded-xl border border-dashed border-border p-10 text-center text-sm text-ink-muted">
            <ShieldOff className="mx-auto mb-2 text-ink-muted" size={24} />
            No alerts in this view.
          </div>
        )}
      </div>
    </div>
  );
}
