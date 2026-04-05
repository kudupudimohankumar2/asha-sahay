import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Users,
  AlertTriangle,
  CalendarClock,
  Baby,
  ChevronRight,
  MapPin,
  UserPlus,
  Plus,
  X,
} from "lucide-react";
import { api } from "../api/client";
import StatCard from "../components/StatCard";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";

const LANGUAGES = [
  { code: "hi", label: "Hindi" },
  { code: "en", label: "English" },
  { code: "te", label: "Telugu" },
];

function formatPregnancy(weeks) {
  if (weeks == null) return "—";
  const mo = Math.floor(weeks / 4);
  const w = weeks % 4;
  if (mo > 0) return `${mo} mo ${w} w`;
  return `${weeks} w`;
}

export default function Home() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formMsg, setFormMsg] = useState(null);
  const [formState, setFormState] = useState(() => ({
    full_name: "",
    husband_name: "",
    age: 25,
    village: "Hosahalli",
    phone: "",
    language_preference: "hi",
    lmp_date: "",
    gravida: 1,
    parity: 0,
    blood_group: "Unknown",
    known_conditions: "",
    current_medications: "",
  }));

  const load = () => {
    setLoading(true);
    Promise.all([api.getStats(), api.getPatients()])
      .then(([s, p]) => {
        setStats(s);
        setPatients(p);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const set = (k) => (e) => setFormState((x) => ({ ...x, [k]: e.target.value }));

  const handleCreatePatient = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormMsg(null);
    try {
      const data = {
        ...formState,
        age: Number(formState.age),
        gravida: Number(formState.gravida),
        parity: Number(formState.parity),
        known_conditions: formState.known_conditions
          ? formState.known_conditions.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
        current_medications: formState.current_medications
          ? formState.current_medications.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
      };
      const created = await api.createPatient(data);
      setFormMsg({ type: "success", text: `${created.full_name} registered.` });
      setFormState((s) => ({
        ...s,
        full_name: "",
        husband_name: "",
        lmp_date: "",
      }));
      load();
      setTimeout(() => setShowAdd(false), 1500);
    } catch (err) {
      setFormMsg({ type: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading dashboard…" />;

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-stone-900">Village dashboard</h1>
          <p className="text-sm text-stone-500 mt-1 font-sans">
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowAdd(!showAdd)}
          className="btn-primary self-start"
        >
          {showAdd ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showAdd ? "Close form" : "Add new patient"}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Total patients"
          value={stats?.total_patients ?? 0}
          color="primary"
        />
        <StatCard
          icon={AlertTriangle}
          label="High-risk cases"
          value={stats?.high_risk_cases ?? stats?.need_attention ?? 0}
          color="red"
          sub="Emergency + high risk"
        />
        <StatCard
          icon={CalendarClock}
          label="Actions pending"
          value={stats?.actions_pending ?? 0}
          color="amber"
          sub="Overdue visits"
        />
        <StatCard
          icon={Baby}
          label="Deliveries (EDD this month)"
          value={stats?.deliveries_this_month ?? 0}
          color="primary"
          sub="Expected due dates"
        />
      </div>

      {showAdd && (
        <div className="card border-emerald-100 bg-emerald-50/30 animate-slide-up">
          <h3 className="text-lg font-display text-stone-900 mb-4 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-emerald-600" />
            Register new patient
          </h3>
          <form onSubmit={handleCreatePatient} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Full name *</label>
                <input className="input-field" value={formState.full_name} onChange={set("full_name")} required />
              </div>
              <div>
                <label className="label">Husband&apos;s name</label>
                <input className="input-field" value={formState.husband_name} onChange={set("husband_name")} />
              </div>
              <div>
                <label className="label">Age *</label>
                <input className="input-field" type="number" min="14" max="50" value={formState.age} onChange={set("age")} required />
              </div>
              <div>
                <label className="label">Village *</label>
                <input className="input-field" value={formState.village} onChange={set("village")} required />
              </div>
              <div>
                <label className="label">LMP * (for pregnancy duration)</label>
                <input className="input-field" type="date" value={formState.lmp_date} onChange={set("lmp_date")} required />
              </div>
              <div>
                <label className="label">Phone</label>
                <input className="input-field" value={formState.phone} onChange={set("phone")} />
              </div>
              <div>
                <label className="label">Language</label>
                <select className="input-field" value={formState.language_preference} onChange={set("language_preference")}>
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>{l.label}</option>
                  ))}
                </select>
              </div>
            </div>
            {formMsg && (
              <div
                className={`p-3 rounded-lg text-sm ${
                  formMsg.type === "success"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-red-50 text-red-700 border border-red-200"
                }`}
              >
                {formMsg.text}
              </div>
            )}
            <div className="flex justify-end">
              <button type="submit" className="btn-primary" disabled={submitting}>
                {submitting ? "Saving…" : "Save patient"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card overflow-hidden p-0">
        <div className="px-6 py-4 border-b border-stone-100 flex items-center justify-between bg-stone-50/80">
          <h2 className="font-display text-lg text-stone-900">Patient queue</h2>
          <span className="text-xs text-stone-500">{patients.length} women</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-stone-500 border-b border-stone-100 bg-white">
                <th className="px-4 py-3 font-semibold">Name</th>
                <th className="px-4 py-3 font-semibold">Age</th>
                <th className="px-4 py-3 font-semibold">Husband</th>
                <th className="px-4 py-3 font-semibold">Village</th>
                <th className="px-4 py-3 font-semibold">Pregnancy</th>
                <th className="px-4 py-3 font-semibold">Risk</th>
                <th className="px-4 py-3 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {patients.map((p) => (
                <tr
                  key={p.patient_id}
                  className="hover:bg-emerald-50/40 cursor-pointer transition-colors"
                  onClick={() => navigate(`/patients/${p.patient_id}`)}
                >
                  <td className="px-4 py-3 font-medium text-stone-900">{p.full_name}</td>
                  <td className="px-4 py-3 text-stone-600">{p.age}</td>
                  <td className="px-4 py-3 text-stone-600">{p.husband_name || "—"}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-stone-600">
                      <MapPin className="w-3.5 h-3.5" />
                      {p.village}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-stone-600">{formatPregnancy(p.gestational_weeks)}</td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <RiskBadge risk={p.risk_band} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <ChevronRight className="w-4 h-4 text-stone-400 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {patients.length === 0 && (
          <p className="text-center text-stone-500 py-10">No patients yet — add one above.</p>
        )}
      </div>

      {stats?.village_names?.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-stone-900 mb-3">Quick village views</h3>
          <div className="flex flex-wrap gap-2">
            {stats.village_names.map((v) => (
              <Link
                key={v}
                to={`/dashboard?village=${encodeURIComponent(v)}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-stone-100 text-sm text-stone-700 hover:bg-emerald-50 hover:text-emerald-800"
              >
                {v}
                <ChevronRight className="w-3 h-3" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
