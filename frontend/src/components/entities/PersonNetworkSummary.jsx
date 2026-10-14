import React from 'react';
import { Network, Users, Share2, FolderGit2, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function PersonNetworkSummary({ summary = {}, personId, fullName }) {
  const navigate = useNavigate();

  const connectedEntities = summary.connected_entities_count ?? 0;
  const relatedPersons = summary.related_persons_count ?? 0;
  const associatedCases = summary.associated_cases_count ?? 0;
  const relationshipTypes = summary.relationship_types || [];
  const primaryCaseId = summary.primary_case_id || 'CASE-001';

  return (
    <div className="space-y-4 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Network size={16} className="text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Network Connections Summary</h2>
        </div>

        <button
          onClick={() => navigate(`/network?caseId=${primaryCaseId}`)}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-xs transition-all self-start sm:self-auto"
        >
          <Network size={14} />
          <span>Open in Network ({primaryCaseId})</span>
          <ExternalLink size={12} />
        </button>
      </div>

      {/* Network Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Connected Entities</div>
          <div className="text-2xl font-mono font-bold text-slate-100 mt-0.5">{connectedEntities}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Topological neighbors</div>
        </div>

        <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Related Persons</div>
          <div className="text-2xl font-mono font-bold text-indigo-400 mt-0.5">{relatedPersons}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Co-occurring associates</div>
        </div>

        <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Associated Cases</div>
          <div className="text-2xl font-mono font-bold text-amber-400 mt-0.5">{associatedCases}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Cross-case registry records</div>
        </div>

        <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Link Modalities</div>
          <div className="text-2xl font-mono font-bold text-emerald-400 mt-0.5">{relationshipTypes.length}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Distinct relation types</div>
        </div>
      </div>

      {/* Relationship Modality Badges */}
      {relationshipTypes.length > 0 && (
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Detected Relationship Modalities
          </div>
          <div className="flex flex-wrap gap-1.5">
            {relationshipTypes.map((type) => (
              <span
                key={type}
                className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-slate-900 text-indigo-300 border border-slate-800"
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
