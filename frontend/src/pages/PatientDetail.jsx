import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Heart,
  ShieldAlert,
  Calendar,
  Apple,
  FileText,
  Upload,
  Phone,
  MapPin,
  Droplets,
  Baby,
  Clock,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";

const TABS = [
  { id: "profile", icon: Heart, label: "Profile" },
  { id: "risk", icon: ShieldAlert, label: "Risk" },
  { id: "schedule", icon: Calendar, label: "Schedule" },
  { id: "ration", icon: Apple, label: "Nutrition" },
  { id: "reports", icon: FileText, label: "Reports" },
];

export default function PatientDetail() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [risk, setRisk] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [ration, setRation] = useState(null);
  const [observations, setObservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("profile");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getPatient(patientId),
      api.getPatientRisk(patientId),
      api.getPatientSchedule(patientId),
      api.getPatientRation(patientId),
      api.getPatientObservations(patientId),
    ])
      .then(([p, r, s, ra, o]) => {
        setPatient(p);
        setRisk(r);
        setSchedule(s);
        setRation(ra);
        setObservations(o);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [patientId]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const result = await api.uploadDocument(patientId, file);
      setUploadResult(result);
    } catch (err) {
      setUploadResult({ error: err.message });
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading patient details..." />;
  if (!patient) return <div className="text-center py-16 text-gray-500">Patient not found</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + Header */}
      <div className="flex items-center gap-3">
        <Link to="/patients" className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
          <ArrowLeft className="w-5 h-5 text-gray-500" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{patient.full_name}</h1>
            <RiskBadge risk={patient.risk_band} size="lg" />
          </div>
          <p className="text-sm text-gray-500 mt-0.5">{patient.village} &middot; Age {patient.age}</p>
        </div>
        {risk?.emergency_flag && (
          <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-lg bg-red-100 border border-red-200">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-sm font-semibold text-red-700">Emergency</span>
          </div>
        )}
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <QuickStat icon={Calendar} label="EDD" value={patient.edd_date || "—"} />
        <QuickStat icon={Clock} label="Gestational Age" value={patient.gestational_weeks ? `${patient.gestational_weeks} weeks` : "—"} />
        <QuickStat icon={Baby} label="Trimester" value={patient.trimester || "—"} />
        <QuickStat icon={Droplets} label="Blood Group" value={patient.blood_group || "—"} />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 -mx-4 lg:-mx-8 px-4 lg:px-8">
        <nav className="flex gap-1 overflow-x-auto">
          {TABS.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                tab === id
                  ? "border-primary-600 text-primary-700"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {tab === "profile" && <ProfileTab patient={patient} observations={observations} />}
        {tab === "risk" && <RiskTab risk={risk} />}
        {tab === "schedule" && <ScheduleTab schedule={schedule} />}
        {tab === "ration" && <RationTab ration={ration} />}
        {tab === "reports" && (
          <ReportsTab
            uploading={uploading}
            uploadResult={uploadResult}
            onUpload={handleUpload}
          />
        )}
      </div>
    </div>
  );
}

function QuickStat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-white border border-gray-200">
      <Icon className="w-5 h-5 text-gray-400 shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-semibold text-gray-900 truncate">{value}</p>
      </div>
    </div>
  );
}


