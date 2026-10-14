import React from 'react';
import { Loader2, AlertCircle } from 'lucide-react';

export default function StatCard({ title, value, icon: Icon, subtitle, loading = false, error = null }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-start justify-between shadow-sm hover:border-slate-700 transition-colors select-none">
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">{title}</p>
        
        {loading ? (
          <div className="flex items-center space-x-2 mt-2">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            <span className="text-xs text-slate-400">Loading…</span>
          </div>
        ) : error ? (
          <div className="flex items-center space-x-2 mt-2 text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs">Error</span>
          </div>
        ) : (
          <h3 className="text-2xl font-mono font-bold text-slate-100">{value}</h3>
        )}

        {subtitle && (
          <p className="text-[11px] text-slate-400 mt-1">{subtitle}</p>
        )}
      </div>
      
      <div className="p-2.5 bg-indigo-950/60 border border-indigo-500/30 rounded-lg text-indigo-400">
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}
