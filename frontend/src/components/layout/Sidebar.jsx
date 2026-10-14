import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { getNavigationForRole, ROLE_DISPLAY_NAMES, ROLE_BADGE_COLORS } from '../../auth/roleNavigation';
import { Activity, LogOut, User } from 'lucide-react';

export default function Sidebar() {
  const { currentUser, role, logout } = useAuth();
  const navigate = useNavigate();

  // Obtain role-specific navigation manifest
  const navSections = getNavigationForRole(role);
  const roleLabel = (role && ROLE_DISPLAY_NAMES[role]) || 'USER';
  const roleBadge = (role && ROLE_BADGE_COLORS[role]) || 'bg-slate-800 text-slate-400';

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <aside className="w-64 bg-slate-950 text-slate-300 flex flex-col h-full border-r border-slate-800/80 shrink-0 select-none">
      {/* Platform Branding */}
      <div className="px-5 py-4 border-b border-slate-800/70 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
          <Activity size={18} />
        </div>
        <div>
          <div className="text-xs font-bold text-slate-100 tracking-wider uppercase flex items-center gap-1.5">
            PS26189 INTEL
          </div>
          <div className="text-[10px] text-slate-400 font-medium">
            Network Analysis System
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 pb-1.5 text-[10px] font-bold text-slate-400 tracking-wider uppercase">
              {section.title}
            </div>
            {section.items.map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm shadow-indigo-950/50'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
                  }`
                }
              >
                <item.icon size={16} className="shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User Status & Sign Out Footer */}
      <div className="p-3 border-t border-slate-800/70 bg-slate-950/90 text-xs space-y-2">
        {currentUser && (
          <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="overflow-hidden mr-2">
              <div className="text-xs font-bold text-slate-200 truncate">
                {currentUser.display_name?.split(' ')[0] || currentUser.username}
              </div>
              <div className="text-[9px] font-mono text-slate-400 truncate">
                {currentUser.jurisdiction || roleLabel}
              </div>
            </div>
            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase font-semibold shrink-0 ${roleBadge}`}>
              {roleLabel.split(' ')[0]}
            </span>
          </div>
        )}

        <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
          <button
            onClick={handleLogout}
            className="text-[11px] text-slate-400 hover:text-rose-400 font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <LogOut size={13} />
            <span>Sign Out</span>
          </button>
          
          <span className="flex items-center gap-1.5 text-emerald-400 text-[10px] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            ACTIVE
          </span>
        </div>
      </div>
    </aside>
  );
}
