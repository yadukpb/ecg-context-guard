import { AlertTriangle, CheckCircle2, Loader2, XCircle } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "../components/Card";
import { CodeBlock } from "../components/CodeBlock";
import { StatTile } from "../components/StatTile";
import { gaps, paper1, paper2, thecf } from "../data/researchFindings";

const TOC = [
  ["overview", "Overview"],
  ["thecf", "THECF calibration"],
  ["paper2", "HGAN-SVM-DT + SFOA-CNN"],
  ["paper1", "Attack-independent defence"],
  ["gaps", "Honest gaps"],
];

function Section({ id, eyebrow, title, children }) {
  return (
    <section id={id} className="scroll-mt-20 border-b border-border py-10 first:pt-0 last:border-0">
      <div className="mb-5">
        <div className="text-xs font-semibold uppercase tracking-wider text-accent">{eyebrow}</div>
        <h2 className="mt-1 text-xl font-bold text-ink-primary sm:text-2xl">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Pill({ children }) {
  return (
    <span className="inline-flex items-center rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-ink-secondary">
      {children}
    </span>
  );
}

function Pct(x, digits = 1) {
  return x == null ? "—" : `${(x * 100).toFixed(digits)}%`;
}

function PendingNote({ children }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-border bg-page p-3 text-xs text-ink-muted">
      <Loader2 size={14} className="animate-spin shrink-0" />
      {children}
    </div>
  );
}

function KeyValueList({ rows }) {
  return (
    <dl className="space-y-2 text-sm">
      {rows.map(([k, v]) => (
        <div key={k} className="flex gap-3">
          <dt className="w-40 shrink-0 font-medium text-ink-muted">{k}</dt>
          <dd className="text-ink-secondary">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function CustomTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs"
      style={{ background: "rgb(var(--surface-raised))", borderColor: "var(--border)" }}
    >
      <div className="mb-1 font-semibold text-ink-primary">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {formatter ? formatter(p.value) : p.value}
        </div>
      ))}
    </div>
  );
}

function EpsilonSweepChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="rgb(var(--gridline))" vertical={false} />
        <XAxis
          dataKey="epsilon"
          tick={{ fontSize: 11, fill: "rgb(var(--ink-muted))" }}
          axisLine={{ stroke: "rgb(var(--axis))" }}
          tickLine={false}
          label={{ value: "epsilon (ε)", position: "insideBottom", offset: -4, fontSize: 11, fill: "rgb(var(--ink-muted))" }}
        />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
          tick={{ fontSize: 11, fill: "rgb(var(--ink-muted))" }}
          axisLine={{ stroke: "rgb(var(--axis))" }}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<CustomTooltip formatter={(v) => Pct(v)} />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="fgsm" name="FGSM" stroke="rgb(var(--accent))" strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
        <Line type="monotone" dataKey="pgd" name="PGD" stroke="rgb(var(--series-2))" strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function RecallBarChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="rgb(var(--gridline))" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: "rgb(var(--ink-muted))" }} axisLine={{ stroke: "rgb(var(--axis))" }} tickLine={false} />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v) => `${Math.round(v * 100)}%`}
          tick={{ fontSize: 11, fill: "rgb(var(--ink-muted))" }}
          axisLine={{ stroke: "rgb(var(--axis))" }}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<CustomTooltip formatter={(v) => Pct(v)} />} />
        <Bar dataKey="value" name="Recall" fill="rgb(var(--accent))" radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ResearchFindings() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Hero */}
      <div className="mb-10">
        <div className="mb-4 flex flex-wrap gap-2">
          <Pill>Dissertation background research</Pill>
          <Pill>Two-paper reproduction</Pill>
          <Pill>Real PhysioNet / Dataverse data only</Pill>
        </div>
        <h1 className="text-3xl font-extrabold leading-tight text-ink-primary sm:text-4xl">
          Research findings — reproducing two published ECG-security papers
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-secondary">
          This is background validation work behind the dissertation, separate from the live
          detector elsewhere in this app: a from-scratch, honest reproduction of two published
          papers against real data, reporting what matched and what didn't — never tuned to
          match the papers' own published numbers.{" "}
          <code className="rounded bg-surface px-1 py-0.5 text-[11px] break-all">research/COMPARISON_REPORT.md</code>{" "}
          and{" "}
          <code className="rounded bg-surface px-1 py-0.5 text-[11px] break-all">research/FEASIBILITY_REPORT.md</code>{" "}
          in the repository are the full source documents this page summarizes.
        </p>
      </div>

      {/* In-page contents */}
      <nav className="mb-10 flex flex-wrap gap-x-5 gap-y-2 rounded-xl border border-border bg-surface px-5 py-4 text-sm">
        {TOC.map(([id, label]) => (
          <a key={id} href={`#${id}`} className="text-ink-secondary hover:text-accent hover:underline">
            {label}
          </a>
        ))}
      </nav>

      <Section id="overview" eyebrow="What this is" title="Two papers, reproduced honestly">
        <div className="space-y-4 text-sm leading-relaxed text-ink-secondary">
          <p>
            Before building the live detector, two published papers close to this
            dissertation's problem space were independently reproduced end-to-end against
            real data — not re-explained, actually re-run:{" "}
            <strong className="text-ink-primary">
              "A power-efficient layered MIoT framework for real-time ECG anomaly detection
              and sensor fault classification based on hierarchical THECF and hybrid
              intelligent models"
            </strong>{" "}
            (THECF + HGAN-SVM-DT + SFOA-CNN, referred to below as Paper 2) and{" "}
            <strong className="text-ink-primary">
              "Attack-data independent defence mechanism against adversarial attacks on ECG
              signal"
            </strong>{" "}
            (referred to below as Paper 1).
          </p>
          <p>
            The rule throughout: every number on this page comes from an actual run against
            real PhysioNet / Harvard Dataverse data in this session. Where a published figure
            wasn't reproduced, that gap is named and explained — never hidden, never tuned
            away to look better.
          </p>
        </div>
      </Section>

      <Section id="thecf" eyebrow="Paper 2 — layer 2" title="THECF: a threshold that didn't hold, and why">
        <p className="mb-5 text-sm leading-relaxed text-ink-secondary">
          THECF's QRS-band-energy-ratio gate rejects a window unless 18–85% of its energy
          falls in a 30–45Hz band — the paper's own published range. Two independent
          measurements on real MIT-BIH (a Butterworth+filtfilt bandpass and a raw FFT
          band-power calculation) found real clean windows carry only ~0.2–1.3% of their
          energy there, not ~42% as the paper's own population statistic claims. Rather than
          hard-code a number that doesn't hold under this windowing convention, thresholds
          were re-derived from {thecf.calibrationDerivation.nCleanWindows.toLocaleString()} real
          clean MIT-BIH windows using the paper's own stated method for its third layer: mean
          ± 2·std.
        </p>
        <div className="mb-5 grid gap-4 sm:grid-cols-2">
          <StatTile icon={XCircle} label="Clean-pass-rate, literal paper thresholds" value={Pct(thecf.literal.cleanPassRate)} caption="rejects effectively every real window" />
          <StatTile icon={CheckCircle2} label="Clean-pass-rate, calibrated thresholds" value={Pct(thecf.calibrated.cleanPassRate)} caption="genuinely discriminative, not degenerate" />
        </div>
        <div className="mb-5 grid gap-4 sm:grid-cols-3">
          {Object.entries(thecf.calibrated.noisyDetectedRateByType).map(([type, rate]) => (
            <StatTile key={type} label={`${type.toUpperCase()} noise detected`} value={Pct(rate)} caption="calibrated thresholds" />
          ))}
        </div>
        <CodeBlock
          filename="research/Paper_2_Layered_MIOT_Framework/THECF/calibrate.py"
          language="python"
          code={`thresholds = thecf.Thresholds(
    energy_low=max(0.0, e_mean - 2 * e_std),
    energy_high=e_mean + 2 * e_std,
    qrs_ratio_low=max(0.0, q_mean - 2 * q_std),
    qrs_ratio_high=q_mean + 2 * q_std,
    ncc_accept=max(0.0, n_mean - 2 * n_std),
)`}
        />
      </Section>

      <Section id="paper2" eyebrow="Paper 2 — layers 3 & 4" title="HGAN-SVM-DT ablation + SFOA-CNN classification">
        <div className="mb-5">
          <KeyValueList
            rows={[
              ["Records", paper2.config.records],
              ["Cross-validation", `${paper2.config.folds}-fold, patient-independent`],
              ["SFOA", `population ${paper2.config.sfoaPopulation}, iterations ${paper2.config.sfoaIterations} — matches the paper's own config`],
            ]}
          />
        </div>
        {paper2.detectionAblation && paper2.classification ? (
          <div className="space-y-6">
            <div>
              <h3 className="mb-3 text-sm font-semibold text-ink-primary">
                HGAN-SVM-DT ablation (normal vs. abnormal, accuracy)
              </h3>
              <RecallBarChart
                data={[
                  ["SVM only", paper2.detectionAblation.svmOnly],
                  ["DT only", paper2.detectionAblation.dtOnly],
                  ["SVM+DT, default", paper2.detectionAblation.svmPlusDtDefault],
                  ["SVM+DT, SFOA-tuned", paper2.detectionAblation.svmPlusDtSfoa],
                ].map(([label, m]) => ({ label, value: m.accuracy }))}
              />
            </div>
            <div>
              <h3 className="mb-3 text-sm font-semibold text-ink-primary">
                SFOA-CNN per-class recall (7 arrhythmia classes)
              </h3>
              <RecallBarChart
                data={Object.entries(paper2.classification.perClassRecall).map(([label, value]) => ({ label, value }))}
              />
              <p className="mt-2 text-xs text-ink-muted">
                Overall: {Pct(paper2.classification.accuracy)} accuracy, {Pct(paper2.classification.f1Macro)} macro-F1
                over {paper2.classification.foldsRun} folds.
              </p>
            </div>
          </div>
        ) : (
          <PendingNote>
            Still running at full scale (48 records × 5-fold CV × SFOA 30/50 — the paper's own
            hardware took 90–120 minutes for the CNN stage alone). This section fills in from{" "}
            <code className="rounded bg-surface px-1 py-0.5 text-[11px] break-all">
              research/Paper_2_Layered_MIOT_Framework/evaluation/results.json
            </code>{" "}
            once that run completes.
          </PendingNote>
        )}
      </Section>

      <Section id="paper1" eyebrow="Paper 1" title="Attack-data-independent defence (the ECG 'gatekeeper')">
        <p className="mb-5 text-sm leading-relaxed text-ink-secondary">
          A ResNet-18 (1D) trained to flag noisy/attacked ECG windows before they reach a
          diagnostic model — evaluated across all four of the paper's named datasets
          combined, not just one.
        </p>
        <div className="mb-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile label="Total samples" value={paper1.datasets.total.toLocaleString()} />
          <StatTile label="Train / test split" value={`${paper1.split.train} / ${paper1.split.test}`} caption={paper1.split.kind} />
          <StatTile label="Clean/noisy accuracy" value={Pct(paper1.cleanVsNoisy.accuracy)} />
          <StatTile label="Clean/noisy F1" value={Pct(paper1.cleanVsNoisy.f1)} />
        </div>
        <div className="mb-5">
          <KeyValueList
            rows={Object.entries(paper1.datasets.perDataset).map(([name, n]) => [
              name === "ecgid" ? "ECG-ID" : name === "cinc2011" ? "CinC-2011" : name === "cinc2014" ? "CinC-2014" : "teleECG",
              `${n} samples`,
            ])}
          />
        </div>
        {paper1.attacks ? (
          <div className="space-y-6">
            <div>
              <h3 className="mb-3 text-sm font-semibold text-ink-primary">
                FGSM vs. PGD accuracy across the paper's 7-value epsilon sweep
              </h3>
              <EpsilonSweepChart
                data={Object.keys(paper1.attacks.fgsm).map((eps) => ({
                  epsilon: eps,
                  fgsm: paper1.attacks.fgsm[eps].accuracy,
                  pgd: paper1.attacks.pgd[eps].accuracy,
                }))}
              />
              <p className="mt-2 text-xs text-ink-muted">
                PGD collapses to 0% accuracy at ε ≥ 0.1 — a real, measured effect of training
                on a much smaller, less diverse dataset than the paper's own ~15,000-segment
                one: at large perturbations the gatekeeper's decision boundary gets pushed the
                <em> wrong</em> way (misclassifying attacked input as clean) rather than
                staying robust. FGSM degrades more gracefully over the same range.
              </p>
            </div>
            <Card title="Real IBM ART black-box attacks" subtitle="HopSkipJump / Boundary, against the trained gatekeeper">
              <KeyValueList
                rows={[
                  ["HopSkipJump (ART)", `${Pct(paper1.attacks.hopskipjumpArt?.[0.0]?.accuracy)} accuracy, n=${paper1.attacks.hopskipjumpArt?.[0.0]?.nSamples ?? "—"}`],
                  ["Boundary (ART)", `${Pct(paper1.attacks.boundaryArt?.[0.0]?.accuracy)} accuracy, n=${paper1.attacks.boundaryArt?.[0.0]?.nSamples ?? "—"}`],
                ]}
              />
            </Card>
            {paper1.leaveOneDatasetOut && (
              <Card title="Leave-one-dataset-out generalization" subtitle="train on 3 of 4 datasets, test on the held-out one — the paper's own protocol">
                <KeyValueList
                  rows={Object.entries(paper1.leaveOneDatasetOut).map(([name, m]) => [
                    name,
                    m.skipped ? m.skipped : `${Pct(m.accuracy)} accuracy, ${Pct(m.f1)} F1`,
                  ])}
                />
              </Card>
            )}
          </div>
        ) : (
          <PendingNote>
            Adversarial robustness (FGSM/PGD across the paper's real 7-value epsilon sweep),
            real IBM ART HopSkipJump/Boundary black-box results, and leave-one-dataset-out
            generalization are still computing — the ART BoundaryAttack is the long pole, with
            up to 100 real model-query iterations per sample. This section fills in from{" "}
            <code className="rounded bg-surface px-1 py-0.5 text-[11px] break-all">
              research/Paper_1_Attack_Independent_Defence/evaluation/results.json
            </code>{" "}
            once that run completes.
          </PendingNote>
        )}
      </Section>

      <Section id="gaps" eyebrow="Said plainly, not discovered by a panel" title="Honest gaps">
        <ul className="space-y-3">
          {gaps.map((gap) => (
            <li key={gap.title} className="flex gap-2.5 rounded-lg border border-warning/30 bg-warning-wash p-3 text-sm text-ink-secondary">
              <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
              <div>
                <div className="font-medium text-ink-primary">{gap.title}</div>
                <div className="mt-0.5">{gap.body}</div>
              </div>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}
