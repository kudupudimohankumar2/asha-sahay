const BASE = "/api";
const TOKEN_KEY = "asha_token";

function authHeaders(extra = {}) {
  const t = localStorage.getItem(TOKEN_KEY);
  const h = { ...extra };
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

async function request(path, options = {}) {
  const isJson = !(options.body instanceof FormData);
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: isJson
      ? { "Content-Type": "application/json", ...authHeaders(), ...options.headers }
      : { ...authHeaders(), ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = Array.isArray(err.detail)
      ? err.detail.map((d) => d.msg || d).join(", ")
      : err.detail || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  register: (body) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (emailOrUsername, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email_or_username: emailOrUsername, password }),
    }),
  me: () => request("/auth/me"),

  getStats: () => request("/stats"),
  getAlerts: () => request("/alerts"),
  getTodayVisits: () => request("/schedule/today"),
  getOverdueVisits: () => request("/schedule/overdue"),

  getPatients: (search, village) => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (village) params.set("village", village);
    const qs = params.toString();
    return request(`/patients${qs ? `?${qs}` : ""}`);
  },
  createPatient: (data) =>
    request("/patients", { method: "POST", body: JSON.stringify(data) }),
  getPatient: (id) => request(`/patients/${id}`),
  getPatientRisk: (id) => request(`/patients/${id}/risk`),
  getPatientSchedule: (id) => request(`/patients/${id}/schedule`),
  getPatientRation: (id) => request(`/patients/${id}/ration`),
  getPatientObservations: (id) => request(`/patients/${id}/observations`),
  getClinicalSummary: (id) => request(`/patients/${id}/clinical-summary`),
  getPatientReports: (id) => request(`/patients/${id}/reports`),

  /** Multipart: payload JSON string + optional voice file + pathology files */
  createObservation: async (patientId, payloadObj, voiceFile, pathologyFiles) => {
    const form = new FormData();
    form.append("payload", JSON.stringify(payloadObj));
    if (voiceFile) form.append("voice", voiceFile);
    for (const f of pathologyFiles || []) {
      form.append("pathology", f);
    }
    const res = await fetch(`${BASE}/patients/${patientId}/observations`, {
      method: "POST",
      body: form,
      headers: authHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  reportMediaUrl: (patientId, reportId) =>
    `${BASE}/patients/${patientId}/reports/${reportId}/media`,

  chat: (patientId, data) =>
    request(`/patients/${patientId}/chat`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  uploadDocument: async (patientId, file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/patients/${patientId}/documents`, {
      method: "POST",
      body: form,
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  getDashboard: (village) => request(`/dashboard/${encodeURIComponent(village)}`),
};
