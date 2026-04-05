import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  BarChart3,
  Users,
  AlertTriangle,
  Calendar,
  Apple,
  Baby,
  MapPin,
  Search,
  ShieldAlert,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const [village, setVillage] = useState(searchParams.get("village") || "Hosahalli");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDashboard = () => {
    if (!village.trim()) return;
    setLoading(true);
    setError(null);
    api.getDashboard(village.trim())
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadDashboard(); }, []);

  const summary = data?.summary || {};
  const risk = data?.risk_distribution || summary?.risk_distribution || {};
  const tri = summary?.trimester_distribution || {};

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Search bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input-field pl-9"
            placeholder="Enter village name..."
            value={village}
            onChange={(e) => setVillage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadDashboard()}
          />
        </div>
        <button onClick={loadDashboard} className="btn-primary">
          <BarChart3 className="w-4 h-4" />
          Load Dashboard
        </button>
      </div>

      {loading && <LoadingSpinner message="Loading village dashboard..." />}
      {error && <div className="card border-red-200 bg-red-50 text-red-700 text-sm">{error}</div>}

      {data && !loading && (
        <>
          {/* Village summary */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                {data.village || village} Dashboard
              </h2>
              <span className="text-sm text-gray-500">{data.date}</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              <SummaryCard
                icon={Users}
                label="Total Patients"
                value={summary.total_active_patients || 0}
                color="bg-primary-50 text-primary-600"
              />
              <SummaryCard
                icon={AlertTriangle}
                label="Emergency"
                value={summary.emergency_count || 0}
                color="bg-red-50 text-red-600"
              />
              <SummaryCard
                icon={ShieldAlert}
                label="High Risk"
                value={summary.high_risk_count || 0}
                color="bg-orange-50 text-orange-600"
              />
              <SummaryCard
                icon={ShieldAlert}
                label="Elevated"
                value={summary.elevated_count || 0}
                color="bg-amber-50 text-amber-600"
              />
            </div>

            {/* Trimester distribution */}
            {(tri["1st"] || tri["2nd"] || tri["3rd"]) && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Trimester Distribution</h4>
                <div className="grid grid-cols-3 gap-3">
                  {["1st", "2nd", "3rd"].map((t) => (
                    <div key={t} className="text-center p-3 rounded-xl bg-gray-50 border border-gray-100">
                      <p className="text-xl font-bold text-gray-900">{tri[t] || 0}</p>
                      <p className="text-xs text-gray-500">{t} Trimester</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk bar */}
            {summary.total_active_patients > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Risk Distribution</h4>
                <div className="flex rounded-full h-3 overflow-hidden bg-gray-100">
                  {(summary.emergency_count || 0) > 0 && (
                    <div className="bg-red-500" style={{ width: `${((summary.emergency_count || 0) / summary.total_active_patients) * 100}%` }} />
                  )}
                  {(summary.high_risk_count || 0) > 0 && (
                    <div className="bg-orange-500" style={{ width: `${((summary.high_risk_count || 0) / summary.total_active_patients) * 100}%` }} />
                  )}
                  {(summary.elevated_count || 0) > 0 && (
                    <div className="bg-amber-400" style={{ width: `${((summary.elevated_count || 0) / summary.total_active_patients) * 100}%` }} />
                  )}
                  <div className="bg-emerald-500 flex-1" />
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* High-risk queue */}
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-500" />
                High-Risk Queue
              </h3>
              {(data.high_risk_patients || []).length === 0 ? (
                <div className="text-center py-6">
                  <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <p className="text-sm text-emerald-700">No high-risk patients. Great!</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {data.high_risk_patients.map((p, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg border-l-4 ${
                        p.risk_band === "EMERGENCY" ? "border-red-500 bg-red-50" : "border-orange-500 bg-orange-50"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">{p.full_name}</p>
                          <p className="text-xs text-gray-600 mt-0.5">
                            Age: {p.age} | Week {p.gestational_weeks || "?"} | EDD: {p.edd_date || "—"}
                          </p>
                          {p.known_conditions && (
                            <p className="text-xs text-gray-500 mt-0.5">
                              {typeof p.known_conditions === "string"
                                ? (() => { try { return JSON.parse(p.known_conditions).join(", "); } catch { return p.known_conditions; } })()
                                : Array.isArray(p.known_conditions) ? p.known_conditions.join(", ") : ""}
                            </p>
                          )}
                        </div>
                        <RiskBadge risk={p.risk_band} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {(data.active_alerts || []).length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Active Alerts ({data.active_alerts.length})</h4>
                  <div className="space-y-2">
                    {data.active_alerts.slice(0, 5).map((a, i) => (
                      <div key={i} className="p-2 rounded-lg bg-red-50 border border-red-100 text-sm">
                        <span className="font-medium">{a.full_name}</span> — {a.severity}
                        <p className="text-xs text-gray-600 mt-0.5 truncate">{a.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Today's visits + Overdue */}
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary-500" />
                Today's Schedule ({(data.todays_visits || []).length} visits)
              </h3>
              {(data.todays_visits || []).length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No visits scheduled today</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {data.todays_visits.map((v, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{v.full_name}</p>
                        <p className="text-xs text-gray-500">{v.visit_type} &middot; {v.trimester}</p>
                      </div>
                      <RiskBadge risk={v.risk_band} />
                    </div>
                  ))}
                </div>
              )}

              {(data.overdue_visits || []).length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Overdue ({data.overdue_visits.length})
                  </h4>
                  <div className="space-y-2">
                    {data.overdue_visits.slice(0, 5).map((v, i) => (
                      <div key={i} className="p-2 rounded-lg bg-red-50 border border-red-100 text-sm">
                        <span className="font-medium">{v.full_name}</span> — {v.visit_type}
                        <span className="text-xs text-gray-500 ml-2">Due: {v.due_date}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Ration summary */}
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Apple className="w-4 h-4 text-amber-500" />
                Ration & Supplements
              </h3>
              {data.ration_summary ? (
                <>
                  <p className="text-sm text-gray-600 mb-3">
                    Total beneficiaries: <span className="font-semibold">{data.ration_summary.total_beneficiaries}</span>
                  </p>
                  {data.ration_summary.supplements && Object.keys(data.ration_summary.supplements).length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                            <th className="pb-2 pr-4">Supplement</th>
                            <th className="pb-2 text-right">Count</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {Object.entries(data.ration_summary.supplements).map(([name, count]) => (
                            <tr key={name} className="text-gray-700">
                              <td className="py-2 pr-4">{name}</td>
                              <td className="py-2 text-right font-medium">{count}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">No ration data available</p>
              )}
            </div>

            {/* Upcoming deliveries */}
            <div className="card">
              <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Baby className="w-4 h-4 text-pink-500" />
                Upcoming Deliveries (30 days)
              </h3>
              {(data.upcoming_deliveries || []).length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No deliveries expected in next 30 days</p>
              ) : (
                <div className="space-y-2">
                  {data.upcoming_deliveries.map((d, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-pink-50 border border-pink-100">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{d.full_name}</p>
                        <p className="text-xs text-gray-500">EDD: {d.edd_date} &middot; Week {d.gestational_weeks || "?"}</p>
                      </div>
                      <RiskBadge risk={d.risk_band} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}


function SummaryCard({ icon: Icon, label, value, color }) {
  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-gray-100">
      <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center mb-2`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}
