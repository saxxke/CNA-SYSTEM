import React, { useState } from 'react';
import { Link2, ExternalLink, ArrowRight, ArrowLeft, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import EvidenceProvenanceModal from '../provenance/EvidenceProvenanceModal';

export default function PersonEvidenceRelationships({ relationships = [], personId }) {
  const navigate = useNavigate();
  const [activeProvenance, setActiveProvenance] = useState(null);

  return (
    <div className="space-y-4 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link2 size={16} className="text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Evidence-Backed Relationships</h2>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
            {relationships.length} Links
          </span>
        </div>
        <p className="text-xs text-slate-400 hidden sm:block">
          Relationships verified via telecom, financial records, and graph evidence.
        </p>
      </div>

      {relationships.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
          No structured evidence relationships indexed for this person.
        </div>
      ) : (
        <div className="bg-slate-950/80 rounded-xl border border-slate-800 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                  <th className="py-2.5 px-3.5">Relationship Type</th>
                  <th className="py-2.5 px-3.5">Connected Entity</th>
                  <th className="py-2.5 px-3.5">Direction</th>
                  <th className="py-2.5 px-3.5">Confidence</th>
                  <th className="py-2.5 px-3.5">Evidence Provenance</th>
                  <th className="py-2.5 px-3.5">Case Context</th>
                  <th className="py-2.5 px-3.5">Method</th>
                  <th className="py-2.5 px-3.5 text-right">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {relationships.map((rel, idx) => {
                  const isPerson = rel.connected_entity_id && rel.connected_entity_id.startsWith('PERSON-');
                  const pct = Math.round((rel.confidence || 0) * 100);

                  return (
                    <tr key={rel.relationship_id || idx} className="hover:bg-slate-900/50 transition-colors">
                      {/* Type */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                          {rel.relationship_type}
                        </span>
                      </td>

                      {/* Connected Entity */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap">
                        {isPerson ? (
                          <button
                            onClick={() => {
                              navigate(`/entities/${rel.connected_entity_id}`);
                              window.scrollTo({ top: 0, behavior: 'smooth' });
                            }}
                            className="font-mono text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1"
                          >
                            <span>{rel.connected_entity_name || rel.connected_entity_id}</span>
                            <ExternalLink size={11} />
                          </button>
                        ) : (
                          <span className="font-mono text-slate-300">{rel.connected_entity_id}</span>
                        )}
                        <span className="text-[10px] text-slate-400 ml-1.5 font-mono">({rel.connected_entity_type})</span>
                      </td>

                      {/* Direction */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap text-[11px] text-slate-400">
                        {rel.direction === 'OUTGOING' ? (
                          <span className="flex items-center gap-1 text-slate-300">
                            Outgoing <ArrowRight size={11} className="text-slate-400" />
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-slate-300">
                            Incoming <ArrowLeft size={11} className="text-slate-400" />
                          </span>
                        )}
                      </td>

                      {/* Confidence */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                          pct >= 80 ? 'text-emerald-300 bg-emerald-950/80 border-emerald-800' :
                          pct >= 60 ? 'text-amber-300 bg-amber-950/80 border-amber-800' :
                          'text-slate-400 bg-slate-800 border-slate-700'
                        }`}>
                          {pct}%
                        </span>
                      </td>

                      {/* Evidence */}
                      <td className="py-2.5 px-3.5 max-w-xs truncate text-[11px] font-mono text-slate-400" title={rel.evidence}>
                        {rel.evidence || 'No detailed log text'}
                      </td>

                      {/* Case Context */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap font-mono text-[11px]">
                        {rel.case_id ? (
                          <button
                            onClick={() => navigate(`/cases/${rel.case_id}`)}
                            className="text-indigo-400 hover:text-indigo-300 underline"
                          >
                            {rel.case_id}
                          </button>
                        ) : (
                          <span className="text-slate-400">System Cross</span>
                        )}
                      </td>

                      {/* Detection Method */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap text-[10px] font-mono text-slate-400">
                        {rel.detection_method || 'rule_based'}
                      </td>

                      {/* Provenance Inspection Trigger */}
                      <td className="py-2.5 px-3.5 whitespace-nowrap text-right">
                        <button
                          onClick={() => setActiveProvenance({
                            source: rel.source_id || personId,
                            target: rel.target_id || rel.connected_entity_id,
                            caseId: rel.case_id
                          })}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-[10px] font-semibold transition-colors"
                          title="Inspect Evidence Provenance"
                        >
                          <FileText size={11} />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Evidence Provenance Modal */}
      {activeProvenance && (
        <EvidenceProvenanceModal
          isOpen={Boolean(activeProvenance)}
          onClose={() => setActiveProvenance(null)}
          sourceId={activeProvenance.source}
          targetId={activeProvenance.target}
          caseId={activeProvenance.caseId}
        />
      )}
    </div>
  );
}
