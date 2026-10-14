import React from 'react';
import { User, Users, MapPin, Briefcase, FolderOpen, ArrowRight, HelpCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * CandidateSelection.jsx
 * Disambiguation interface for ambiguous person names (Rule 5).
 * Guarantees the assistant never guesses.
 */
export default function CandidateSelection({ candidates = [], onSelectCandidate }) {
  if (!candidates || candidates.length === 0) return null;

  return (
    <div className="mt-3 p-3.5 rounded-lg bg-amber-950/20 border border-amber-500/30 text-slate-200">
      <div className="flex items-center gap-2 mb-2.5 text-amber-400 font-semibold text-xs uppercase tracking-wider">
        <HelpCircle className="w-4 h-4" />
        <span>Ambiguous Name Resolution — Select Intended Person</span>
      </div>
      <p className="text-xs text-slate-300 mb-3">
        Multiple individual records match this name. In accordance with investigative integrity protocols, the system does not infer or guess identity. Please choose a specific record:
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {candidates.map((cand) => (
          <div
            key={cand.person_id}
            className="p-3 rounded-md bg-slate-900/80 border border-slate-700/80 hover:border-amber-500/50 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-1">
                <div>
                  <h5 className="font-bold text-slate-100 text-sm">{cand.full_name}</h5>
                  <span className="text-[11px] font-mono text-blue-400 bg-blue-950/50 px-1.5 py-0.5 rounded border border-blue-800/50">
                    {cand.person_id}
                  </span>
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                  {cand.associated_case_count} case(s)
                </span>
              </div>

              <div className="space-y-1 text-xs text-slate-400 mt-2">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="truncate">{cand.location || 'Unknown Location'}</span>
                </div>
                {cand.occupation && (
                  <div className="flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span className="truncate">{cand.occupation}</span>
                  </div>
                )}
                {cand.aliases && cand.aliases.length > 0 && (
                  <div className="text-[11px] text-slate-400 truncate">
                    <span className="text-slate-500">Aliases:</span> {cand.aliases.join(', ')}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 mt-3 pt-2.5 border-t border-slate-800">
              <Link
                to={`/entities/${cand.person_id}`}
                className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors flex items-center gap-1"
              >
                <User className="w-3 h-3" />
                Profile
              </Link>
              <button
                onClick={() => onSelectCandidate(cand.person_id, cand.full_name)}
                className="flex-1 px-2.5 py-1 text-xs font-medium rounded bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/40 hover:border-blue-500 transition-all flex items-center justify-center gap-1"
              >
                Query This Person
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
