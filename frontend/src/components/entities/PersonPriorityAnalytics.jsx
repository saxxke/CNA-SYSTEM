import React from 'react';
import { Target, BarChart2, AlertCircle, ShieldAlert, CheckCircle2, TrendingUp } from 'lucide-react';

const LEVEL_COLORS = {
  'HIGH': 'bg-rose-950/80 text-rose-300 border-rose-500/40',
  'MEDIUM': 'bg-amber-950/80 text-amber-300 border-amber-500/40',
  'LOW': 'bg-sky-950/80 text-sky-300 border-sky-500/40',
};

export default function PersonPriorityAnalytics({ priority = null, graphMetrics = {} }) {
  const hasPriority = Boolean(priority);
  const priorityScore = hasPriority ? Math.round((priority.priority_score || 0) * 100) : null;
  const priorityLevel = (priority?.priority_level || 'STANDARD').toUpperCase();
  const reasons = priority?.reasons || [];
  const supportingEvidence = priority?.supporting_evidence || [];

  const degreeCentrality = graphMetrics.degree_centrality != null ? (graphMetrics.degree_centrality).toFixed(3) : null;
  const betweennessCentrality = graphMetrics.betweenness_centrality != null ? (graphMetrics.betweenness_centrality).toFixed(3) : null;

  return (
    <div className="space-y-4 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Investigation Priority & Graph Analytics</h2>
        </div>
        <span className="text-[11px] font-bold text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-500/40">
          Analytical Lead Only
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Priority Score Card */}
        <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Investigation Priority</div>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-mono font-bold text-slate-100">
                  {priorityScore != null ? priorityScore : 'Unscored'}
                </span>
                {priorityScore != null && (
                  <span className="text-xs text-slate-400 font-mono">/ 100</span>
                )}
              </div>
            </div>

            {hasPriority && (
              <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold border ${LEVEL_COLORS[priorityLevel] || 'bg-slate-800 text-slate-300'}`}>
                {priorityLevel} PRIORITY
              </span>
            )}
          </div>

          {/* Progress bar */}
          {priorityScore != null && (
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  priorityLevel === 'HIGH' ? 'bg-rose-500' : priorityLevel === 'MEDIUM' ? 'bg-amber-500' : 'bg-indigo-500'
                }`}
                style={{ width: `${Math.min(priorityScore, 100)}%` }}
              />
            </div>
          )}

          {/* Reasons */}
          <div className="space-y-1.5 pt-1">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Triage Rationales
            </div>
            {reasons.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No specific priority flags assigned.</p>
            ) : (
              <ul className="space-y-1">
                {reasons.map((r, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Graph Analytics Card */}
        <div className="p-5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <BarChart2 size={13} className="text-indigo-400" />
            Topological Centrality Scores
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
              <div className="text-[10px] text-slate-400 uppercase font-bold">Degree Centrality</div>
              <div className="text-xl font-mono font-bold text-slate-100 mt-1">
                {degreeCentrality ?? 'N/A'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">Direct connection fraction</div>
            </div>

            <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
              <div className="text-[10px] text-slate-400 uppercase font-bold">Betweenness Score</div>
              <div className="text-xl font-mono font-bold text-slate-100 mt-1">
                {betweennessCentrality ?? 'N/A'}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">Shortest-path bridge fraction</div>
            </div>
          </div>

          {/* Supporting evidence */}
          {supportingEvidence.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Corroborating Evidence
              </div>
              <div className="bg-slate-900 rounded-lg p-2.5 border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1">
                {supportingEvidence.slice(0, 3).map((ev, i) => (
                  <p key={i} className="truncate">• {ev}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
