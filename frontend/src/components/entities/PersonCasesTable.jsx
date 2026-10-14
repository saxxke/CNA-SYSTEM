import React from 'react';
import { FolderOpen, MapPin, Calendar, FileText, ChevronRight, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const OFFENCE_COLORS = {
  'Cyber Crime': 'bg-purple-950/80 text-purple-300 border-purple-500/40',
  'Extortion': 'bg-rose-950/80 text-rose-300 border-rose-500/40',
  'Kidnapping': 'bg-amber-950/80 text-amber-300 border-amber-500/40',
  'Financial Fraud': 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
  'Narcotics': 'bg-red-950/80 text-red-300 border-red-500/40',
  'Theft': 'bg-blue-950/80 text-blue-300 border-blue-500/40',
  'Homicide': 'bg-stone-900 text-stone-300 border-stone-600',
  'Smuggling': 'bg-indigo-950/80 text-indigo-300 border-indigo-500/40',
};

export default function PersonCasesTable({ cases = [] }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderOpen size={16} className="text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Associated Case Records</h2>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
            {cases.length} {cases.length === 1 ? 'Case' : 'Cases'} Linked
          </span>
        </div>
        <p className="text-xs text-slate-400 hidden sm:block">
          Select any case to open dossier and relational graph.
        </p>
      </div>

      {cases.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
          No cases directly associated with this person record.
        </div>
      ) : (
        <div className="space-y-3">
          {cases.map((c) => {
            const offenceClass = OFFENCE_COLORS[c.offence_category] || 'bg-slate-800 text-slate-300 border-slate-700';
            const isClosed = (c.status || '').toUpperCase() === 'CLOSED';

            return (
              <div
                key={c.case_id}
                onClick={() => navigate(`/cases/${c.case_id}`)}
                className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 hover:border-slate-700 cursor-pointer transition-all space-y-3 group"
              >
                {/* Header row: ID, FIR, Offence, Status */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-indigo-300 bg-indigo-950 border border-indigo-800 px-2 py-0.5 rounded">
                      {c.case_id}
                    </span>
                    <span className="font-mono text-xs text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                      {c.fir_number || 'FIR Unassigned'}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${offenceClass}`}>
                      {c.offence_category}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                      isClosed ? 'bg-slate-800 text-slate-400' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      {c.status || 'ACTIVE'}
                    </span>
                    <ChevronRight size={15} className="text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>

                {/* Case Title & Narrative */}
                <div>
                  <h3 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                    {c.case_title || c.title || c.case_id}
                  </h3>
                  {c.description && (
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {c.description}
                    </p>
                  )}
                </div>

                {/* Footer metadata */}
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <MapPin size={12} className="text-slate-500" />
                      <span>{c.district || 'General Area'} {c.police_station ? `• PS: ${c.police_station}` : ''}</span>
                    </div>
                    {c.date_opened && (
                      <div className="flex items-center gap-1">
                        <Calendar size={12} className="text-slate-500" />
                        <span>Opened: {c.date_opened}</span>
                      </div>
                    )}
                  </div>

                  <span className="text-[11px] font-semibold text-indigo-400 group-hover:text-indigo-300">
                    Open Case Dossier →
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
