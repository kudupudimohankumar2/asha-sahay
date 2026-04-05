import { useEffect, useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  Droplets,
  Activity,
  Mic,
  Image as ImageIcon,
  ChevronDown,
  ChevronUp,
  Clock,
  Stethoscope,
} from "lucide-react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";

const TABS = [
  { id: "summary", label: "Summary & timeline" },
  { id: "add", label: "Add health record" },
  { id: "history", label: "Visit history" },
];

function initials(name) {
  if (!name?.trim()) return "?";
  const p = name.trim().split(/\s+/);
  return p.length === 1 ? p[0].slice(0, 2).toUpperCase() : (p[0][0] + p[p.length - 1][0]).toUpperCase();
}

function parseSymptoms(row) {
  const s = row.symptoms;
  if (!s) return [];
  if (Array.isArray(s)) return s;
  try {
    const j = JSON.parse(s);
    return Array.isArray(j) ? j : [];
  } catch {
    return String(s)
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  }
}

export default function PatientDetail() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [risk, setRisk] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [observations, setObservations] = useState([]);
  const [reports, setReports] = useState([]);
  const [clinicalSummary, setClinicalSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("summary");

  const [form, setForm] = useState({
    obs_date: new Date().toISOString().slice(0, 10),
    systolic_bp: "",
    diastolic_bp: "",
    cholesterol: "",
    weight_kg: "",
    hemoglobin: "",
    symptoms: "",
    next_visit_date: "",
    notes: "",
  });
  const [voiceFile, setVoiceFile] = useState(null);
  const [pathologyFiles, setPathologyFiles] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [expanded, setExpanded] = useState({});

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getPatient(patientId),
      api.getPatientRisk(patientId),
      api.getPatientSchedule(patientId),
      api.getPatientObservations(patientId),
      api.getPatientReports(patientId),
      api.getClinicalSummary(patientId).catch(() => ({ summary: "" })),
    ])
      .then(([p, r, s, o, rep, cs]) => {
        setPatient(p);
        setRisk(r);
        setSchedule(s);
        setObservations(o);
        setReports(rep);
        setClinicalSummary(cs.summary || "");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [patientId]);

  const metrics = useMemo(() => {
    const obs = observations[0];
    const nextSched = [...(schedule || [])]
      .filter((x) => x.status !== "completed")
      .sort((a, b) => String(a.due_date).localeCompare(String(b.due_date)))[0];
    const lastSched = [...(schedule || [])]
      .filter((x) => x.status === "completed")
      .sort((a, b) => String(b.due_date).localeCompare(String(a.due_date)))[0];
    return {
      lastVisit: obs?.obs_date || lastSched?.due_date || "—",
      nextVisit: nextSched?.due_date || obs?.next_visit_date || "—",
      bp:
        obs?.systolic_bp && obs?.diastolic_bp
          ? `${obs.systolic_bp}/${obs.diastolic_bp}`
          : "—",
      hb: obs?.hemoglobin != null ? `${obs.hemoglobin}` : "—",
    };
  }, [observations, schedule]);

  const pregLabel = useMemo(() => {
    if (!patient) return "—";
    const w = patient.gestational_weeks;
    if (w == null) return "—";
    const mo = Math.floor(w / 4);
    const wr = w % 4;
    return mo > 0 ? `${mo} months ${wr} w` : `${w} weeks`;
  }, [patient]);

  const handleSubmitRecord = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveMsg(null);
    try {
      const payload = {
        obs_date: form.obs_date || undefined,
        systolic_bp: form.systolic_bp ? Number(form.systolic_bp) : undefined,
        diastolic_bp: form.diastolic_bp ? Number(form.diastolic_bp) : undefined,
        cholesterol: form.cholesterol ? Number(form.cholesterol) : undefined,
        weight_kg: form.weight_kg ? Number(form.weight_kg) : undefined,
        hemoglobin: form.hemoglobin ? Number(form.hemoglobin) : undefined,
        symptoms: form.symptoms,
        next_visit_date: form.next_visit_date || undefined,
        notes: form.notes,
      };
      await api.createObservation(patientId, payload, voiceFile, pathologyFiles);
      setSaveMsg({ type: "ok", text: "Visit saved." });
      setVoiceFile(null);
      setPathologyFiles([]);
      setForm((f) => ({
        ...f,
        symptoms: "",
        notes: "",
      }));
      load();
    } catch (err) {
      setSaveMsg({ type: "err", text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const toggleEx = (id) => setExpanded((x) => ({ ...x, [id]: !x[id] }));

  if (loading) return <LoadingSpinner message="Loading patient…" />;
  if (!patient) return <div className="text-center py-16 text-stone-500">Patient not found</div>;

  const reportsByObs = {};
  for (const r of reports || []) {
    const oid = r.observation_id;
    if (!oid) continue;
    if (!reportsByObs[oid]) reportsByObs[oid] = [];
    reportsByObs[oid].push(r);
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      <div className="flex items-start gap-4">
        <Link to="/patients" className="p-2 rounded-xl hover:bg-stone-100 mt-1">
          <ArrowLeft className="w-5 h-5 text-stone-500" />
        </Link>
        <div className="flex-1 rounded-2xl bg-gradient-to-r from-emerald-800 to-emerald-900 text-white p-6 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center text-2xl font-display font-semibold">
              {initials(patient.full_name)}
            </div>
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-display text-2xl sm:text-3xl">{patient.full_name}</h1>
                <RiskBadge risk={patient.risk_band} size="lg" />
              </div>
              <p className="text-emerald-100/90 mt-1 text-sm">
                Age {patient.age}
                {patient.husband_name ? ` · Spouse: ${patient.husband_name}` : ""} · {patient.village}
              </p>
              <p className="text-emerald-200/80 text-sm mt-2">
                Pregnancy: <span className="text-white font-medium">{pregLabel}</span>
                {patient.trimester ? ` · ${patient.trimester} trimester` : ""}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="border-b border-stone-200">
        <nav className="flex gap-1 overflow-x-auto pb-px">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap font-sans ${
                tab === id
                  ? "border-emerald-600 text-emerald-800"
                  : "border-transparent text-stone-500 hover:text-stone-800"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      {tab === "summary" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Metric icon={Calendar} label="Last visit / record" value={metrics.lastVisit} />
            <Metric icon={Clock} label="Next visit" value={metrics.nextVisit} />
            <Metric icon={Activity} label="Latest BP (mmHg)" value={metrics.bp} />
            <Metric icon={Droplets} label="Latest Hb (g/dL)" value={metrics.hb} />
          </div>

          <div className="card border-l-4 border-emerald-500 bg-emerald-50/30">
            <h3 className="text-sm font-semibold text-emerald-900 flex items-center gap-2 mb-2">
              <Stethoscope className="w-4 h-4" />
              AI clinical summary
            </h3>
            <p className="text-stone-700 text-sm leading-relaxed whitespace-pre-wrap">
              {clinicalSummary || "Generating summary…"}
            </p>
          </div>

          <div className="card">
            <h3 className="font-display text-lg text-stone-900 mb-4">Visit timeline</h3>
            <div className="space-y-4">
              {observations.length === 0 && schedule.length === 0 && (
                <p className="text-stone-500 text-sm">No visits recorded yet.</p>
              )}
              {observations.map((o, i) => (
                <div key={o.observation_id || i} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 rounded-full bg-emerald-500 ring-4 ring-emerald-100" />
                    {i < observations.length - 1 && <div className="w-0.5 flex-1 bg-stone-200 min-h-[2rem]" />}
                  </div>
                  <div className="flex-1 pb-6">
                    <p className="text-sm font-semibold text-stone-900">{o.obs_date}</p>
                    <p className="text-xs text-stone-600 mt-1">
                      BP:{" "}
                      {o.systolic_bp && o.diastolic_bp
                        ? `${o.systolic_bp}/${o.diastolic_bp}`
                        : "—"}{" "}
                      · Hb: {o.hemoglobin ?? "—"} · Wt: {o.weight_kg ?? "—"} kg
                      {o.cholesterol != null ? ` · Chol: ${o.cholesterol}` : ""}
                    </p>
                    {parseSymptoms(o).length > 0 && (
                      <p className="text-xs text-stone-500 mt-1">
                        Symptoms: {parseSymptoms(o).join(", ")}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {risk && (
            <div className="card bg-stone-50">
              <h3 className="text-sm font-semibold text-stone-800 mb-2">Risk snapshot</h3>
              <div className="flex items-center gap-3">
                <RiskBadge risk={risk.risk_band} size="lg" />
                <span className="text-sm text-stone-600">Score {risk.risk_score?.toFixed(0) ?? "—"}/100</span>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === "add" && (
        <form onSubmit={handleSubmitRecord} className="card space-y-4 max-w-2xl">
          <h3 className="font-display text-lg text-stone-900">Record a visit</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Visit date</label>
              <input
                className="input-field"
                type="date"
                value={form.obs_date}
                onChange={(e) => setForm((f) => ({ ...f, obs_date: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Next visit date</label>
              <input
                className="input-field"
                type="date"
                value={form.next_visit_date}
                onChange={(e) => setForm((f) => ({ ...f, next_visit_date: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Systolic BP</label>
              <input
                className="input-field"
                type="number"
                value={form.systolic_bp}
                onChange={(e) => setForm((f) => ({ ...f, systolic_bp: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Diastolic BP</label>
              <input
                className="input-field"
                type="number"
                value={form.diastolic_bp}
                onChange={(e) => setForm((f) => ({ ...f, diastolic_bp: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Cholesterol (mg/dL)</label>
              <input
                className="input-field"
                type="number"
                step="0.1"
                value={form.cholesterol}
                onChange={(e) => setForm((f) => ({ ...f, cholesterol: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Weight (kg)</label>
              <input
                className="input-field"
                type="number"
                step="0.1"
                value={form.weight_kg}
                onChange={(e) => setForm((f) => ({ ...f, weight_kg: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Hemoglobin (g/dL)</label>
              <input
                className="input-field"
                type="number"
                step="0.1"
                value={form.hemoglobin}
                onChange={(e) => setForm((f) => ({ ...f, hemoglobin: e.target.value }))}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Symptoms (comma-separated)</label>
              <input
                className="input-field"
                value={form.symptoms}
                onChange={(e) => setForm((f) => ({ ...f, symptoms: e.target.value }))}
                placeholder="headache, nausea…"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Notes</label>
              <textarea
                className="input-field min-h-[80px]"
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label flex items-center gap-2">
                <Mic className="w-4 h-4" />
                Voice note
              </label>
              <input
                type="file"
                accept="audio/*,.webm,.wav,.mp3"
                className="text-sm text-stone-600"
                onChange={(e) => setVoiceFile(e.target.files?.[0] || null)}
              />
            </div>
            <div>
              <label className="label flex items-center gap-2">
                <ImageIcon className="w-4 h-4" />
                Pathology reports (images/PDF)
              </label>
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                multiple
                className="text-sm text-stone-600"
                onChange={(e) => setPathologyFiles(Array.from(e.target.files || []))}
              />
            </div>
          </div>

          {saveMsg && (
            <p
              className={`text-sm px-3 py-2 rounded-lg ${
                saveMsg.type === "ok"
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-red-50 text-red-700 border border-red-200"
              }`}
            >
              {saveMsg.text}
            </p>
          )}

          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save visit"}
          </button>
        </form>
      )}

      {tab === "history" && (
        <div className="card overflow-hidden p-0">
          <div className="px-6 py-4 border-b border-stone-100 bg-stone-50">
            <h3 className="font-display text-lg text-stone-900">All visit records</h3>
          </div>
          <div className="divide-y divide-stone-100">
            {observations.length === 0 ? (
              <p className="p-8 text-center text-stone-500 text-sm">No visits yet.</p>
            ) : (
              observations.map((o) => {
                const oid = o.observation_id;
                const open = expanded[oid];
                const reps = reportsByObs[oid] || [];
                const hasVoice = !!o.voice_note_path;
                return (
                  <div key={oid} className="bg-white">
                    <button
                      type="button"
                      className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-stone-50"
                      onClick={() => toggleEx(oid)}
                    >
                      <div>
                        <p className="text-sm font-semibold text-stone-900">{o.obs_date}</p>
                        <p className="text-xs text-stone-500">
                          BP {o.systolic_bp}/{o.diastolic_bp} · Hb {o.hemoglobin ?? "—"} · Wt {o.weight_kg ?? "—"}
                        </p>
                      </div>
                      {open ? <ChevronUp className="w-5 h-5 text-stone-400" /> : <ChevronDown className="w-5 h-5 text-stone-400" />}
                    </button>
                    {open && (
                      <div className="px-4 pb-4 pl-8 space-y-4 border-t border-stone-100 bg-stone-50/50">
                        {parseSymptoms(o).length > 0 && (
                          <p className="text-sm text-stone-700">
                            <span className="font-medium">Symptoms:</span> {parseSymptoms(o).join(", ")}
                          </p>
                        )}
                        {hasVoice && (
                          <div>
                            <p className="text-xs font-medium text-stone-600 mb-1">Voice note</p>
                            <audio
                              controls
                              className="w-full max-w-md"
                              src={`/api/patients/${patientId}/observations/${oid}/voice`}
                            >
                              <track kind="captions" />
                            </audio>
                          </div>
                        )}
                        {reps.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-stone-600 mb-2">Pathology / reports</p>
                            <div className="flex flex-wrap gap-3">
                              {reps.map((r) => (
                                <a
                                  key={r.report_id}
                                  href={api.reportMediaUrl(patientId, r.report_id)}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="block rounded-lg border border-stone-200 overflow-hidden w-32 h-32 bg-stone-100 hover:ring-2 ring-emerald-400"
                                >
                                  {String(r.file_type || "").includes("pdf") ? (
                                    <div className="w-full h-full flex items-center justify-center text-xs text-stone-500 p-2">
                                      PDF
                                    </div>
                                  ) : (
                                    <img
                                      src={api.reportMediaUrl(patientId, r.report_id)}
                                      alt="Report"
                                      className="w-full h-full object-cover"
                                    />
                                  )}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4 flex items-start gap-3 shadow-sm">
      <Icon className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
      <div>
        <p className="text-xs text-stone-500 uppercase tracking-wide">{label}</p>
        <p className="text-sm font-semibold text-stone-900 mt-0.5">{value}</p>
      </div>
    </div>
  );
}
