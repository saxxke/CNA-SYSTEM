import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { DEFAULT_ROLE_REDIRECTS, ROLE_DISPLAY_NAMES } from '../auth/roleNavigation';
import { ShieldAlert, ArrowLeft, Home, Lock } from 'lucide-react';

export default function UnauthorizedPage() {
  const navigate = useNavigate();
  const { role, currentUser } = useAuth();

  const handleReturnHome = () => {
    const destination = (role && DEFAULT_ROLE_REDIRECTS[role]) || '/login';
    navigate(destination, { replace: true });
  };

  const roleName = (role && ROLE_DISPLAY_NAMES[role]) || 'AUTHORIZED USER';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 relative overflow-hidden select-none">
      {/* Ambient background glow */}
      <div className="absolute w-96 h-96 bg-rose-600/10 rounded-full blur-3xl pointer-events-none -top-10 -left-10"></div>
      <div className="absolute w-96 h-96 bg-amber-600/10 rounded-full blur-3xl pointer-events-none -bottom-10 -right-10"></div>

      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-xl relative z-10 text-center">
        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 mx-auto flex items-center justify-center shadow-lg shadow-rose-950/40 mb-5">
          <ShieldAlert size={32} />
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-3">
          <Lock size={11} className="text-amber-400" />
          <span>RBAC Security Boundary</span>
        </div>

        <h1 className="text-2xl font-bold text-slate-100 tracking-tight mb-2">
          Access Restricted
        </h1>

        <p className="text-xs text-slate-400 leading-relaxed mb-6">
          Your account does not have permission to access this section. 
          The requested module is restricted to specific investigative or administrative tiers.
        </p>

        {currentUser && (
          <div className="mb-6 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-left text-xs space-y-1 font-mono">
            <div className="text-[11px] text-slate-400">Authenticated Identity:</div>
            <div className="text-slate-200 font-semibold truncate">{currentUser.display_name}</div>
            <div className="text-[11px] text-indigo-400 flex items-center gap-2 pt-1 border-t border-slate-800/60 mt-1">
              <span>Role Tier:</span>
              <span className="font-bold text-slate-200">{roleName}</span>
            </div>
          </div>
        )}

        <div className="space-y-2.5">
          <button
            onClick={handleReturnHome}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg shadow-lg shadow-indigo-900/40 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Home size={14} />
            <span>Return to Authorized Dashboard</span>
          </button>

          <button
            onClick={() => navigate(-1)}
            className="w-full py-2 px-4 bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-slate-100 text-xs font-semibold rounded-lg border border-slate-700/60 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <ArrowLeft size={13} />
            <span>Go Back to Previous Page</span>
          </button>
        </div>
      </div>

      <footer className="mt-8 text-[11px] text-slate-400 font-mono text-center">
        Anweshan AI Access Control • Unauthorized operations are logged on the backend
      </footer>
    </div>
  );
}
