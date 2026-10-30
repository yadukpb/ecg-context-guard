import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Activity,
  ArrowLeft,
  Bug,
  Gauge,
  HeartPulse,
  Play,
  Radio,
  Square,
  Waves,
} from "lucide-react";
import { api } from "../api/client";
import { usePolling } from "../hooks/usePolling";
import { VerdictBadge } from "../components/VerdictBadge";
import { EcgChart } from "../components/EcgChart";
import { ScoreTimeline } from "../components/ScoreTimeline";
import { ScoreMeter } from "../components/ScoreMeter";
import { StatTile } from "../components/StatTile";
import { DashboardGuide } from "../components/DashboardGuide";
import { Card } from "../components/Card";
import { verdictMeta } from "../lib/verdict";

const ATTACK_TYPES = [
  { value: "amplitude_drift", label: "Amplitude drift" },
  { value: "rr_stretch", label: "RR-interval stretch" },
  { value: "segment_replay", label: "Segment replay" },
];

export function PatientDashboard() {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [streamRunning, setStreamRunning] = useState(false);
  const [attackEnabled, setAttackEnabled] = useState(false);
  const [attackType, setAttackType] = useState(ATTACK_TYPES[0].value);
  const [intensity, setIntensity] = useState(0.7);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getPatient(id).then((d) => setPatient(d.patient));
    api
      .streamStatus(id)
      .then((status) => {
        setStreamRunning(!!status.running);
        setAttackEnabled(!!status.attack_enabled);
        if (status.attack_type && status.attack_type !== "none") setAttackType(status.attack_type);
      })
      .catch(() => {});
  }, [id]);

  const { data: latest } = usePolling(() => api.latestSegment(id), 2000, true, [id]);
  const { data: historyData } = usePolling(() => api.history(id, 60), 4000, true, [id]);

  const segment = latest?.segment;
  const verdict = segment?.detection?.verdict;
  const meta = verdictMeta(verdict);

  async function handleStart() {
    setBusy(true);
    setError("");
    try {
      await api.startStream(id);
      setStreamRunning(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleStop() {
    setBusy(true);
    try {
      await api.stopStream(id);
      setStreamRunning(false);
      setAttackEnabled(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleAttackToggle(enabled) {
    setBusy(true);
    setError("");
    try {
      await api.setAttack(id, { enabled, attackType, intensity });
      setAttackEnabled(enabled);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!patient) {
    return <div className="flex h-screen items-center justify-center text-ink-muted">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <Link to="/patients" className="mb-4 inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-accent">
        <ArrowLeft size={14} /> All patients
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">{patient.name}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            <span className="font-mono-figures">{patient.recordId}</span>
            {patient.recordId?.startsWith("bidmc:") ? " — real ECG + PPG" : " — MIT-BIH ECG"}
            {patient.cardiacHistory && ` — ${patient.cardiacHistory}`}
          </p>
        </div>
        <VerdictBadge verdict={verdict} calibrating={segment?.calibrating} size="lg" />
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-critical/30 bg-critical-wash px-4 py-2.5 text-sm text-critical">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-6 lg:col-span-2">
          <Card title="Live ECG window" subtitle="2-second replay window, updated every ~2s" icon={Activity}>
            <EcgChart waveform={segment?.waveform} color={meta.color} />
          </Card>

          <Card title="Detection score over time" subtitle="Weighted temporal + cross-sensor score" icon={Gauge}>
            <ScoreTimeline segments={historyData?.segments} />
          </Card>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile
              icon={HeartPulse}
              label="Heart rate"
              value={segment?.features ? segment.features.heart_rate_bpm.toFixed(0) : "—"}
              unit="bpm"
              baseline={patient.baseline ? `${patient.baseline.hr_mean.toFixed(0)} bpm` : null}
            />
            <StatTile
              icon={Activity}
              label="RR interval"
              value={segment?.features ? segment.features.rr_mean_sec.toFixed(2) : "—"}
              unit="s"
              baseline={patient.baseline ? `${patient.baseline.rr_mean.toFixed(2)} s` : null}
            />
            <StatTile
              icon={Waves}
              label="QRS amplitude"
              value={segment?.features ? segment.features.qrs_amplitude_mean.toFixed(2) : "—"}
              baseline={patient.baseline ? patient.baseline.amp_mean.toFixed(2) : null}
            />
            <StatTile
              icon={Radio}
              label="Secondary vital HR"
              value={segment?.secondaryHrBpm ? segment.secondaryHrBpm.toFixed(0) : "—"}
              unit="bpm"
              caption={segment?.crossSensorSource === "real_ppg" ? "real PPG sensor" : "synthetic stand-in"}
            />
          </div>
        </div>

        {/* Side column */}
        <div className="space-y-6">
          <Card title="Combined detection score" icon={Gauge}>
            <div className="mb-3 font-mono-figures text-3xl font-bold" style={{ color: meta.color }}>
              {segment?.detection ? segment.detection.combined_score.toFixed(2) : "—"}
            </div>
            <ScoreMeter score={segment?.detection?.combined_score ?? 0} />
          </Card>

          <Card title="Stream control" subtitle="Simulated IoMT device replay" icon={Play}>
            {!streamRunning ? (
              <button
                onClick={handleStart}
                disabled={busy}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-2.5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:opacity-50"
              >
                <Play size={15} /> Start stream
              </button>
            ) : (
              <button
                onClick={handleStop}
                disabled={busy}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-border py-2.5 text-sm font-semibold text-ink-primary transition hover:bg-accent-wash/60 disabled:opacity-50"
              >
                <Square size={14} /> Stop stream
              </button>
            )}
            <p className="mt-2 text-xs text-ink-muted">
              {streamRunning ? "Streaming live — polling every 2s." : "Stopped. Start to begin replaying ECG."}
            </p>
          </Card>

          <Card title="Attack simulation" subtitle="Injects a clinically-plausible manipulation" icon={Bug}>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-ink-muted">Attack type</label>
                <select
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink-primary outline-none focus:border-accent"
                  value={attackType}
                  onChange={(e) => setAttackType(e.target.value)}
                >
                  {ATTACK_TYPES.map((a) => (
                    <option key={a.value} value={a.value}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 flex justify-between text-xs font-medium text-ink-muted">
                  <span>Intensity</span>
                  <span className="font-mono-figures">{intensity.toFixed(1)}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={intensity}
                  onChange={(e) => setIntensity(Number(e.target.value))}
                  className="w-full accent-accent"
                />
              </div>

              <button
                onClick={() => handleAttackToggle(!attackEnabled)}
                disabled={busy || !streamRunning}
                className={`flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold text-white transition disabled:opacity-50 ${
                  attackEnabled ? "bg-critical hover:bg-critical/90" : "bg-slate-700 hover:bg-slate-600"
                }`}
              >
                <Bug size={15} />
                {attackEnabled ? "Stop attack simulation" : "Simulate attack"}
              </button>
              {!streamRunning && <p className="text-xs text-ink-muted">Start the stream first.</p>}
            </div>
          </Card>
        </div>
      </div>

      <DashboardGuide />
    </div>
  );
}
