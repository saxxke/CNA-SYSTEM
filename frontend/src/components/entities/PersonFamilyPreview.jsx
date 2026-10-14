import React from 'react';
import { Users2, ShieldAlert, AlertTriangle, ExternalLink, HeartHandshake, UserCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const SUBTYPE_BADGES = {
  'FATHER': 'bg-blue-950/80 text-blue-300 border-blue-500/40',
  'MOTHER': 'bg-pink-950/80 text-pink-300 border-pink-500/40',
  'SPOUSE': 'bg-purple-950/80 text-purple-300 border-purple-500/40',
  'CHILD': 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
  'SON': 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
  'DAUGHTER': 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
  'BROTHER': 'bg-teal-950/80 text-teal-300 border-teal-500/40',
  'SISTER': 'bg-teal-950/80 text-teal-300 border-teal-500/40',
};

export default function PersonFamilyPreview({ family = [], subjectName = 'Subject', subjectId = '' }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <HeartHandshake size={16} className="text-emerald-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Family Relationships (Civilian Record)</h2>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
            {family.length} Recorded
          </span>
        </div>
        {subjectId && (
          <button
            onClick={() => navigate(`/entities/${subjectId}/family`)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-emerald-300 bg-emerald-950/60 border border-emerald-500/30 hover:bg-emerald-900/40 transition-colors self-start"
          >
            <span>Open Dedicated Family Explorer</span>
            <ExternalLink size={12} />
          </button>
        )}
      </div>

      {/* Mandatory Safety Notice: Visually Separated */}
      <div className="p-3.5 rounded-xl bg-amber-950/50 border border-amber-600/30 text-amber-200 text-xs flex items-start gap-3">
        <ShieldAlert size={18} className="text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <div className="font-bold text-amber-300">MANDATORY INVESTIGATIVE SAFETY RULE</div>
          <p className="text-amber-200/80 leading-relaxed">
            Family relationship does <strong>NOT</strong> imply case involvement, criminality, or investigative culpability. 
            Civilian family ties are maintained strictly for biological and identification reference. Keep family relationships visually separate from case associations.
          </p>
        </div>
      </div>

      {family.length === 0 ? (
        <div className="p-10 text-center text-slate-400 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
          No registered civilian family relationships on file for this person.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {family.map((rel) => {
            const badgeClass = SUBTYPE_BADGES[rel.relationship_subtype] || 'bg-slate-800 text-slate-300 border-slate-700';

            return (
              <div
                key={rel.relationship_id || rel.relative_person_id}
                onClick={() => {
                  if (rel.relative_person_id) {
                    navigate(`/entities/${rel.relative_person_id}`);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }}
                className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl hover:border-slate-700 cursor-pointer transition-all space-y-2 group"
              >
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider border ${badgeClass}`}>
                    {rel.relationship_subtype || 'RELATIVE'}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    Reciprocal: {rel.is_reciprocal ? 'Yes' : 'No'}
                  </span>
                </div>

                <div>
                  <div className="font-bold text-sm text-slate-100 group-hover:text-emerald-300 transition-colors">
                    {rel.relative_name || 'Relative'}
                  </div>
                  <div className="font-mono text-[11px] text-slate-400 mt-0.5">
                    {rel.relative_person_id}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>{rel.relative_occupation || 'Civilian'} • {rel.relative_location || 'Area'}</span>
                  <span className="text-[10px] text-emerald-400 font-bold group-hover:underline">View Profile →</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
