import React from 'react';
import { AlertTriangle, ShieldAlert, Award, Activity, FileText, User, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * PriorityResultCard.jsx
 * Displays deterministic priority scoring and analytical rationale.
 * Strictly labeled as Analytical Priority requiring human investigator verification.
 */
export default function PriorityResultCard({ priorityInfo, personId, personName }) {
  if (!priorityInfo) return null;

  const {
    priority_score = 0,
    priority_level = 'LOW',
    reasons = [],
    supporting_evidence = [],
    centrality_metrics = {}
  } = priorityInfo;

  const getLevelBadgeClass = (level) => {
    switch (level?.toUpperCase()) {
      case 'HIGH':
        return 'bg-red-950/60 text-red-300 border-red-800/60';
      case 'MEDIUM':
        return 'bg-amber-950/60 text-amber-300 border-amber-800/60';
      default:
        return 'bg-blue-950/60 text-blue-300 border-blue-800/60';
    }
  };

  return (
    <div className="mt-3 p-4 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all text-slate-200">
      <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Analytical Priority — Human Review
            </span>
            <span
              className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${getLevelBadgeClass(
                priority_level
              )}`}
            >
              {priority_level} PRIORITY
            </span>
          </div>
          <h4 className="text-base font-bold text-slate-100 mt-1">
            {personName || personId || 'Subject Analysis'}
          </h4>
        </div>

        <div className="text-right">
          <div className="text-2xl font-black text-amber-400 tracking-tight font-mono">
            {Math.round(priority_score)}
            <span className="text-xs text-slate-500 font-normal"> / 100</span>
          </div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Priority Score</span>
        </div>
      </div>

      {/* Centrality Metrics if available */}
      {centrality_metrics && Object.keys(centrality_metrics).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-3">
          {Object.entries(centrality_metrics).map(([key, val]) => (
            <div key={key} className="p-2 rounded bg-slate-800/60 border border-slate-700/60">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block truncate">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-xs font-mono font-semibold text-blue-400">
                {typeof val === 'number' ? val.toFixed(3) : val}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Analytical Reasons */}
      {reasons && reasons.length > 0 && (
        <div className="mt-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-1.5 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            Priority Determination Factors
          </span>
          <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
            {reasons.map((r, i) => (
              <li key={i} className="leading-relaxed">
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Supporting Evidence Snippets */}
      {supporting_evidence && supporting_evidence.length > 0 && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/80">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1.5 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            Supporting Synthetic Records
          </span>
          <div className="space-y-1">
            {supporting_evidence.map((ev, i) => (
              <div key={i} className="text-xs text-slate-400 bg-slate-800/40 p-1.5 rounded border border-slate-800">
                {ev}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Safety Notice & Action */}
      <div className="mt-3.5 pt-3 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs">
        <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Priority is an algorithmic focus metric, not a legal finding of guilt.</span>
        </div>

        {personId && (
          <Link
            to={`/entities/${personId}`}
            className="px-3 py-1 text-xs rounded bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors flex items-center gap-1 shrink-0 self-start sm:self-auto"
          >
            <User className="w-3 h-3" />
            View Full Dossier
            <ArrowRight className="w-3 h-3" />
          </Link>
        )}
      </div>
    </div>
  );
}
