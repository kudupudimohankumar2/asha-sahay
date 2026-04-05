import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Calendar,
  Clock,
  ChevronRight,
  MapPin,
  Activity,
} from "lucide-react";
import { api } from "../api/client";
import StatCard from "../components/StatCard";
import RiskBadge from "../components/RiskBadge";
import LoadingSpinner from "../components/LoadingSpinner";

export default function Home() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [todayVisits, setTodayVisits] = useState([]);
  const [overdueVisits, setOverdueVisits] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getStats(),
      api.getAlerts(),
      api.getTodayVisits(),
      api.getOverdueVisits(),
    ])
      .then(([s, a, t, o]) => {
        setStats(s);
        setAlerts(a);
        setTodayVisits(t);
        setOverdueVisits(o);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading dashboard..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Date header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>
        </div>
        <Link to="/patients" className="btn-primary">
          <Users className="w-4 h-4" />
          View Patients
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Active Patients" value={stats?.total_patients || 0} color="primary" />
        <StatCard icon={ShieldAlert} label="Need Attention" value={stats?.need_attention || 0} color="red" sub="Emergency + High Risk" />
        <StatCard icon={AlertTriangle} label="Elevated Risk" value={stats?.elevated || 0} color="amber" />
        <StatCard icon={ShieldCheck} label="Normal" value={stats?.normal || 0} color="emerald" />
      </div>

      {/* Risk Distribution Bar */}
      {stats && stats.total_patients > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Risk Distribution</h3>
          <div className="flex rounded-full h-3 overflow-hidden bg-gray-100">
            {stats.emergency > 0 && (
              <div className="bg-red-500 transition-all" style={{ width: `${(stats.emergency / stats.total_patients) * 100}%` }} />
            )}
            {stats.high_risk > 0 && (
              <div className="bg-orange-500 transition-all" style={{ width: `${(stats.high_risk / stats.total_patients) * 100}%` }} />
            )}
            {stats.elevated > 0 && (
              <div className="bg-amber-400 transition-all" style={{ width: `${(stats.elevated / stats.total_patients) * 100}%` }} />
            )}
            {stats.normal > 0 && (
              <div className="bg-emerald-500 transition-all" style={{ width: `${(stats.normal / stats.total_patients) * 100}%` }} />
            )}
          </div>
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Emergency ({stats.emergency})</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" />High Risk ({stats.high_risk})</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" />Elevated ({stats.elevated})</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Normal ({stats.normal})</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Active Alerts
            </h3>
            <span className="text-xs text-gray-400">{alerts.length} total</span>
          </div>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">No active alerts — all clear!</p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {alerts.slice(0, 6).map((a, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    a.severity === "EMERGENCY" || a.severity === "CRITICAL"
                      ? "border-red-200 bg-red-50"
                      : "border-amber-200 bg-amber-50"
                  }`}
                >
                  <Activity className={`w-4 h-4 mt-0.5 shrink-0 ${
                    a.severity === "EMERGENCY" ? "text-red-500" : "text-amber-500"
                  }`} />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900">{a.full_name}</p>
                    <p className="text-xs text-gray-600 mt-0.5 truncate">{a.message}</p>
                  </div>
                  <RiskBadge risk={a.severity === "CRITICAL" ? "EMERGENCY" : a.severity} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Today's Visits */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-primary-500" />
              Today's Visits
            </h3>
            <span className="text-xs text-gray-400">{todayVisits.length} scheduled</span>
          </div>
          {todayVisits.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">No visits scheduled for today</p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {todayVisits.slice(0, 6).map((v, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{v.visit_type}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Tests: {(v.tests_due || []).slice(0, 2).join(", ")}
                      {(v.tests_due || []).length > 2 ? "..." : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {v.is_pmsma_aligned && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">PMSMA</span>
                    )}
                    {v.escalation_flag && (
                      <span className="w-2 h-2 rounded-full bg-red-500" title="Escalation required" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Overdue */}
      {overdueVisits.length > 0 && (
        <div className="card border-red-200 bg-red-50/30">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-red-700 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Overdue Visits
            </h3>
            <span className="text-xs font-medium text-red-500">{overdueVisits.length} overdue</span>
          </div>
          <div className="space-y-2">
            {overdueVisits.slice(0, 4).map((v, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white border border-red-100">
                <div>
                  <p className="text-sm font-medium text-gray-900">{v.visit_type}</p>
                  <p className="text-xs text-gray-500">Due: {v.due_date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick links — Villages */}
      {stats?.village_names?.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary-500" />
            Villages
          </h3>
          <div className="flex flex-wrap gap-2">
            {stats.village_names.map((v) => (
              <Link
                key={v}
                to={`/dashboard?village=${encodeURIComponent(v)}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gray-100 text-sm text-gray-700 hover:bg-primary-50 hover:text-primary-700 transition-colors"
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
