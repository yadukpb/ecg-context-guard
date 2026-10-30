import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, HeartPulse, Lock, ShieldCheck, Waves } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const HIGHLIGHTS = [
  {
    icon: Waves,
    title: "Real ECG, replayed live",
    body: "Streams genuine MIT-BIH Arrhythmia Database recordings window-by-window, simulating a live IoMT cardiac monitor.",
  },
  {
    icon: ShieldCheck,
    title: "Patient-specific baselines",
    body: "Learns each patient's own normal heart rate, rhythm and QRS amplitude instead of one global threshold.",
  },
  {
    icon: Activity,
    title: "Catches plausible manipulation",
    body: "Detects attacks engineered to stay within clinically normal ranges — the kind naive anomaly detectors miss.",
  },
];

export function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(form.email, form.password);
      } else {
        await register(form.email, form.password, form.name);
      }
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-page lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-[#0d2a4f] via-[#123a63] to-[#1c5cab] p-12 text-white lg:flex">
        <div className="pointer-events-none absolute inset-0 opacity-20">
          <svg viewBox="0 0 400 400" className="h-full w-full">
            <path
              d="M0,200 L60,200 L80,120 L105,280 L130,60 L155,200 L400,200"
              fill="none"
              stroke="white"
              strokeWidth="2"
            />
          </svg>
        </div>

        <div className="relative">
          <div className="mb-8 flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/15 backdrop-blur">
              <HeartPulse size={20} />
            </div>
            <span className="text-lg font-bold">ECG Context Guard</span>
          </div>
          <h1 className="mb-4 max-w-md text-3xl font-extrabold leading-tight">
            Context-aware detection of semantic data manipulation in remote cardiac monitoring
          </h1>
          <p className="max-w-md text-sm text-blue-100">
            A working prototype for the M.Tech review project — detecting ECG tampering
            engineered to look clinically normal, using patient-specific context instead of
            blunt thresholds.
          </p>
        </div>

        <div className="relative space-y-5">
          {HIGHLIGHTS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/15">
                <Icon size={16} />
              </div>
              <div>
                <div className="text-sm font-semibold">{title}</div>
                <div className="text-xs text-blue-100">{body}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-white">
              <HeartPulse size={20} />
            </div>
            <span className="text-lg font-bold text-ink-primary">ECG Context Guard</span>
          </div>

          <h2 className="mb-1 text-2xl font-bold text-ink-primary">
            {mode === "login" ? "Welcome back" : "Create an account"}
          </h2>
          <p className="mb-6 text-sm text-ink-muted">
            {mode === "login" ? "Sign in to your clinician account" : "Set up a clinician account"}
          </p>

          <div className="mb-5 flex items-start gap-2 rounded-lg border border-border bg-accent-wash px-3 py-2.5 text-xs text-ink-secondary">
            <Lock size={14} className="mt-0.5 shrink-0 text-accent" />
            <span>
              Demo login: <code className="font-mono-figures">demo@ecg-guard.local</code> /{" "}
              <code className="font-mono-figures">demo1234</code> (after running the seed script)
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === "register" && (
              <input
                className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-ink-primary outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
                placeholder="Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            )}
            <input
              className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-ink-primary outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            <input
              className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-ink-primary outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              placeholder="Password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />

            {error && <p className="text-sm text-critical">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-accent py-2.5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:opacity-50"
            >
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <button
            className="mt-4 text-sm font-medium text-accent hover:underline"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
