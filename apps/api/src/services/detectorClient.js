/**
 * Thin HTTP client for the Python detector service's control endpoints. Express is the only
 * thing allowed to call these — the dashboard never talks to the detector service directly
 * (see docs/building/01-architecture.md).
 */
import { env } from "../config/env.js";

const BASE = env.detectorBaseUrl;

async function call(path, body) {
  const resp = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`detector service ${path} failed: ${resp.status} ${text}`);
  }
  return resp.json();
}

export const detectorClient = {
  listRecords: async () => {
    const resp = await fetch(`${BASE}/records`);
    return resp.json();
  },
  startStream: (patientId, recordId) =>
    call("/stream/start", { patient_id: patientId, record_id: recordId }),
  stopStream: (patientId) => call("/stream/stop", { patient_id: patientId }),
  setAttack: (patientId, { enabled, attackType, intensity }) =>
    call("/attack", {
      patient_id: patientId,
      enabled,
      attack_type: attackType,
      intensity,
    }),
  status: async (patientId) => {
    const resp = await fetch(`${BASE}/stream/${patientId}/status`);
    return resp.json();
  },
};