function ProfileTab({ patient, observations }) {
  const fields = [
    ["Phone", patient.phone || "—", Phone],
    ["Village", patient.village, MapPin],
    ["Language", patient.language_preference?.toUpperCase()],
    ["Gravida", patient.gravida],
    ["Parity", patient.parity],
    ["LMP Date", patient.lmp_date || "—"],
    ["EDD", patient.edd_date || "—"],
    ["Risk Score", patient.risk_score?.toFixed(0) + "/100"],
  ];

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Patient Information</h3>
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {fields.map(([label, val]) => (
            <div key={label}>
              <dt className="text-xs text-gray-500">{label}</dt>
              <dd className="text-sm font-medium text-gray-900 mt-0.5">{val}</dd>
            </div>
          ))}
        </dl>
      </div>

      {patient.known_conditions?.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Known Conditions</h3>
          <div className="flex flex-wrap gap-2">
            {patient.known_conditions.map((c, i) => (
              <span key={i} className="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-sm border border-amber-200">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {patient.current_medications?.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Current Medications</h3>
          <div className="flex flex-wrap gap-2">
            {patient.current_medications.map((m, i) => (
              <span key={i} className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm border border-blue-200">
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {observations.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Latest Observations</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                  <th className="pb-2 pr-4">Date</th>
                  <th className="pb-2 pr-4">Hb (g/dL)</th>
                  <th className="pb-2 pr-4">BP (mmHg)</th>
                  <th className="pb-2 pr-4">Weight (kg)</th>
                  <th className="pb-2 pr-4">Fetal Movement</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {observations.slice(0, 5).map((o, i) => (
                  <tr key={i} className="text-gray-700">
                    <td className="py-2 pr-4 font-medium">{o.obs_date || "—"}</td>
                    <td className="py-2 pr-4">{o.hemoglobin ?? "—"}</td>
                    <td className="py-2 pr-4">{o.systolic_bp && o.diastolic_bp ? `${o.systolic_bp}/${o.diastolic_bp}` : "—"}</td>
                    <td className="py-2 pr-4">{o.weight_kg ?? "—"}</td>
                    <td className="py-2 pr-4">{o.fetal_movement || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}


function RiskTab({ risk }) {
  if (!risk) return <p className="text-gray-500">No risk data available</p>;

  return (
    <div className="space-y-6">
      {/* Risk summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-900">Risk Assessment</h3>
          <RiskBadge risk={risk.risk_band} size="lg" />
        </div>
        <div className="flex items-center gap-6">
          <div>
            <p className="text-3xl font-bold text-gray-900">{risk.risk_score?.toFixed(0)}</p>
            <p className="text-xs text-gray-500">Risk Score (0-100)</p>
          </div>
          <div className="flex-1">
            <div className="h-3 rounded-full bg-gray-100 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  risk.risk_score > 70 ? "bg-red-500" : risk.risk_score > 40 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${Math.min(risk.risk_score, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Emergency banner */}
      {risk.emergency_flag && (
        <div className="p-4 rounded-xl bg-red-50 border-2 border-red-200">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <h4 className="text-base font-bold text-red-700">Emergency Action Required</h4>
          </div>
          <p className="text-sm text-red-700">{risk.suggested_next_action}</p>
        </div>
      )}

      {/* Triggered rules */}
      {risk.triggered_rules?.length > 0 ? (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Triggered Rules ({risk.triggered_rules.length})</h3>
          <div className="space-y-3">
            {risk.triggered_rules.map((rule, i) => {
              const sevColor = rule.severity === "EMERGENCY" ? "border-red-400 bg-red-50" :
                rule.severity === "HIGH_RISK" ? "border-orange-400 bg-orange-50" :
                "border-amber-300 bg-amber-50";
              return (
                <div key={i} className={`p-4 rounded-lg border-l-4 ${sevColor}`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900">{rule.name}</h4>
                      <p className="text-xs text-gray-600 mt-1">{rule.details}</p>
                    </div>
                    <span className="text-xs font-medium text-gray-500">{rule.severity}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Action: {rule.action}</p>
                  {rule.source_ref && (
                    <p className="text-xs text-gray-400 mt-1">Source: {rule.source_ref}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="card text-center py-8">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
          <p className="text-sm text-emerald-700 font-medium">No risk flags detected</p>
          <p className="text-xs text-gray-500 mt-1">Continue routine care</p>
        </div>
      )}
    </div>
  );
}


function ScheduleTab({ schedule }) {
  if (!schedule?.length)
    return <p className="text-sm text-gray-500 text-center py-8">No schedule generated yet</p>;

  const statusIcon = (s) => {
    if (s === "completed") return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
    if (s === "overdue") return <AlertCircle className="w-4 h-4 text-red-500" />;
    return <Clock className="w-4 h-4 text-blue-500" />;
  };

  return (
    <div className="card">
      <h3 className="text-base font-semibold text-gray-900 mb-4">ANC Schedule</h3>
      <div className="space-y-3">
        {schedule.map((entry, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 p-4 rounded-lg border transition-colors ${
              entry.status === "overdue"
                ? "border-red-200 bg-red-50/50"
                : entry.status === "completed"
                ? "border-emerald-200 bg-emerald-50/50"
                : "border-gray-200 bg-gray-50/50"
            }`}
          >
            <div className="mt-0.5">{statusIcon(entry.status)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-semibold text-gray-900">{entry.visit_type}</h4>
                {entry.is_pmsma_aligned && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">PMSMA</span>
                )}
                {entry.escalation_flag && (
                  <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Escalation</span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-1">Due: {entry.due_date} &middot; Status: {entry.status}</p>
              {entry.tests_due?.length > 0 && (
                <p className="text-xs text-gray-400 mt-1">Tests: {entry.tests_due.join(", ")}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


function RationTab({ ration }) {
  if (!ration) return <p className="text-sm text-gray-500 text-center py-8">No ration data available</p>;

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Weekly Nutrition Recommendation</h3>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 rounded-xl bg-primary-50">
            <p className="text-xl font-bold text-primary-700">{ration.calorie_target}</p>
            <p className="text-xs text-primary-600">cal/day</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-blue-50">
            <p className="text-xl font-bold text-blue-700">{ration.protein_target_g}g</p>
            <p className="text-xs text-blue-600">protein/day</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-gray-50">
            <p className="text-xl font-bold text-gray-700">{ration.week_start}</p>
            <p className="text-xs text-gray-500">week start</p>
          </div>
        </div>

        {ration.ration_items?.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                  <th className="pb-2 pr-4">Item</th>
                  <th className="pb-2 pr-4">Quantity</th>
                  <th className="pb-2 pr-4">Frequency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {ration.ration_items.map((item, i) => (
                  <tr key={i} className="text-gray-700">
                    <td className="py-2.5 pr-4 font-medium">{item.item_name}</td>
                    <td className="py-2.5 pr-4">{item.quantity} {item.unit}</td>
                    <td className="py-2.5 pr-4">{item.frequency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {ration.supplements?.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Supplements</h3>
          <div className="flex flex-wrap gap-2">
            {ration.supplements.map((s, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-sm border border-emerald-200">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {ration.special_adjustments?.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-gray-900 mb-3">Special Adjustments</h3>
          <ul className="space-y-2">
            {ration.special_adjustments.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      {ration.rule_basis?.length > 0 && (
        <div className="card bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Rule Basis</h3>
          <p className="text-xs text-gray-500">{ration.rule_basis.join(" | ")}</p>
        </div>
      )}
    </div>
  );
}


function ReportsTab({ uploading, uploadResult, onUpload }) {
  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Upload Report</h3>
        <label className={`flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
          uploading ? "border-primary-300 bg-primary-50" : "border-gray-300 bg-gray-50 hover:border-primary-400 hover:bg-primary-50"
        }`}>
          <Upload className={`w-8 h-8 mb-2 ${uploading ? "text-primary-500 animate-pulse" : "text-gray-400"}`} />
          <span className="text-sm text-gray-600">
            {uploading ? "Processing..." : "Click to upload PDF or image"}
          </span>
          <span className="text-xs text-gray-400 mt-1">PDF, JPG, PNG supported</span>
          <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={onUpload} disabled={uploading} />
        </label>
      </div>

      {uploadResult && (
        <div className={`card ${uploadResult.error ? "border-red-200" : "border-emerald-200"}`}>
          {uploadResult.error ? (
            <p className="text-sm text-red-700">{uploadResult.error}</p>
          ) : (
            <>
              <h3 className="text-base font-semibold text-gray-900 mb-2">
                Report Processed ({((uploadResult.confidence || 0) * 100).toFixed(0)}% confidence)
              </h3>
              {uploadResult.abnormality_flags?.length > 0 && (
                <div className="space-y-1 mb-3">
                  {uploadResult.abnormality_flags.map((flag, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-red-700">
                      <AlertCircle className="w-4 h-4" /> {flag}
                    </div>
                  ))}
                </div>
              )}
              {uploadResult.extraction?.findings && (
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(uploadResult.extraction.findings).map(([k, v]) => (
                    <div key={k} className="p-2 rounded-lg bg-gray-50">
                      <p className="text-xs text-gray-500">{k}</p>
                      <p className="text-sm font-medium text-gray-900">{v}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
