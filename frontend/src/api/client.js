const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
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
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  getDashboard: (village) => request(`/dashboard/${encodeURIComponent(village)}`),
};
