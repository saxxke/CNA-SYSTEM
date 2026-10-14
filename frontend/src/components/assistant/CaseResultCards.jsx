import React from 'react';
import { FolderOpen, Network, MapPin, Calendar, FileText, ArrowRight, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * CaseResultCards.jsx
 * Displays verified case records returned by the backend.
 * Provides direct deep links to Case Explorer and Network views.
 */
export default function CaseResultCards({ cases = [], onAskFollowup }) {
  if (!cases || cases.length === 0) return null;

  return (
    <div className="mt-3 space-y-2.5">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-semibold uppercase tracking-wider text-slate-300">
          Matched Case Records ({cases.length})
        </span>
        <span className="text-[11px] text-slate-400">Official Case Registry</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {cases.map((c) => (
          <div
            key={c.case_id}
            className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-800/40">
                      {c.case_id}
                    </span>
                    {c.fir_number && (
                      <span className="text-[11px] text-slate-400">FIR: {c.fir_number}</span>
                    )}
                  </div>
                  <h5 className="font-bold text-slate-100 text-sm mt-1">{c.title}</h5>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                    c.status === 'OPEN'
                      ? 'bg-amber-950/50 text-amber-300 border-amber-800/50'
                      : 'bg-emerald-950/50 text-emerald-300 border-emerald-800/50'
                  }`}
                >
                  {c.status || 'RECORDED'}
                </span>
              </div>

              <div className="space-y-1 text-xs text-slate-300 mt-2">
                {c.offence_category && (
                  <div className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span className="font-medium text-slate-200">{c.offence_category}</span>
                  </div>
                )}
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="text-slate-300 truncate">
                    {[c.location, c.district, c.police_station].filter(Boolean).join(' • ') || 'Location unrecorded'}
                  </span>
                </div>
                {c.year && (
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="text-slate-300">{c.year}</span>
                  </div>
                )}
              </div>

              {/* Matching Reasons */}
              {c.matching_reasons && c.matching_reasons.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-800/80">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
                    Matching Reasons:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {c.matching_reasons.map((reason, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700"
                      >
                        {reason}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex items-center gap-2 mt-3 pt-2.5 border-t border-slate-800 text-xs">
              <Link
                to={`/cases/${c.case_id}`}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors flex items-center gap-1"
                title="View Case Investigation Record"
              >
                <FolderOpen className="w-3 h-3 text-amber-400" />
                View Case
              </Link>
              <Link
                to={`/network?caseId=${c.case_id}`}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors flex items-center gap-1"
                title="Open Case Subgraph in Network View"
              >
                <Network className="w-3 h-3 text-emerald-400" />
                Network
              </Link>
              {onAskFollowup && (
                <button
                  onClick={() => onAskFollowup(`Tell me more about ${c.case_id}`)}
                  className="px-2.5 py-1 rounded bg-blue-900/30 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-700/40 transition-colors ml-auto flex items-center gap-1"
                >
                  Ask Details
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
