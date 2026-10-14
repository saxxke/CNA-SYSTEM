import React from 'react';
import { User, Users, Network, MapPin, Briefcase, FolderOpen, ArrowRight, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * PersonResultCards.jsx
 * Displays verified person investigative leads returned by the backend.
 * Enforces non-accusatory terminology and deep navigation.
 */
export default function PersonResultCards({ persons = [], onAskFollowup }) {
  if (!persons || persons.length === 0) return null;

  return (
    <div className="mt-3 space-y-2.5">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-semibold uppercase tracking-wider text-slate-300">
          Matched Person Leads ({persons.length})
        </span>
        <span className="text-[11px] text-slate-400">Analytical Subject Records</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {persons.map((p) => (
          <div
            key={p.person_id}
            className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div>
                  <h5 className="font-bold text-slate-100 text-sm">{p.full_name}</h5>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[11px] font-mono text-blue-400 bg-blue-950/50 px-1.5 py-0.5 rounded border border-blue-800/50">
                      {p.person_id}
                    </span>
                    {p.gender && (
                      <span className="text-[10px] text-slate-400">{p.gender}</span>
                    )}
                  </div>
                </div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-950/40 text-blue-300 border border-blue-800/40 font-medium whitespace-nowrap">
                  {p.associated_case_count} associated case(s)
                </span>
              </div>

              <div className="space-y-1 text-xs text-slate-300 mt-2.5">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="text-slate-300 truncate">
                    {p.location || p.city || p.district || 'Location unrecorded'}
                  </span>
                </div>
                {p.occupation && (
                  <div className="flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="text-slate-300 truncate">{p.occupation}</span>
                  </div>
                )}
              </div>

              {/* Matching Reasons */}
              {p.matching_reasons && p.matching_reasons.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-800/80">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
                    Matching Reasons:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {p.matching_reasons.map((reason, idx) => (
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

              {/* Associated Case IDs */}
              {p.associated_case_ids && p.associated_case_ids.length > 0 && (
                <div className="mt-2 text-[11px] text-slate-400">
                  <span className="text-slate-400">Associated Cases:</span>{' '}
                  <span className="font-mono text-slate-300">
                    {p.associated_case_ids.slice(0, 4).join(', ')}
                    {p.associated_case_ids.length > 4 ? ` +${p.associated_case_ids.length - 4} more` : ''}
                  </span>
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-2.5 border-t border-slate-800 text-xs">
              <Link
                to={`/entities/${p.person_id}`}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors flex items-center gap-1"
                title="View Person Investigation Dossier"
              >
                <User className="w-3 h-3 text-blue-400" />
                Profile
              </Link>
              <Link
                to={`/entities/${p.person_id}/family`}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors flex items-center gap-1"
                title="View Civilian Family Context (Not evidence of case involvement)"
              >
                <Users className="w-3 h-3 text-purple-400" />
                Family
              </Link>
              <Link
                to={`/network?personId=${p.person_id}`}
                className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition-colors flex items-center gap-1"
                title="Open Network Graph View"
              >
                <Network className="w-3 h-3 text-emerald-400" />
                Network
              </Link>
              {onAskFollowup && (
                <button
                  onClick={() => onAskFollowup(`Tell me more about ${p.person_id}`)}
                  className="px-2 py-1 rounded bg-blue-900/30 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-700/40 transition-colors ml-auto flex items-center gap-1"
                  title="Query dossier in assistant"
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
