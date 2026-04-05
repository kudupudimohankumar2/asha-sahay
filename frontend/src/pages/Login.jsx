import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, Languages, Heart, Shield } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (isAuthenticated) navigate("/", { replace: true });
  }, [isAuthenticated, navigate]);

  const [tab, setTab] = useState("signin");
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const [signInEmail, setSignInEmail] = useState("");
  const [signInPassword, setSignInPassword] = useState("");

  const [reg, setReg] = useState({
    full_name: "",
    username: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
  });

  const setR = (k) => (e) => setReg((s) => ({ ...s, [k]: e.target.value }));

  const handleSignIn = async (e) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await login(signInEmail.trim(), signInPassword);
      navigate("/", { replace: true });
    } catch (ex) {
      setErr(ex.message || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setErr(null);
    if (reg.password !== reg.confirm) {
      setErr("Passwords do not match");
      return;
    }
    if (reg.password.length < 6) {
      setErr("Password must be at least 6 characters");
      return;
    }
    setBusy(true);
    try {
      await register({
        email: reg.email.trim(),
        username: reg.username.trim(),
        full_name: reg.full_name.trim(),
        phone: reg.phone.trim(),
        password: reg.password,
      });
      navigate("/", { replace: true });
    } catch (ex) {
      setErr(ex.message || "Could not create account");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-stone-950 text-stone-100">
      <div className="lg:w-[42%] bg-gradient-to-br from-emerald-950 via-stone-900 to-stone-950 p-10 lg:p-14 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-emerald-900/40">
        <div className="max-w-md mx-auto w-full space-y-8">
          <div>
            <p className="font-display text-4xl lg:text-5xl text-emerald-100 leading-tight">
              🌸 ASHA Sahayak
            </p>
            <p className="mt-2 text-emerald-200/80 font-sans text-lg">आशा सहायक — maternal care companion</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
              <Languages className="w-6 h-6 text-emerald-400 mb-2" />
              <p className="font-semibold text-white">22+ Languages</p>
              <p className="text-xs text-stone-400 mt-1">Voice & text support</p>
            </div>
            <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
              <Sparkles className="w-6 h-6 text-amber-400 mb-2" />
              <p className="font-semibold text-white">AI powered</p>
              <p className="text-xs text-stone-400 mt-1">Risk & schedule guidance</p>
            </div>
            <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
              <Heart className="w-6 h-6 text-rose-400 mb-2" />
              <p className="font-semibold text-white">ANC aligned</p>
              <p className="text-xs text-stone-400 mt-1">PMSMA-aware schedules</p>
            </div>
            <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
              <Shield className="w-6 h-6 text-cyan-400 mb-2" />
              <p className="font-semibold text-white">Field-first</p>
              <p className="text-xs text-stone-400 mt-1">Built for ASHA workflows</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-stone-900">
        <div className="w-full max-w-md">
          <div className="flex rounded-xl bg-stone-800/80 p-1 mb-8 border border-stone-700">
            <button
              type="button"
              onClick={() => { setTab("signin"); setErr(null); }}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                tab === "signin" ? "bg-emerald-600 text-white shadow" : "text-stone-400 hover:text-white"
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => { setTab("register"); setErr(null); }}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                tab === "register" ? "bg-emerald-600 text-white shadow" : "text-stone-400 hover:text-white"
              }`}
            >
              Create account
            </button>
          </div>

          {tab === "signin" ? (
            <form onSubmit={handleSignIn} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-stone-400 mb-1.5">Email or username</label>
                <input
                  className="w-full rounded-lg bg-stone-800 border border-stone-600 px-3 py-2.5 text-stone-100 placeholder-stone-500 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                  value={signInEmail}
                  onChange={(e) => setSignInEmail(e.target.value)}
                  placeholder="demo@asha.local"
                  autoComplete="username"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-400 mb-1.5">Password</label>
                <input
                  type="password"
                  className="w-full rounded-lg bg-stone-800 border border-stone-600 px-3 py-2.5 text-stone-100 placeholder-stone-500 focus:ring-2 focus:ring-emerald-500 outline-none"
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
              </div>
              {err && <p className="text-sm text-red-400 bg-red-950/50 border border-red-900/50 rounded-lg px-3 py-2">{err}</p>}
              <button
                type="submit"
                disabled={busy}
                className="w-full py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold disabled:opacity-50"
              >
                {busy ? "Signing in…" : "Sign in"}
              </button>
              <p className="text-xs text-stone-500 text-center">
                Demo: <span className="text-stone-400">demo@asha.local</span> / <span className="text-stone-400">demo123</span>
              </p>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-stone-400 mb-1">Full name</label>
                <input className="input-dark" value={reg.full_name} onChange={setR("full_name")} required />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-stone-400 mb-1">Username</label>
                  <input className="input-dark" value={reg.username} onChange={setR("username")} required />
                </div>
                <div>
                  <label className="block text-xs font-medium text-stone-400 mb-1">Phone (optional)</label>
                  <input className="input-dark" value={reg.phone} onChange={setR("phone")} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-400 mb-1">Email</label>
                <input type="email" className="input-dark" value={reg.email} onChange={setR("email")} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-400 mb-1">Password</label>
                <input type="password" className="input-dark" value={reg.password} onChange={setR("password")} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-stone-400 mb-1">Confirm password</label>
                <input type="password" className="input-dark" value={reg.confirm} onChange={setR("confirm")} required />
              </div>
              {err && <p className="text-sm text-red-400 bg-red-950/50 border border-red-900/50 rounded-lg px-3 py-2">{err}</p>}
              <button
                type="submit"
                disabled={busy}
                className="w-full py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold disabled:opacity-50"
              >
                {busy ? "Creating…" : "Create account"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
