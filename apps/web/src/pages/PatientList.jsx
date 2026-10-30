import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Clock, HeartPulse, Plus, Radio, Users } from "lucide-react";
import { api } from "../api/client";
import { Card } from "../components/Card";

export function PatientList() {
  const [patients, setPatients] = useState([]);
  const [records, setRecords] = useState([]);
  const [form, setForm] = useState({ name: "", cardiacHistory: "", recordId: "" });
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [loaded, setLoaded] = useState(false);

  async function refresh() {
    const [{ patients }, { records }] = await Promise.all([api.listPatients(), api.listRecords()]);
    setPatients(patients);
    setRecords(records);
    setForm((f) => ({ ...f, recordId: f.recordId || records[0]?.id || "" }));
    setLoaded(true);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      await api.createPatient(form);
      setForm({ ...form, name: "", cardiacHistory: "" });
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-wash text-accent">
          <Users size={18} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Patients</h1>
          <p className="text-sm text-ink-muted">
            Each patient streams a real PhysioNet record — MIT-BIH (ECG only) or BIDMC (ECG + real PPG).
          </p>
        </div>
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2">
        {patients.map((p) => (
          <Link
            key={p._id}
            to={`/patients/${p._id}`}
            className="group rounded-xl border border-border bg-surface p-5 shadow-card transition hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-md"
          >
            <div className="mb-3 flex items-start justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-wash text-accent">
                <HeartPulse size={18} />
              </div>
              {p.baseline ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-good-wash px-2.5 py-1 text-xs font-medium text-good">
                  <CheckCircle2 size={12} /> Baseline ready
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-xs font-medium text-ink-muted">
                  <Clock size={12} /> Not calibrated
                </span>
              )}
            </div>
            <div className="font-semibold text-ink-primary group-hover:text-accent">{p.name}</div>
            <div className="mt-1 flex items-center gap-1.5 text-xs text-ink-muted">
              <span className="font-mono-figures">{p.recordId}</span>
              {p.recordId?.startsWith("bidmc:") ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-good-wash px-1.5 py-0.5 text-[10px] font-medium text-good">
                  <Radio size={10} /> real cross-sensor
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full border border-border px-1.5 py-0.5 text-[10px] font-medium text-ink-muted">
                  synthetic cross-sensor
                </span>
              )}
            </div>
            {p.cardiacHistory && (
              <p className="mt-2 line-clamp-2 text-xs text-ink-secondary">{p.cardiacHistory}</p>
            )}
          </Link>
        ))}
        {loaded && patients.length === 0 && (
          <div className="col-span-2 rounded-xl border border-dashed border-border p-8 text-center text-sm text-ink-muted">
            No patients yet — add one below to start a stream.
          </div>
        )}
      </div>

      <Card title="Add a patient" icon={Plus} className="max-w-md">
        <form onSubmit={handleCreate} className="space-y-3">
          <input
            className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
            placeholder="Patient name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <textarea
            className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
            placeholder="Cardiac history (optional)"
            rows={2}
            value={form.cardiacHistory}
            onChange={(e) => setForm({ ...form, cardiacHistory: e.target.value })}
          />
          <select
            className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-ink-primary outline-none focus:border-accent"
            value={form.recordId}
            onChange={(e) => setForm({ ...form, recordId: e.target.value })}
          >
            <optgroup label="MIT-BIH — ECG only, synthetic cross-sensor">
              {records
                .filter((r) => r.dataset === "mitdb")
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
            </optgroup>
            <optgroup label="BIDMC — real ECG + PPG, real cross-sensor">
              {records
                .filter((r) => r.dataset === "bidmc")
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
            </optgroup>
          </select>
          <p className="-mt-1 text-xs text-ink-muted">
            BIDMC patients cross-check the ECG against a real, independently-recorded PPG channel from the
            same patient. MIT-BIH has no second channel, so those patients use a disclosed synthetic
            stand-in instead (see the Overview page).
          </p>

          {error && <p className="text-sm text-critical">{error}</p>}

          <button
            type="submit"
            disabled={creating}
            className="rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:opacity-50"
          >
            Add patient
          </button>
        </form>
      </Card>
    </div>
  );
}
