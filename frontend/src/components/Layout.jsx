import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Home,
  Users,
  MessageCircle,
  BarChart3,
  Menu,
  X,
  LogOut,
  Flower2,
} from "lucide-react";
import { useState, useMemo } from "react";
import { useAuth } from "../context/AuthContext";

const NAV = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/patients", icon: Users, label: "Patients" },
  { to: "/assistant", icon: MessageCircle, label: "AI Assistant" },
  { to: "/dashboard", icon: BarChart3, label: "Village dashboard" },
];

function initials(name) {
  if (!name || !name.trim()) return "?";
  const p = name.trim().split(/\s+/);
  if (p.length === 1) return p[0].slice(0, 2).toUpperCase();
  return (p[0][0] + p[p.length - 1][0]).toUpperCase();
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const title = useMemo(() => {
    const n = NAV.find((x) =>
      x.to === "/" ? location.pathname === "/" : location.pathname.startsWith(x.to)
    );
    if (location.pathname.match(/^\/patients\/[^/]+$/)) return "Patient detail";
    return n?.label || "ASHA Sahayak";
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex h-screen overflow-hidden bg-stone-50">
      <aside className="hidden lg:flex lg:flex-col lg:w-72 bg-white border-r border-stone-200 shadow-sm">
        <div className="flex items-center gap-3 px-6 py-6 border-b border-stone-100">
          <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-emerald-100 text-emerald-800 shadow-inner">
            <Flower2 className="w-6 h-6" strokeWidth={1.5} />
          </div>
          <div>
            <h1 className="font-display text-xl text-stone-900 leading-tight">🌸 ASHA Sahayak</h1>
            <p className="text-xs text-stone-500 font-sans">आशा सहायक</p>
          </div>
        </div>

        <div className="px-4 py-4 border-b border-stone-100">
          <div className="flex items-center gap-3 rounded-xl bg-stone-50 border border-stone-100 p-3">
            <div className="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center text-sm font-semibold shrink-0">
              {initials(user?.full_name || "")}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-stone-900 truncate">{user?.full_name}</p>
              <p className="text-xs text-stone-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="mt-3 w-full flex items-center justify-center gap-2 rounded-lg border border-stone-200 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-100"
                    : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-stone-100">
          <p className="text-[11px] text-stone-400 text-center font-sans">BharatBricks · Databricks</p>
        </div>
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/30" onClick={() => setOpen(false)} />
          <aside className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-xl">
            <div className="flex items-center justify-between px-5 py-5 border-b border-stone-100">
              <span className="font-display text-lg">🌸 ASHA Sahayak</span>
              <button type="button" onClick={() => setOpen(false)} className="p-1.5 rounded-lg hover:bg-stone-100">
                <X className="w-5 h-5 text-stone-500" />
              </button>
            </div>
            <div className="px-4 py-3 border-b border-stone-100">
              <p className="text-sm font-semibold text-stone-900">{user?.full_name}</p>
              <p className="text-xs text-stone-500 truncate">{user?.email}</p>
              <button
                type="button"
                onClick={() => { handleLogout(); setOpen(false); }}
                className="mt-2 text-sm text-red-600 font-medium"
              >
                Logout
              </button>
            </div>
            <nav className="px-3 py-4 space-y-1">
              {NAV.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${
                      isActive ? "bg-emerald-50 text-emerald-800" : "text-stone-600"
                    }`
                  }
                >
                  <Icon className="w-5 h-5" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center gap-4 px-4 lg:px-8 py-4 bg-white border-b border-stone-200 shrink-0 shadow-sm">
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="p-2 rounded-lg hover:bg-stone-100 lg:hidden"
          >
            <Menu className="w-5 h-5 text-stone-600" />
          </button>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] uppercase tracking-wider text-emerald-700 font-semibold font-sans">ASHA worker console</p>
            <h2 className="text-lg font-display text-stone-900 truncate">{title}</h2>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-semibold text-stone-900 leading-tight">{user?.full_name}</p>
              <p className="text-xs text-stone-500 truncate max-w-[200px]">{user?.email}</p>
            </div>
            <div
              className="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center text-sm font-semibold shadow-md"
              title={user?.full_name}
            >
              {initials(user?.full_name || "")}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
