#!/usr/bin/env node
// Launches the Python detector service from its virtual environment, cross-platform (the
// venv's internal layout differs between Windows and macOS/Linux: `Scripts\` + `.exe` vs
// `bin/`). Used by `npm run dev:detector` and, via that, `npm start`.
import { spawn } from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const detectorDir = path.resolve(__dirname, "../services/detector");
const isWindows = process.platform === "win32";
const venvPython = path.join(
  detectorDir,
  "venv",
  isWindows ? "Scripts" : "bin",
  isWindows ? "python.exe" : "python",
);

if (!fs.existsSync(venvPython)) {
  console.error(
    `[detector] no virtual environment found at ${path.join(detectorDir, "venv")}.\n` +
      "[detector] run `npm run setup` first (one-time) to create it and install dependencies.",
  );
  process.exit(1);
}

const child = spawn(venvPython, ["-m", "uvicorn", "app.main:app", "--port", "8000"], {
  cwd: detectorDir,
  stdio: "inherit",
});

child.on("exit", (code) => process.exit(code ?? 0));
