import { Outlet, NavLink, useLocation } from "react-router-dom";
import {
  Home,
  Users,
  MessageCircle,
  BarChart3,
  Heart,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

const NAV = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/patients", icon: Users, label: "Patients" },
  { to: "/assistant", icon: MessageCircle, label: "AI Assistant" },
  { to: "/dashboard", icon: BarChart3, label: "Dashboard" },
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar — desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-gray-200">
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary-100 text-primary-700">
            <Heart className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">ASHA Sahayak</h1>
            <p className="text-xs text-gray-500">आशा सहायक</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-50 text-primary-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">
            Built for BharatBricks Hackathon
          </p>
          <p className="text-xs text-gray-400 text-center mt-0.5">
            Powered by Databricks
          </p>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/30" onClick={() => setOpen(false)} />
          <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl animate-fade-in">
            <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary-100 text-primary-700">
                  <Heart className="w-5 h-5" />
                </div>
                <h1 className="text-lg font-bold text-gray-900">ASHA Sahayak</h1>
              </div>
              <button onClick={() => setOpen(false)} className="p-1.5 rounded-lg hover:bg-gray-100">
                <X className="w-5 h-5 text-gray-500" />
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
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-primary-50 text-primary-700"
                        : "text-gray-600 hover:bg-gray-100"
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

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-4 px-4 lg:px-8 py-4 bg-white border-b border-gray-200 shrink-0">
          <button
            onClick={() => setOpen(true)}
            className="p-2 rounded-lg hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">
              {NAV.find((n) => (n.to === "/" ? location.pathname === "/" : location.pathname.startsWith(n.to)))?.label ||
                "Patient Detail"}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden sm:inline text-xs text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
              Demo Mode
            </span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
