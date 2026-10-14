import React from 'react';
import { Network, ArrowRight, ShieldCheck, FileText, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * NetworkResultCards.jsx
 * Displays verified relational edges from NetworkX graph.
 * Provides direct deep links to interactive Network Graph viewer.
 */
export default function NetworkResultCards({ relationships = [], activePersonId, activeCaseId }) {
  if (!relationships || relationships.length === 0) return null;

  return (
    <div className="mt-3 space-y-2.5">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-semibold uppercase tracking-wider text-slate-300">
          Verified Network Connections ({relationships.length})
        </span>
        <span className="text-[11px] text-slate-400">NetworkX Intelligence Graph</span>
      </div>

      <div className="space-y-2">
        {relationships.map((rel, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          >
            <div className="space-y-1.5 flex-1">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="font-semibold text-slate-100 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                  {rel.source_name || rel.source}
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-800/60 font-semibold flex items-center gap-1">
                  {rel.relationship_type || rel.type}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                <span className="font-semibold text-slate-100 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                  {rel.target_name || rel.target}
                </span>
                {rel.confidence != null && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
                    {Math.round(rel.confidence * 100)}% Conf.
                  </span>
                )}
              </div>

              {rel.evidence && (
                <p className="text-xs text-slate-400 italic pl-1 border-l border-slate-700">
                  "{rel.evidence}"
                </p>
              )}

              {rel.case_id && (
                <div className="text-[11px] text-slate-500">
                  Associated Case: <span className="font-mono text-slate-400">{rel.case_id}</span>
                </div>
              )}
            </div>

            <div className="shrink-0 flex items-center gap-2">
              <Link
                to={rel.case_id ? `/network?caseId=${rel.case_id}` : activePersonId ? `/network?personId=${activePersonId}` : '/network'}
                className="px-2.5 py-1.5 text-xs font-medium rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 transition-colors flex items-center gap-1.5"
              >
                <Network className="w-3.5 h-3.5 text-emerald-400" />
                <span>Open Graph</span>
                <ExternalLink className="w-3 h-3 text-slate-400" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
