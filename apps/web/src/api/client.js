const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:4000";

async function request(path, { method = "GET", body } = {}) {
  const resp = await fetch(`${BASE_URL}${path}`, {
    method,
    credentials: "include", // sends/receives the httpOnly JWT cookie
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  const isJson = resp.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await resp.json() : null;

  if (!resp.ok) {
    throw new Error(data?.error || `Request to ${path} failed with ${resp.status}`);
  }
  return data;
}

export const api = {
  register: (body) => request("/api/auth/register", { method: "POST", body }),
  login: (body) => request("/api/auth/login", { method: "POST", body }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  me: () => request("/api/auth/me"),

  listRecords: () => request("/api/patients/meta/records"),
  listPatients: () => request("/api/patients"),
  createPatient: (body) => request("/api/patients", { method: "POST", body }),
  getPatient: (id) => request(`/api/patients/${id}`),
  latestSegment: (id) => request(`/api/patients/${id}/latest`),
  history: (id, limit = 60) => request(`/api/patients/${id}/history?limit=${limit}`),

  startStream: (id) => request(`/api/patients/${id}/start`, { method: "POST" }),
  stopStream: (id) => request(`/api/patients/${id}/stop`, { method: "POST" }),
  setAttack: (id, body) => request(`/api/patients/${id}/attack`, { method: "POST", body }),
  streamStatus: (id) => request(`/api/patients/${id}/status`),

  listAlerts: (limit = 50) => request(`/api/alerts?limit=${limit}`),
  acknowledgeAlert: (id) => request(`/api/alerts/${id}/acknowledge`, { method: "POST" }),
};
