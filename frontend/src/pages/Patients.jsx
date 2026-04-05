import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  Plus,
  X,
  UserPlus,
  ChevronRight,
  Calendar,
  MapPin,
} from "lucide-react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

const LANGUAGES = [
  { code: "hi", label: "Hindi" },
  { code: "en", label: "English" },
  { code: "kn", label: "Kannada" },
  { code: "te", label: "Telugu" },
  { code: "ta", label: "Tamil" },
  { code: "mr", label: "Marathi" },
  { code: "bn", label: "Bengali" },
  { code: "gu", label: "Gujarati" },
  { code: "ml", label: "Malayalam" },
  { code: "pa", label: "Punjabi" },
];

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formState, setFormState] = useState(initialForm());
  const [submitting, setSubmitting] = useState(false);
  const [formMsg, setFormMsg] = useState(null);

  function initialForm() {
    return {
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
    };
  }

  const loadPatients = (q) => {
    setLoading(true);
    api.getPatients(q || undefined)
      .then(setPatients)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadPatients(); }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    loadPatients(search);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormMsg(null);
    try {
      const data = {
        ...formState,
        husband_name: (formState.husband_name || "").trim(),
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
      setFormMsg({ type: "success", text: `${created.full_name} registered! EDD: ${created.edd_date}, Trimester: ${created.trimester}` });
      setFormState(initialForm());
      loadPatients();
      setTimeout(() => setShowForm(false), 2000);
    } catch (err) {
      setFormMsg({ type: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const set = (k) => (e) => setFormState((s) => ({ ...s, [k]: e.target.value }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-sm text-gray-500 mt-0.5">{patients.length} registered patients</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? "Close" : "Register Patient"}
        </button>
      </div>

      {/* Registration form */}
      {showForm && (
        <div className="card animate-slide-up">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-primary-600" />
            Register New Patient
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Full Name *</label>
                <input className="input-field" value={formState.full_name} onChange={set("full_name")} placeholder="e.g., Lakshmi Devi" required />
              </div>
              <div>
                <label className="label">Husband&apos;s name</label>
                <input className="input-field" value={formState.husband_name} onChange={set("husband_name")} placeholder="Optional" />
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
                <label className="label">Phone</label>
                <input className="input-field" value={formState.phone} onChange={set("phone")} placeholder="98XXXXXXXX" />
              </div>
              <div>
                <label className="label">Last Menstrual Period (LMP) *</label>
                <input className="input-field" type="date" value={formState.lmp_date} onChange={set("lmp_date")} required />
              </div>
              <div>
                <label className="label">Language</label>
                <select className="input-field" value={formState.language_preference} onChange={set("language_preference")}>
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>{l.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Gravida</label>
                <input className="input-field" type="number" min="1" value={formState.gravida} onChange={set("gravida")} />
              </div>
              <div>
                <label className="label">Parity</label>
                <input className="input-field" type="number" min="0" value={formState.parity} onChange={set("parity")} />
              </div>
              <div>
                <label className="label">Blood Group</label>
                <select className="input-field" value={formState.blood_group} onChange={set("blood_group")}>
                  {["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((g) => (
                    <option key={g} value={g}>{g}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Known Conditions</label>
                <input className="input-field" value={formState.known_conditions} onChange={set("known_conditions")} placeholder="e.g., anemia, prior c-section" />
              </div>
              <div className="sm:col-span-2">
                <label className="label">Current Medications</label>
                <input className="input-field" value={formState.current_medications} onChange={set("current_medications")} placeholder="e.g., IFA tablet, calcium" />
              </div>
            </div>

            {formMsg && (
              <div className={`p-3 rounded-lg text-sm ${
                formMsg.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"
              }`}>
                {formMsg.text}
              </div>
            )}

            <div className="flex justify-end">
              <button type="submit" className="btn-primary" disabled={submitting}>
                {submitting ? "Registering..." : "Register Patient"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input-field pl-9"
            placeholder="Search by name, village, or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-secondary">Search</button>
      </form>

      {/* Patient list */}
      {loading ? (
        <LoadingSpinner message="Loading patients..." />
      ) : patients.length === 0 ? (
        <EmptyState title="No patients found" description="Try a different search or register a new patient." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {patients.map((p) => (
            <Link
              key={p.patient_id}
              to={`/patients/${p.patient_id}`}
              className="card hover:shadow-md hover:border-primary-200 transition-all group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-semibold text-gray-900 group-hover:text-primary-700 transition-colors">
                    {p.full_name}
                  </h3>
                  <p className="text-sm text-gray-500 mt-0.5">Age: {p.age}</p>
                </div>
                <RiskBadge risk={p.risk_band} />
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                {p.husband_name && (
                  <span className="text-gray-600">Spouse: {p.husband_name}</span>
                )}
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" /> {p.village}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> {p.trimester || "—"} trimester
                </span>
                <span>{p.gestational_weeks ? `${p.gestational_weeks}w` : "—"}</span>
              </div>

              {p.edd_date && (
                <p className="mt-2 text-xs text-gray-400">EDD: {p.edd_date}</p>
              )}

              <div className="mt-3 flex items-center justify-end text-xs text-primary-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                View Details <ChevronRight className="w-3 h-3 ml-0.5" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
