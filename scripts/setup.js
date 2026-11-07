#!/usr/bin/env node
// One-time setup for running the app without Docker: installs Node dependencies, creates
// the Python detector service's virtual environment, installs its dependencies, and copies
// every .env.example to .env where one doesn't already exist. After this finishes once,
// `npm start` runs everything (including the database — see apps/api/src/config/db.js).
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";

function run(command, cwd) {
  console.log(`\n> ${command}${cwd ? `  (in ${path.relative(root, cwd) || "."})` : ""}`);
  execSync(command, { cwd: cwd || root, stdio: "inherit" });
}

function copyEnvIfMissing(dir) {
  const example = path.join(dir, ".env.example");
  const target = path.join(dir, ".env");
  if (!fs.existsSync(example)) return;
  if (fs.existsSync(target)) {
    console.log(`[setup] ${path.relative(root, target)} already exists, leaving it as is`);
    return;
  }
  fs.copyFileSync(example, target);
  console.log(`[setup] created ${path.relative(root, target)}`);
}

function findPythonCommand() {
  const candidates = isWindows ? ["python", "py"] : ["python3", "python"];
  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: "ignore" });
      return cmd;
    } catch {
      // try the next candidate
    }
  }
  console.error(
    "[setup] Could not find a working Python install (tried: " +
      candidates.join(", ") +
      ").\n[setup] Install Python 3.10+ first — see the README's Windows setup section — then re-run `npm run setup`.",
  );
  process.exit(1);
}

console.log("[setup] Installing Node dependencies (apps/api + apps/web)...");
run("npm install");

console.log("\n[setup] Setting up .env files...");
copyEnvIfMissing(path.join(root, "apps/api"));
copyEnvIfMissing(path.join(root, "apps/web"));
copyEnvIfMissing(path.join(root, "services/detector"));

const detectorDir = path.join(root, "services/detector");
const venvDir = path.join(detectorDir, "venv");
const venvPython = path.join(venvDir, isWindows ? "Scripts" : "bin", isWindows ? "python.exe" : "python");

if (fs.existsSync(venvPython)) {
  console.log(`\n[setup] Python virtual environment already exists at ${path.relative(root, venvDir)}`);
} else {
  console.log("\n[setup] Creating the Python detector service's virtual environment...");
  const pythonCmd = findPythonCommand();
  run(`${pythonCmd} -m venv venv`, detectorDir);
}

console.log("\n[setup] Installing Python dependencies...");
const pipPath = path.join(venvDir, isWindows ? "Scripts" : "bin", isWindows ? "pip.exe" : "pip");
run(`"${pipPath}" install -r requirements.txt`, detectorDir);

console.log(
  "\n[setup] Done. Run `npm start` to launch the detector, API, and web dashboard together.\n" +
    "[setup] No database setup needed — it starts itself automatically on first run.",
);
