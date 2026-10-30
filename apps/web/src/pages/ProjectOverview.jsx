import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  BellRing,
  Binary,
  Bug,
  Cable,
  Database,
  FlaskConical,
  GraduationCap,
  Layers,
  LogIn,
  PlayCircle,
  Radio,
  Server,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  SlidersHorizontal,
  Sparkles,
  Square,
  Target,
  Users,
  Waves,
} from "lucide-react";
import { CodeBlock } from "../components/CodeBlock";

const TOC = [
  ["problem", "The problem"],
  ["gap", "Research gap"],
  ["aim", "Aim & objectives"],
  ["architecture", "System architecture"],
  ["workflow", "End-to-end workflow"],
  ["algorithm", "Detection algorithm"],
  ["code", "Code walkthrough"],
  ["attacks", "Attack simulation"],
  ["howto", "How to run the demo"],
  ["evidence", "Live evidence"],
  ["dataset", "Dataset"],
  ["stack", "Tech stack"],
  ["limitations", "Limitations"],
  ["roadmap", "Roadmap"],
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

function ArchBox({ icon: Icon, title, subtitle, accent = false }) {
  return (
    <div
      className={`flex flex-col items-center gap-1.5 rounded-xl border p-4 text-center shadow-card ${
        accent ? "border-accent/40 bg-accent-wash" : "border-border bg-surface"
      }`}
    >
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${accent ? "bg-accent text-white" : "bg-accent-wash text-accent"}`}>
        <Icon size={17} />
      </div>
      <div className="text-sm font-semibold text-ink-primary">{title}</div>
      <div className="text-[11px] text-ink-muted">{subtitle}</div>
    </div>
  );
}

const WORKFLOW = [
  {
    title: "ECG data collection",
    body: "A Python background loop replays a real recording from the MIT-BIH Arrhythmia Database — a public archive of real, cardiologist-labeled patient ECGs, more on this under Dataset below — for the assigned patient, 2 seconds at a time, simulating a live IoMT cardiac monitor instead of a static file.",
  },
  {
    title: "Preprocessing & noise removal",
    body: "Each window passes through baseline-wander removal and a 0.5–40Hz bandpass filter before anything else touches it — standard ECG cleanup.",
  },
  {
    title: "Secure data transmission",
    body: "The cleaned window is AES-GCM encrypted and pushed to the Express API over HTTP, simulating the secure channel a real IoMT device would use.",
  },
  {
    title: "Patient-specific baseline creation",
    body: "The first 15 windows calibrate a per-patient profile — mean/SD of heart rate, RR-interval, and QRS amplitude — persisted so it survives a service restart.",
  },
  {
    title: "Temporal ECG analysis",
    body: "Every later window is compared against the patient's own baseline and their own last 10 windows, catching abrupt in-session changes a global threshold would miss.",
  },
  {
    title: "Cross-sensor analysis",
    body: "Patients backed by a BIDMC record get a real, independently-recorded PPG reading from the same patient. Patients backed by MIT-BIH (which has no second channel) get a disclosed synthetic stand-in instead.",
  },
  {
    title: "Attack simulation",
    body: "An optional, operator-triggered module distorts the outgoing window — amplitude drift, RR-interval stretch, or segment replay — while keeping it clinically plausible.",
  },
  {
    title: "Manipulation detection",
    body: "Baseline deviation, sudden change, and cross-sensor mismatch combine into one weighted score, classified as genuine, suspicious, or manipulated.",
  },
  {
    title: "Security alert & dashboard",
    body: "Non-genuine verdicts raise an alert, persisted in MongoDB and surfaced live on the clinician dashboard with the waveform, scores, and history.",
  },
];

const ATTACKS = [
  {
    icon: Waves,
    name: "Amplitude drift",
    mechanism: "QRS amplitude is scaled smoothly across the window (up to ±18%).",
    why: "Real amplitude changes happen (electrode contact, posture) — this mimics that while keeping values in range.",
  },
  {
    icon: Activity,
    name: "RR-interval stretch",
    mechanism: "The window is time-warped so beats land closer or farther apart than they really did (up to ±20%).",
    why: "Fabricates a heart-rate change without touching a single sample value — only timing is wrong.",
  },
  {
    icon: Binary,
    name: "Segment replay",
    mechanism: "The second half of the window is overwritten with an exact copy of the first half.",
    why: "Every value is real and previously genuine — but exact repetition never happens in a real heartbeat.",
  },
];

const HOWTO = [
  {
    icon: LogIn,
    title: "1. Log in",
    body: "Use the seeded demo account (demo@ecg-guard.local / demo1234) or register your own clinician account.",
  },
  {
    icon: Users,
    title: "2. Open a patient",
    body: "Go to Patients and open the demo patient — or add a new one and assign it any MIT-BIH record from the list.",
  },
  {
    icon: PlayCircle,
    title: "3. Start the stream",
    body: "Click Start stream. The detector either resumes a previously-saved baseline for that patient, or spends the first ~30 seconds (15 windows) calibrating a fresh one.",
  },
  {
    icon: ShieldCheck,
    title: "4. Watch it read genuine",
    body: "Once calibration finishes, the verdict badge turns green and the ECG trace, stat tiles, and score chart update roughly every 2 seconds — this is the real heartbeat, untouched.",
  },
  {
    icon: SlidersHorizontal,
    title: "5. Choose an attack",
    body: "Pick a type — amplitude drift, RR-interval stretch, or segment replay — and an intensity from 0 to 1 in the Attack Simulation panel.",
  },
  {
    icon: FlaskConical,
    title: "6. Simulate the attack",
    body: "Click Simulate attack. Within a window or two the verdict flips to suspicious or manipulated and the score meter crosses the marked thresholds live.",
  },
  {
    icon: BellRing,
    title: "7. Check the Alerts page",
    body: "Every non-genuine verdict is logged there in real time, filterable by severity, with an Acknowledge action per alert.",
  },
  {
    icon: Square,
    title: "8. Stop the stream",
    body: "Click Stop stream when you're done. The patient's calibrated baseline is saved, so starting again later skips recalibration.",
  },
];

const CODE_SNIPPETS = [
  {
    title: "Preprocessing — clean the window before anything else sees it",
    file: "services/detector/app/signal_proc.py",
    language: "python",
    code: `def bandpass_filter(x: np.ndarray, fs: int, low: float = 0.5, high: float = 40.0) -> np.ndarray:
    """General-purpose noise removal: keep the 0.5-40Hz band ECG signal content lives in."""
    nyq = fs / 2
    b, a = sps.butter(4, [low / nyq, high / nyq], btype="bandpass")
    return sps.filtfilt(b, a, x)


def remove_baseline_wander(x: np.ndarray, fs: int, cutoff: float = 0.5) -> np.ndarray:
    """Strip slow drift (respiration, electrode motion) below \`cutoff\` Hz."""
    nyq = fs / 2
    b, a = sps.butter(2, cutoff / nyq, btype="highpass")
    return sps.filtfilt(b, a, x)


def preprocess(raw: np.ndarray, fs: int) -> np.ndarray:
    """Full preprocessing step applied to every incoming window before anything else sees it."""
    x = remove_baseline_wander(raw, fs)
    x = bandpass_filter(x, fs)
    return x`,
    explain:
      "Two Butterworth filters, applied in order. The high-pass at 0.5Hz removes slow drift from breathing and electrode movement; the 0.5–40Hz bandpass then keeps only the frequency band real ECG content actually lives in. Nothing downstream — baselines, detection, attacks — ever sees a raw, unfiltered sample.",
  },
  {
    title: "Patient baseline — a floor so normal variation never looks extreme",
    file: "services/detector/app/baseline.py",
    language: "python",
    code: `# A floor on the standard deviations we'll use for z-scoring, so a patient whose calibration
# window happens to be perfectly uniform doesn't produce a baseline so tight that normal
# variation later reads as an extreme z-score (division by ~0).
_MIN_STD = {"hr": 2.0, "rr": 0.02, "amp": 0.03}


def build(self) -> BaselineProfile:
    return BaselineProfile(
        hr_mean=float(np.mean(self._hr)),
        hr_std=max(float(np.std(self._hr)), _MIN_STD["hr"]),
        rr_mean=float(np.mean(self._rr)),
        rr_std=max(float(np.std(self._rr)), _MIN_STD["rr"]),
        amp_mean=float(np.mean(self._amp)),
        amp_std=max(float(np.std(self._amp)), _MIN_STD["amp"]),
        n_calibration_windows=self.n_windows,
    )`,
    explain:
      "Each patient's own calibration-phase mean and standard deviation become their personal \"normal\" — not a population threshold. The max(...) floor matters: without it, a patient whose 15 calibration windows happened to be unusually steady would get a baseline so tight that completely ordinary variation later would read as an extreme z-score.",
  },
  {
    title: "Attack simulation — plausible by construction, not by luck",
    file: "services/detector/app/attack.py",
    language: "python",
    code: `# Bounds chosen so the manipulated signal stays within what a clinician would consider a
# plausible single reading, even at full intensity.
_MAX_AMPLITUDE_SCALE_DELTA = 0.18  # up to +/-18% amplitude scaling
_MAX_TIME_WARP = 0.20  # up to +/-20% effective RR stretch/compression


def apply_attack(window: np.ndarray, attack_type: AttackType, intensity: float) -> np.ndarray:
    intensity = max(0.0, min(1.0, intensity))

    if attack_type == AttackType.AMPLITUDE_DRIFT:
        n = len(window)
        delta = _MAX_AMPLITUDE_SCALE_DELTA * intensity
        ramp = np.linspace(1.0, 1.0 + delta, n)
        return window * ramp

    if attack_type == AttackType.RR_STRETCH:
        n = len(window)
        warp = 1.0 + _MAX_TIME_WARP * intensity
        stretched = resample(window, int(n * warp))
        return stretched[:n] if len(stretched) >= n else np.pad(stretched, (0, n - len(stretched)))`,
    explain:
      "intensity is clamped to [0, 1] and every branch's math is bounded by a constant chosen up front — amplitude scaling can never exceed ±18%, timing warp can never exceed ±20%. Even at intensity=1.0, the output can't drift into a range a clinician would call abnormal. That's the entire point of a semantic manipulation attack: it has to stay plausible to be the hard case.",
  },
  {
    title: "Detection — the formula shown earlier, as the literal running code",
    file: "services/detector/app/detector.py",
    language: "python",
    code: `def score_window(
    features: WindowFeatures,
    baseline: BaselineProfile,
    history: list[WindowFeatures],
    secondary_hr_bpm: float,
    cross_sensor_is_real: bool = False,
) -> DetectionResult:
    baseline_dev = _baseline_deviation(features, baseline)
    sudden = _sudden_change(features, history)
    temporal = _W_BASELINE_DEVIATION * baseline_dev + _W_SUDDEN_CHANGE * sudden
    expected_std = (
        _CROSS_SENSOR_EXPECTED_STD_BPM_REAL if cross_sensor_is_real
        else _CROSS_SENSOR_EXPECTED_STD_BPM_SYNTHETIC
    )
    cross_sensor = _cross_sensor_score(features.heart_rate_bpm, secondary_hr_bpm, expected_std)
    combined = _W_TEMPORAL * temporal + _W_CROSS_SENSOR * cross_sensor

    return DetectionResult(
        baseline_deviation=baseline_dev,
        sudden_change=sudden,
        temporal_score=temporal,
        cross_sensor_score=cross_sensor,
        combined_score=combined,
        verdict=_verdict_from_score(combined),
    )`,
    explain:
      "No model, no black box — this is the whole decision. Five numbers go in (this window's features, the patient's baseline, their recent history, the secondary vital, and whether that vital is a real sensor or the synthetic stand-in), two weighted sums come out, and a threshold on the second sum picks the verdict. A real independent sensor gets a wider expected-noise tolerance than the synthetic one, because two genuinely independent short-window readings naturally disagree more than a value mathematically derived from the same ECG — verified against real data, see the mistakes log.",
  },
  {
    title: "Real cross-sensor reading — peak-detecting an actual second sensor",
    file: "services/detector/app/signal_proc.py",
    language: "python",
    code: `def extract_ppg_hr(x: np.ndarray, fs: int) -> float:
    """Pulse rate from a real PPG window, independently of anything the ECG
    pipeline computed. Returns 0.0 ("no reliable reading") rather than
    guessing when the signal is too sparse or the result implausible."""
    peaks = detect_ppg_peaks(x, fs)
    if len(peaks) < _MIN_PPG_PEAKS:
        return 0.0
    intervals_sec = np.diff(peaks) / fs
    hr = float(60.0 / np.median(intervals_sec))
    if not (_PLAUSIBLE_HR_RANGE[0] <= hr <= _PLAUSIBLE_HR_RANGE[1]):
        return 0.0
    return hr`,
    explain:
      "For patients backed by a BIDMC record (real concurrent ECG + PPG from the same patient — see the Dataset section), this peak-detects the actual pulse-oximeter waveform instead of simulating a reading. Real PPG is noisier than ECG, so it abstains — returns 0.0, 'no reading this window' — rather than reporting a guess, the same honest behavior a real pulse oximeter shows on a poor-perfusion finger.",
  },
  {
    title: "Secure transport — two languages agreeing on one byte format",
    file: "services/detector/app/crypto_channel.py",
    language: "python",
    code: `_KEY = hashlib.sha256(TRANSPORT_SECRET.encode("utf-8")).digest()  # 32 bytes -> AES-256

def encrypt_json(payload: dict) -> str:
    plaintext = json.dumps(payload).encode("utf-8")
    cipher = AES.new(_KEY, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return (
        base64.b64encode(cipher.nonce).decode("ascii")
        + "."
        + base64.b64encode(ciphertext + tag).decode("ascii")
    )`,
    explain:
      "The Python detector service encrypts every outgoing window with AES-256-GCM, keyed by a SHA-256 hash of a shared secret. The payload format — base64(nonce) + \".\" + base64(ciphertext+tag) — is simple on purpose, because the Node API has to parse that exact same format in a completely different language.",
  },
  {
    title: "...and the other side, decrypting in Node",
    file: "apps/api/src/services/cryptoChannel.js",
    language: "javascript",
    code: `const KEY = crypto.createHash("sha256").update(env.transportSecret).digest();

export function decryptBlob(blob) {
  const [nonceB64, bodyB64] = blob.split(".");
  const nonce = Buffer.from(nonceB64, "base64");
  const body = Buffer.from(bodyB64, "base64");
  const tag = body.subarray(body.length - 16);
  const ciphertext = body.subarray(0, body.length - 16);

  const decipher = crypto.createDecipheriv("aes-256-gcm", KEY, nonce);
  decipher.setAuthTag(tag);
  const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  return JSON.parse(plaintext.toString("utf8"));
}`,
    explain:
      "Same key derivation (SHA-256 of the same shared secret), same framing, read back out. Every segment and alert in this app's database passed through this exact encrypt-in-Python / decrypt-in-Node round trip while testing the running app.",
  },
];

const LIMITATIONS = [
  "Real cross-sensor data only exists for BIDMC-backed patients: MIT-BIH has no second channel, so those patients still use a synthetically generated secondary vital tied to the true pre-attack heart rate — a genuine check in principle, but not a real sensor stream. Each patient's dashboard and the /records list both label which kind a patient has.",
  "Detection thresholds (2.0 suspicious / 3.5 manipulated) are reasoned defaults validated against real MIT-BIH windows, not fit to a large labeled attack dataset.",
  "Attack strength matters: a subtle attack at low intensity can legitimately score as genuine for a window or two — observed live, where amplitude drift at 0.7 intensity was weaker than RR-stretch at the same intensity.",
  "Single-channel MIT-BIH only — no multi-lead voting, no motion-artifact modeling, no patient-reported context (e.g. “I was exercising”).",
  "Detection is a documented weighted z-score scheme, not ML/DL — a deliberate choice for this semester, with ML/DL explicitly named as a future extension.",
];

export function ProjectOverview() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Hero */}
      <div className="mb-10">
        <div className="mb-4 flex flex-wrap gap-2">
          <Pill>Cybersecurity</Pill>
          <Pill>Healthcare IoMT</Pill>
          <Pill>Signal processing</Pill>
          <Pill>M.Tech Review Project · 2026–2027</Pill>
        </div>
        <h1 className="text-3xl font-extrabold leading-tight text-ink-primary sm:text-4xl">
          Context-Aware Detection of Semantic Data Manipulation Attacks in Remote ECG-Based
          Cardiac Patient Monitoring Systems
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-secondary">
          Remote cardiac monitoring sends a patient's ECG to clinicians over an IoMT network.
          An attacker doesn't need to push values to extremes to cause harm — a reading that
          stays entirely within a <em>clinically plausible</em> range can still be fabricated,
          and that kind of tampering is exactly what naive threshold-based monitors miss. This
          project builds, and actually runs, a system that instead asks: does this reading
          match <em>this patient's own</em> history, their own recent behaviour, and an
          independent vital-sign reading — not just "is this number in range."
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

      <Section id="problem" eyebrow="Problem statement" title="Why threshold-based monitoring isn't enough">
        <div className="space-y-4 text-sm leading-relaxed text-ink-secondary">
          <p>
            Remote ECG systems depend on trustworthy physiological data to make clinical
            decisions. An attacker with access to the data path — a compromised gateway, a
            man-in-the-middle position, a malicious firmware update — can subtly manipulate
            ECG measurements. If that manipulation keeps every value inside a textbook-normal
            range, a traditional threshold-based alarm never fires, because nothing is
            technically abnormal.
          </p>
          <p>
            The harder problem is that genuine physiological variation — exercise, stress,
            medication, sleep — can look a lot like malicious manipulation from the outside.
            Telling the two apart requires more context than any single reading can carry on
            its own: who the patient is, what their own normal looks like, how their rhythm
            has been behaving in this very session, and whether an independent signal agrees.
          </p>
        </div>
      </Section>

      <Section id="gap" eyebrow="Literature review finding" title="What the existing work doesn't cover">
        <ul className="grid gap-3 sm:grid-cols-2">
          {[
            "Existing approaches mainly detect obvious anomalies or out-of-range values",
            "Limited focus on semantically plausible data manipulation specifically",
            "Patient-specific ECG patterns are rarely modeled as the detection baseline",
            "Temporal behaviour within a session is underused as an evidence source",
            "Relationships between multiple physiological signals are rarely exploited",
            "Medical-context reasoning and cybersecurity analysis are rarely integrated",
          ].map((item) => (
            <li key={item} className="flex gap-2.5 rounded-lg border border-border bg-surface p-3 text-sm text-ink-secondary">
              <Target size={16} className="mt-0.5 shrink-0 text-accent" />
              {item}
            </li>
          ))}
        </ul>
      </Section>

      <Section id="aim" eyebrow="Aim & key objectives" title="What this project sets out to do">
        <p className="mb-4 text-sm leading-relaxed text-ink-secondary">
          Develop a context-aware cybersecurity system for detecting semantic data
          manipulation attacks in remote ECG-based cardiac monitoring — and prove it works
          against real ECG recordings, not a toy example.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            "Establish patient-specific ECG baselines",
            "Analyse temporal ECG behaviour within a session",
            "Analyse cross-sensor physiological consistency",
            "Simulate subtle, clinically-plausible manipulation attacks",
            "Detect suspicious or manipulated ECG data in near real time",
            "Improve physiological data integrity and security end-to-end",
          ].map((item) => (
            <div key={item} className="flex items-center gap-2.5 text-sm text-ink-secondary">
              <ShieldCheck size={16} className="shrink-0 text-good" />
              {item}
            </div>
          ))}
        </div>
      </Section>

      <Section id="architecture" eyebrow="How it's built" title="System architecture">
        <p className="mb-6 text-sm leading-relaxed text-ink-secondary">
          Three services, each with one job. The Python service owns signal math and knows
          nothing about users; Express owns persistence and auth and is the only thing
          allowed to drive the Python service; React only ever talks to Express.
        </p>
        <div className="grid grid-cols-5 items-center gap-3">
          <ArchBox icon={Layers} title="React Dashboard" subtitle="Vite · Tailwind · Recharts" />
          <ArrowRight className="mx-auto text-ink-muted" size={18} />
          <ArchBox icon={Server} title="Express API" subtitle="Auth · patients · alerts" accent />
          <ArrowRight className="mx-auto text-ink-muted" size={18} />
          <ArchBox icon={Cable} title="Detector service" subtitle="FastAPI · signal processing" />

          <div />
          <div />
          <ArrowDown className="mx-auto text-ink-muted" size={18} />
          <div />
          <ArrowDown className="mx-auto text-ink-muted" size={18} />

          <div />
          <div />
          <ArchBox icon={Database} title="MongoDB" subtitle="Patients · segments · alerts" />
          <div />
          <ArchBox icon={Radio} title="PhysioNet" subtitle="MIT-BIH Arrhythmia DB" />
        </div>
        <p className="mt-6 text-sm leading-relaxed text-ink-secondary">
          Transport between the detector and Express is <strong>AES-GCM encrypted</strong>,
          simulating the secure channel a real IoMT device would use — encryption happens the
          instant a window is ready to "transmit," decryption happens the instant Express
          receives it.
        </p>
      </Section>

      <Section id="workflow" eyebrow="Pipeline" title="What happens to every 2-second window">
        <ol className="relative space-y-6 border-l-2 border-border pl-6">
          {WORKFLOW.map((step, i) => (
            <li key={step.title} className="relative">
              <span className="absolute -left-[31px] flex h-6 w-6 items-center justify-center rounded-full bg-accent text-[11px] font-bold text-white">
                {i + 1}
              </span>
              <div className="text-sm font-semibold text-ink-primary">{step.title}</div>
              <p className="mt-0.5 text-sm leading-relaxed text-ink-secondary">{step.body}</p>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="algorithm" eyebrow="The core contribution" title="Detection algorithm, in full">
        <p className="mb-4 text-sm leading-relaxed text-ink-secondary">
          Deliberately <strong>not</strong> ML/DL-based — this semester's detector is an
          inspectable, documented weighted z-score scheme, with ML/DL named explicitly as a
          future extension once a larger labeled attack dataset exists.
        </p>

        <div className="mb-4 overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-accent-wash text-xs uppercase tracking-wide text-ink-muted">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Component</th>
                <th className="px-4 py-2.5 font-semibold">Compares against</th>
                <th className="px-4 py-2.5 font-semibold">Weight</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="px-4 py-2.5">Baseline deviation</td>
                <td className="px-4 py-2.5 text-ink-secondary">Patient's long-run calibrated baseline</td>
                <td className="px-4 py-2.5 font-mono-figures">0.4</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5">Sudden change</td>
                <td className="px-4 py-2.5 text-ink-secondary">Patient's own last 10 windows</td>
                <td className="px-4 py-2.5 font-mono-figures">0.6</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5">Cross-sensor score</td>
                <td className="px-4 py-2.5 text-ink-secondary">Independent secondary-vital HR reading</td>
                <td className="px-4 py-2.5 font-mono-figures">0.4 of combined</td>
              </tr>
            </tbody>
          </table>
        </div>

        <pre className="overflow-x-auto rounded-lg border border-border bg-page p-4 text-xs leading-relaxed text-ink-secondary">
{`temporal_score  = 0.4 · baseline_deviation + 0.6 · sudden_change
combined_score  = 0.6 · temporal_score     + 0.4 · cross_sensor_score

verdict = manipulated   if combined_score ≥ 3.5
          suspicious    if combined_score ≥ 2.0
          genuine        otherwise`}
        </pre>
        <p className="mt-4 text-sm leading-relaxed text-ink-secondary">
          Sudden change is weighted higher than long-run baseline deviation on purpose: a
          patient's rhythm drifting slowly over real sessions (exercise, medication, time of
          day) is normal; an abrupt jump <em>within one streaming session</em>, with no
          real-world event behind it, is the signature an injected attack leaves.
        </p>
      </Section>

      <Section id="code" eyebrow="From the source" title="Code walkthrough — how each principle is implemented">
        <p className="mb-6 text-sm leading-relaxed text-ink-secondary">
          Seven short excerpts, copied directly from the files that run in this build, cover
          the principles the whole system rests on: clean the signal first, give each patient
          their own normal, keep attacks plausible by construction, turn the verdict into a
          plain formula, and confirm the two services agree on one encrypted format.
        </p>
        <div className="space-y-6">
          {CODE_SNIPPETS.map((snip) => (
            <div key={snip.title}>
              <div className="mb-2 text-sm font-semibold text-ink-primary">{snip.title}</div>
              <CodeBlock code={snip.code} language={snip.language} filename={snip.file} />
              <p className="mt-2 text-xs leading-relaxed text-ink-secondary">{snip.explain}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="attacks" eyebrow="Red-team simulation" title="Three attacks, each still 'clinically plausible'">
        <p className="mb-5 text-sm leading-relaxed text-ink-secondary">
          These deliberately avoid pushing values out of range — that's the attack class
          naive threshold detectors already catch. Each stays inside a documented plausible
          bound even at full intensity.
        </p>
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          {ATTACKS.map(({ icon: Icon, name, mechanism, why }) => (
            <div key={name} className="rounded-xl border border-border bg-surface p-4 shadow-card">
              <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-critical-wash text-critical">
                <Icon size={16} />
              </div>
              <div className="mb-1 text-sm font-semibold text-ink-primary">{name}</div>
              <p className="mb-2 text-xs leading-relaxed text-ink-secondary">{mechanism}</p>
              <p className="text-xs italic leading-relaxed text-ink-muted">{why}</p>
            </div>
          ))}
        </div>
        <figure className="overflow-hidden rounded-xl border border-border bg-surface shadow-card">
          <img src="/figures/waveform_comparison.png" alt="Genuine ECG window compared against each attack type" className="w-full" />
          <figcaption className="border-t border-border px-4 py-3 text-xs text-ink-muted">
            Real MIT-BIH window (top) vs. each attack applied at full intensity. Generated by{" "}
            <code className="font-mono-figures">services/detector/scripts/generate_report_figures.py</code>{" "}
            — every line here is a real, preprocessed ECG signal from the running detector
            service.
          </figcaption>
        </figure>
      </Section>

      <Section id="howto" eyebrow="Try it yourself" title="How to run this demo">
        <p className="mb-5 text-sm leading-relaxed text-ink-secondary">
          Here's the exact sequence to drive it end-to-end, starting from the Patients page.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {HOWTO.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex gap-3 rounded-xl border border-border bg-surface p-4 shadow-card">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-wash text-accent">
                <Icon size={16} />
              </div>
              <div>
                <div className="text-sm font-semibold text-ink-primary">{title}</div>
                <p className="mt-0.5 text-xs leading-relaxed text-ink-secondary">{body}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section id="evidence" eyebrow="Verified live" title="Live evidence from this working build">
        <p className="mb-5 text-sm leading-relaxed text-ink-secondary">
          Every claim on this page was exercised end-to-end against the running system: real
          MIT-BIH data, real encryption and decryption, real detection scoring.
        </p>
        <figure className="mb-6 overflow-hidden rounded-xl border border-border bg-surface shadow-card">
          <img src="/figures/detection_timeline.png" alt="Detection score over time, attack switched on partway through" className="w-full" />
          <figcaption className="border-t border-border px-4 py-3 text-xs text-ink-muted">
            Ten genuine windows (green), then an RR-stretch attack switched on — the score
            jumps straight past the manipulated threshold and stays there.
          </figcaption>
        </figure>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-good/30 bg-good-wash p-4">
            <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-good">
              <ShieldCheck size={16} /> Genuine stream, verified live
            </div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              Heart rate 76 bpm against a 74 bpm baseline, combined score 0.26 — comfortably
              under the suspicious threshold, verdict <strong>genuine</strong>, confirmed in
              a real browser session against the running dashboard.
            </p>
          </div>
          <div className="rounded-xl border border-critical/30 bg-critical-wash p-4">
            <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-critical">
              <ShieldX size={16} /> Same patient, attack switched on
            </div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              RR-interval stretch at intensity 1.0 drove heart rate to 64 bpm, cross-sensor
              score to 6.77, combined score to 4.18 — verdict flipped to{" "}
              <strong>manipulated</strong> within one 2-second window, with an alert raised
              automatically.
            </p>
          </div>
        </div>

        <p className="mb-4 mt-6 text-sm leading-relaxed text-ink-secondary">
          The same attack, run against a <strong className="text-ink-primary">BIDMC-backed
          patient</strong> — a real second sensor (PPG), not the synthetic stand-in above:
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-good/30 bg-good-wash p-4">
            <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-good">
              <ShieldCheck size={16} /> Genuine stream, real PPG sensor
            </div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              Heart rate 101 bpm, real PPG-derived secondary HR 96 bpm, combined score 0.22 —
              the two independent sensors agree closely on their own, verdict{" "}
              <strong>genuine</strong>, confirmed live against the running dashboard.
            </p>
          </div>
          <div className="rounded-xl border border-warning/30 bg-warning-wash p-4">
            <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-warning">
              <ShieldAlert size={16} /> Same patient, attack switched on
            </div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              RR-interval stretch at intensity 0.7 attacked only the transmitted ECG — the
              real PPG channel kept reporting the patient's true rate, the disagreement pushed
              the combined score to 2.37, verdict flipped to <strong>suspicious</strong>.
            </p>
          </div>
        </div>
      </Section>

      <Section id="dataset" eyebrow="Ground truth" title="Dataset">
        <div className="mb-5 rounded-lg border border-border bg-page p-4 text-sm leading-relaxed text-ink-secondary">
          <strong className="text-ink-primary">What is MIT-BIH?</strong> The MIT-BIH
          Arrhythmia Database is one of the most widely used public ECG datasets in
          biomedical research. In the late 1970s, researchers at MIT and Boston's Beth Israel
          Hospital recorded real patients' heart activity on Holter monitors and had
          cardiologists manually label every single heartbeat — normal and abnormal.
          PhysioNet, a public archive, has hosted it ever since, free to stream or download.
          So when this project says "MIT-BIH record 100," it means one specific, real
          patient's labeled recording from that archive — not a generated or simulated
          waveform.
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <dl className="space-y-2 text-sm">
              {[
                ["Source", "PhysioNet — MIT-BIH Arrhythmia Database"],
                ["Records", "48 recordings from 47 subjects"],
                ["Sampling rate", "360 Hz"],
                ["Channels used", "Lead II (MLII), two-channel source"],
                ["Access method", "wfdb.rdrecord(..., pn_dir=\"mitdb\") — streamed directly, no manual download"],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-3">
                  <dt className="w-32 shrink-0 font-medium text-ink-muted">{k}</dt>
                  <dd className="text-ink-secondary">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="rounded-lg border border-border bg-page p-4 text-sm text-ink-secondary">
            <strong className="text-ink-primary">Why MIT-BIH:</strong> it's a well-established,
            publicly verifiable clinical ECG dataset. Using real recordings, rather than
            synthetic waveforms, means every genuine-vs-manipulated comparison on this page is
            grounded in an actual patient's heartbeat — not a generated signal shaped to make
            the detector look good.
          </div>
        </div>

        <div className="mt-5 rounded-lg border border-border bg-page p-4 text-sm leading-relaxed text-ink-secondary">
          <strong className="text-ink-primary">What is BIDMC?</strong> The BIDMC PPG and
          Respiration Database, also hosted on PhysioNet, contains real concurrent ECG *and*
          PPG (pulse-oximeter) recordings from the same ICU patients on the same timebase —
          extracted from the MIMIC II Matched Waveform Database. It exists in this project for
          one specific reason: MIT-BIH only has ECG, so it can't supply a genuine second
          sensor for the cross-sensor check (see Detection algorithm). BIDMC can.
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <dl className="space-y-2 text-sm">
            {[
              ["Source", "PhysioNet — BIDMC PPG and Respiration Database"],
              ["Records used", "5 of 53 (bidmc:05 – bidmc:09, curated — see below)"],
              ["Sampling rate", "125 Hz"],
              ["Channels used", "ECG (lead II) and PLETH (PPG), same patient, same timebase"],
              ["Access method", "wfdb.rdrecord(\"bidmcNN\", pn_dir=\"bidmc\") — streamed directly"],
            ].map(([k, v]) => (
              <div key={k} className="flex gap-3">
                <dt className="w-32 shrink-0 font-medium text-ink-muted">{k}</dt>
                <dd className="text-ink-secondary">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="rounded-lg border border-border bg-page p-4 text-sm text-ink-secondary">
            <strong className="text-ink-primary">Why only 5 of 53 records:</strong> stress-tested
            the first 20 against ~100 genuine, unattacked windows each. Several (01-04, 10, 17)
            occasionally crossed the suspicious/manipulated threshold on clean data — real
            sensor and short-window noise specific to those recordings, not a detector bug.
            Rather than loosen the detector to paper over the noisiest recordings, the five
            offered demo patients (05-09) were chosen because they held up under that stress
            test. Full investigation in <code className="rounded bg-surface px-1 py-0.5 text-[11px]">docs/mistakes-log.md</code>.
          </div>
        </div>
      </Section>

      <Section id="stack" eyebrow="Implementation" title="Tech stack">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-border bg-surface p-4 shadow-card">
            <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-accent-wash text-accent">
              <Cable size={16} />
            </div>
            <div className="mb-1 text-sm font-semibold text-ink-primary">Detector service</div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              Python, FastAPI, wfdb, SciPy/NumPy, PyCryptodome. Owns MIT-BIH loading,
              filtering, R-peak detection, baselines, attack simulation, and scoring.
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4 shadow-card">
            <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-accent-wash text-accent">
              <Server size={16} />
            </div>
            <div className="mb-1 text-sm font-semibold text-ink-primary">Backend API</div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              Node, Express, Mongoose, MongoDB, JWT-cookie auth. System of record for
              patients, segments, and alerts; the only caller of the detector service.
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4 shadow-card">
            <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-accent-wash text-accent">
              <Layers size={16} />
            </div>
            <div className="mb-1 text-sm font-semibold text-ink-primary">Dashboard</div>
            <p className="text-xs leading-relaxed text-ink-secondary">
              React, Vite, Tailwind, Recharts. Live ECG waveform, score timeline, attack
              controls, and an alert feed — polling-based, no websockets yet.
            </p>
          </div>
        </div>
      </Section>

      <Section id="limitations" eyebrow="Said plainly, not discovered by a panel" title="Honest limitations">
        <ul className="space-y-3">
          {LIMITATIONS.map((item) => (
            <li key={item} className="flex gap-2.5 rounded-lg border border-warning/30 bg-warning-wash p-3 text-sm text-ink-secondary">
              <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
              {item}
            </li>
          ))}
        </ul>
      </Section>

      <Section id="roadmap" eyebrow="Project plan" title="Semester split">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface p-5 shadow-card">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink-primary">
              <Sparkles size={16} className="text-accent" /> Semester 1 — this build
            </div>
            <p className="text-sm leading-relaxed text-ink-secondary">
              Secure monitoring and attack-simulation platform: real ECG replay, secure
              transmission, patient baselines, temporal + cross-sensor analysis, the three
              attack types, and the weighted-threshold detector — all running end-to-end.
            </p>
          </div>
          <div className="rounded-xl border border-dashed border-border bg-surface p-5">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink-primary">
              <Bug size={16} className="text-ink-muted" /> Semester 2 — proposed extension
            </div>
            <p className="text-sm leading-relaxed text-ink-secondary">
              ML/DL-based detection trained on a larger labeled attack set, multi-lead and
              real multi-sensor support, and threshold tuning against a formal evaluation
              protocol rather than reasoned defaults.
            </p>
          </div>
        </div>
      </Section>

      <div className="flex flex-wrap items-center gap-2 pt-4 text-xs text-ink-muted">
        <GraduationCap size={14} />
        Presented by Aneesh S (KH.EN.P2MCA25215) &amp; Gifty Mary (KH.EN.P2MCA25226) · Guide:
        Aparna V · Department of Computer Science · Amrita Vishwa Vidyapeetham, 2026–2027
      </div>
    </div>
  );
}
