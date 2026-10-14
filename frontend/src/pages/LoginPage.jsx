import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { DEFAULT_ROLE_REDIRECTS } from '../auth/roleNavigation';
import { 
  Shield, Lock, User, Eye, EyeOff, Loader2, AlertCircle, 
  CheckCircle2, KeyRound, ArrowRight, Activity 
} from 'lucide-react';

const DEMO_ACCOUNTS = [
  {
    roleLabel: 'Citizen Portal',
    roleTag: 'CITIZEN',
    username: 'citizen.demo',
    password: 'DemoCitizen@2026',
    desc: 'Authorized case inquiry and tracking (CASE-001, CASE-014)',
    badgeColor: 'border-teal-500/40 text-teal-300 bg-teal-500/10'
  },
  {
    roleLabel: 'Investigating Officer',
    roleTag: 'INVESTIGATING_OFFICER',
    username: 'io.demo',
    password: 'DemoInvestigator@2026',
    desc: 'Case explorer, graph analysis, entity resolution & AI assistant',
    badgeColor: 'border-indigo-500/40 text-indigo-300 bg-indigo-500/10'
  },
  {
    roleLabel: 'IPS Officer (Supervisory)',
    roleTag: 'IPS_OFFICER',
    username: 'ips.demo',
    password: 'DemoSupervisory@2026',
    desc: 'Cross-case intelligence, bridging analytics & executive reports',
    badgeColor: 'border-amber-500/40 text-amber-300 bg-amber-500/10'
  },
  {
    roleLabel: 'Home Ministry Oversight',
    roleTag: 'HOME_MINISTRY',
    username: 'hm.demo',
    password: 'DemoOversight@2026',
    desc: 'Macro trends, regional analytics & national oversight reports',
    badgeColor: 'border-purple-500/40 text-purple-300 bg-purple-500/10'
  }
];

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, role, loading: authLoading } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Auto-redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && role) {
      const fromPath = location.state?.from?.pathname;
      const destination = fromPath && fromPath !== '/login' ? fromPath : (DEFAULT_ROLE_REDIRECTS[role] || '/dashboard');
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, role, navigate, location.state]);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setErrorMessage('');

    if (!username.trim() || !password) {
      setErrorMessage('Please provide both username and password.');
      return;
    }

    try {
      setSubmitting(true);
      const verifiedUser = await login(username.trim(), password);
      
      const fromPath = location.state?.from?.pathname;
      const destination = fromPath && fromPath !== '/login' ? fromPath : (DEFAULT_ROLE_REDIRECTS[verifiedUser.role] || '/dashboard');
      navigate(destination, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMessage(detail);
      } else if (err.response?.status === 401) {
        setErrorMessage('Invalid username or password.');
      } else {
        setErrorMessage('Authentication server unreachable. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectDemo = (account) => {
    setUsername(account.username);
    setPassword(account.password);
    setErrorMessage('');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-300">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between select-none relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-indigo-900/15 via-indigo-950/5 to-transparent pointer-events-none blur-3xl"></div>
      
      {/* Top mini banner */}
      <header className="px-6 py-4 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-md flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-sm shadow-indigo-950">
            <Activity size={18} />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-100 tracking-wider uppercase">
              PS26189 INTEL
            </span>
            <span className="text-[10px] text-slate-400 block -mt-0.5 font-medium">
              Anweshan AI Investigation & Relational Verification Network
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Auth Service Active
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 relative z-10">
        <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          
          {/* Left Column: Login Form */}
          <div className="lg:col-span-6 bg-slate-900/90 border border-slate-800/90 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl flex flex-col justify-between">
            <div>
              <div className="mb-6">
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-semibold mb-3">
                  <Shield size={12} />
                  <span>Secure Access Boundary</span>
                </div>
                <h1 className="text-xl font-bold text-slate-100 tracking-tight">
                  Sign in to Investigation Console
                </h1>
                <p className="text-xs text-slate-400 mt-1">
                  Enter official credentials. Authoritative role and access tier are strictly verified by backend RBAC.
                </p>
              </div>

              {errorMessage && (
                <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5 animate-fadeIn">
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Username
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      id="login-username-input"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="e.g. io.demo, citizen.demo"
                      className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-mono"
                      autoComplete="username"
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="login-password-input"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full pl-9 pr-10 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-all font-mono"
                      autoComplete="current-password"
                      disabled={submitting}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 cursor-pointer"
                      tabIndex={-1}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  id="login-submit-button"
                  disabled={submitting}
                  className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900/50 text-white text-xs font-bold rounded-lg shadow-lg shadow-indigo-900/40 hover:shadow-indigo-900/60 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed"
                >
                  {submitting ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      <span>Authenticating…</span>
                    </>
                  ) : (
                    <>
                      <span>Authenticate Identity</span>
                      <ArrowRight size={14} />
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800/80 text-[10px] text-slate-400 leading-relaxed">
              <span className="font-semibold text-slate-400">Security Note:</span> Role and access tier are determined exclusively by the authenticated backend identity. No client-side role parameters are accepted.
            </div>
          </div>

          {/* Right Column: Demo Accounts Quick-Fill Widget */}
          <div className="lg:col-span-6 bg-slate-900/50 border border-slate-800/80 rounded-2xl p-6 sm:p-7 flex flex-col justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <KeyRound size={15} className="text-amber-400" />
                <h2 className="text-xs font-bold text-slate-200 tracking-wider uppercase">
                  Demonstration Access Matrix
                </h2>
              </div>
              <p className="text-[11px] text-slate-400 mb-4 leading-relaxed">
                Click any persona below to auto-populate credentials for role verification. Authentication calls the live backend API.
              </p>

              <div className="space-y-2.5">
                {DEMO_ACCOUNTS.map((acc) => {
                  const isSelected = username === acc.username;
                  return (
                    <button
                      key={acc.username}
                      type="button"
                      onClick={() => handleSelectDemo(acc)}
                      className={`w-full text-left p-3 rounded-xl border transition-all cursor-pointer ${
                        isSelected 
                          ? 'bg-slate-800/90 border-indigo-500/70 shadow-md shadow-indigo-950/50 ring-1 ring-indigo-500/40' 
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/70'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                          {acc.roleLabel}
                          {isSelected && <CheckCircle2 size={13} className="text-indigo-400" />}
                        </span>
                        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase font-semibold ${acc.badgeColor}`}>
                          {acc.roleTag}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mb-1.5 line-clamp-1">
                        {acc.desc}
                      </p>
                      <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                        <span>User: <strong className="text-slate-300">{acc.username}</strong></span>
                        <span>•</span>
                        <span>Pass: <strong className="text-slate-300">••••••••</strong></span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="mt-5 p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[10px] text-slate-400">
              <span className="text-slate-300 font-semibold">Hackathon MVP:</span> All accounts use synthetic demonstration identities. Real police credentials or live citizen data are strictly excluded.
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-3 px-6 text-center text-[10px] text-slate-400 bg-slate-950/80">
        Anweshan AI Multi-Vector Relational Intelligence • Official Use Only • RBAC Enforcement Level 4
      </footer>
    </div>
  );
}
