import React from 'react';
import { useAuth } from '../auth/AuthContext';
import { ROLE_DISPLAY_NAMES, ROLE_BADGE_COLORS } from '../auth/roleNavigation';
import { User, Shield, MapPin, CheckCircle, LogOut, KeyRound } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const { currentUser, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const roleName = (role && ROLE_DISPLAY_NAMES[role]) || 'USER';
  const roleBadge = (role && ROLE_BADGE_COLORS[role]) || 'bg-slate-700 text-slate-200';

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2.5">
            <User className="text-indigo-400" size={22} />
            User Identity Profile
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative session identity and permissions derived from backend user records.
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="px-3.5 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-sm"
        >
          <LogOut size={14} />
          <span>Sign Out</span>
        </button>
      </div>

      {/* Profile Details Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Identity Overview */}
        <div className="md:col-span-1 bg-slate-900/80 border border-slate-800 rounded-xl p-6 flex flex-col items-center text-center shadow-lg">
          <div className="w-20 h-20 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-300 mb-4 shadow-md shadow-indigo-950">
            <User size={36} />
          </div>

          <h2 className="text-sm font-bold text-slate-100 mb-1">
            {currentUser?.display_name || 'Authenticated User'}
          </h2>
          <span className="text-xs font-mono text-slate-400 mb-3">
            @{currentUser?.username}
          </span>

          <div className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase border ${roleBadge} mb-4`}>
            {roleName}
          </div>

          <div className="w-full pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Status</span>
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <CheckCircle size={13} />
              Active
            </span>
          </div>
        </div>

        {/* Security & Access Details */}
        <div className="md:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4 shadow-lg">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wider pb-3 border-b border-slate-800">
            <Shield size={15} className="text-indigo-400" />
            Security Credentials & Authorization Details
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-1">
                User Identifier
              </span>
              <span className="font-mono text-slate-200 font-semibold">
                {currentUser?.user_id || 'usr_session'}
              </span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-1">
                Assigned Jurisdiction
              </span>
              <span className="text-slate-200 font-medium flex items-center gap-1.5">
                <MapPin size={13} className="text-amber-400 shrink-0" />
                {currentUser?.jurisdiction || 'Unrestricted / General'}
              </span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-1">
                Authentication Method
              </span>
              <span className="text-slate-200 font-medium flex items-center gap-1.5">
                <KeyRound size={13} className="text-indigo-400 shrink-0" />
                PBKDF2-HMAC-SHA256 Bearer Token
              </span>
            </div>

            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-1">
                Security Boundary
              </span>
              <span className="text-emerald-400 font-medium">
                Authoritative Backend RBAC
              </span>
            </div>
          </div>

          <div className="mt-4 p-3.5 bg-indigo-950/20 border border-indigo-500/30 rounded-lg text-xs text-indigo-300/90 leading-relaxed">
            <div className="font-bold text-indigo-200 mb-1">Session Security Assurance</div>
            All analytical capabilities, entity lookups, and graph traversals are bound strictly to your authenticated role. Unauthorized endpoints automatically yield HTTP 403.
          </div>
        </div>

      </div>
    </div>
  );
}
