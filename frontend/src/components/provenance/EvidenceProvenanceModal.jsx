/**
 * EvidenceProvenanceModal.jsx
 * ===========================
 * Phase 8A: Explainable Relationship Evidence Provenance Inspector.
 *
 * Guarantees:
 * - Displays sanitized synthetic records backing an analytical relationship.
 * - Displays observable ML evidence signals ("Confidence Evidence Breakdown").
 * - Strictly non-accusatory terminology: No "guilt", "criminal probability", or "proof".
 * - Mandatory synthetic data and human verification safety notice.
 */
import React, { useState, useEffect } from 'react';
import { 
  X, Link2, ShieldAlert, FileText, Activity, AlertCircle, 
  Loader2, PhoneCall, CreditCard, FolderOpen, ArrowRight, 
  ExternalLink, BarChart3, Database, CheckCircle2
} from 'lucide-react';
import api from '../../api/client';

export default function EvidenceProvenanceModal({
  isOpen,
  onClose,
  sourceId,
  targetId,
  caseId = null
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !sourceId || !targetId) {
      setData(null);
      return;
    }

    let isMounted = true;
    const fetchProvenance = async () => {
      try {
        setLoading(true);
        setError(null);
        let url = `/api/provenance/edge?source=${encodeURIComponent(sourceId)}&target=${encodeURIComponent(targetId)}`;
        if (caseId) {
          url += `&case_id=${encodeURIComponent(caseId)}`;
        }
        const resp = await api.get(url);
        if (isMounted) {
          setData(resp.data);
        }
      } catch (err) {
        if (isMounted) {
          if (err.response?.status === 403) {
            setError('Access restricted: You do not have authorization to view evidence provenance for this case.');
          } else if (err.response?.status === 404) {
            setError('Evidence provenance record not found or outside your authorized investigation scope.');
          } else {
            setError('Unable to load evidence provenance from the server.');
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchProvenance();
    return () => {
      isMounted = false;
    };
  }, [isOpen, sourceId, targetId, caseId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-950 border border-indigo-800 text-indigo-400">
              <Link2 size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Relationship Evidence Provenance
              </h2>
              <p className="text-xs text-slate-400">
                Audited analytical trace of synthetic supporting records & observable signals
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
            title="Close Provenance Inspector"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center space-y-3">
              <Loader2 size={32} className="animate-spin text-indigo-400" />
              <p className="font-semibold text-slate-300">Retrieving sanitized evidence provenance…</p>
            </div>
          ) : error ? (
            <div className="p-8 bg-slate-950/60 border border-amber-900/40 rounded-xl text-center space-y-2">
              <AlertCircle size={32} className="mx-auto text-amber-400" />
              <h3 className="text-sm font-bold text-amber-200">Provenance Access Restricted</h3>
              <p className="text-slate-400 leading-relaxed max-w-md mx-auto">{error}</p>
            </div>
          ) : data ? (
            <>
              {/* Relationship Summary Bar */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="px-2.5 py-1 rounded text-xs font-mono font-bold uppercase tracking-wider bg-indigo-950 text-indigo-300 border border-indigo-800">
                    {data.relationship_type}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Detection Method:</span>
                    <span className="px-2 py-0.5 rounded font-mono font-bold text-[11px] bg-slate-800 text-slate-200 border border-slate-700">
                      {data.detection_method}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="font-bold text-slate-200">{data.source_label}</div>
                      <div className="font-mono text-[10px] text-slate-400">{data.source_id} ({data.source_type})</div>
                    </div>
                    <ArrowRight size={16} className="text-indigo-400" />
                    <div>
                      <div className="font-bold text-slate-200">{data.target_label}</div>
                      <div className="font-mono text-[10px] text-slate-400">{data.target_id} ({data.target_type})</div>
                    </div>
                  </div>
                  {data.case_id && (
                    <div className="text-right">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Case Reference</span>
                      <span className="font-mono text-xs font-bold text-indigo-400">{data.case_id}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Confidence Evidence Breakdown */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 size={15} className="text-indigo-400" />
                    <h3 className="font-bold uppercase tracking-wider text-slate-300 text-xs">
                      Confidence Evidence Breakdown
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-100 text-sm">
                      {Math.round((data.confidence_breakdown?.confidence_score || 0) * 100)}%
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                      data.confidence_breakdown?.confidence_level === 'HIGH'
                        ? 'text-emerald-300 bg-emerald-950/80 border-emerald-500/40'
                        : data.confidence_breakdown?.confidence_level === 'MEDIUM'
                        ? 'text-amber-300 bg-amber-950/80 border-amber-500/40'
                        : 'text-slate-300 bg-slate-800 border-slate-600'
                    }`}>
                      {data.confidence_breakdown?.confidence_level} CONFIDENCE
                    </span>
                  </div>
                </div>

                {/* Methodology Note */}
                <p className="text-[11px] text-slate-400 italic bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed">
                  {data.confidence_breakdown?.methodology_note}
                </p>

                {/* Observable Signals Table */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-900/80 border-b border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        <th className="py-2 px-3">Observable Evidence Signal</th>
                        <th className="py-2 px-3">Observed Value</th>
                        <th className="py-2 px-3">Signal Interpretation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono text-[11px]">
                      {(data.confidence_breakdown?.observable_signals || []).map((sig, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/40">
                          <td className="py-2 px-3 text-slate-200 font-semibold">{sig.feature_name}</td>
                          <td className="py-2 px-3 text-indigo-300 font-bold">{sig.feature_value}</td>
                          <td className="py-2 px-3 text-slate-400 font-sans text-xs">{sig.signal_interpretation}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Supporting Synthetic Records */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Database size={15} className="text-indigo-400" />
                  <h3 className="font-bold uppercase tracking-wider text-slate-300 text-xs">
                    Corroborating Source Records ({data.supporting_records?.length || 0})
                  </h3>
                </div>

                {(!data.supporting_records || data.supporting_records.length === 0) ? (
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-center text-slate-400">
                    No primary synthetic records explicitly linked to this relationship edge.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {data.supporting_records.map((wrapper, idx) => {
                      if (wrapper.communication) {
                        const comm = wrapper.communication;
                        return (
                          <div key={idx} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1.5 text-indigo-400 font-bold font-mono text-[11px]">
                                <PhoneCall size={13} />
                                {comm.record_id} • {comm.communication_type}
                              </span>
                              <span className="font-mono text-[10px] text-slate-400">{comm.date}</span>
                            </div>
                            <p className="text-slate-300 text-xs font-mono">{comm.summary}</p>
                            <div className="flex gap-4 text-[10px] text-slate-400 font-mono">
                              <span>Source: communications.csv</span>
                              <span>Duration: {comm.duration_seconds}s</span>
                              <span>Case: {comm.case_id}</span>
                            </div>
                          </div>
                        );
                      }

                      if (wrapper.transaction) {
                        const txn = wrapper.transaction;
                        return (
                          <div key={idx} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1.5 text-emerald-400 font-bold font-mono text-[11px]">
                                <CreditCard size={13} />
                                {txn.record_id} • {txn.currency} {txn.amount.toLocaleString()}
                              </span>
                              <span className="font-mono text-[10px] text-slate-400">{txn.date}</span>
                            </div>
                            <p className="text-slate-300 text-xs font-mono">{txn.summary}</p>
                            <div className="flex gap-4 text-[10px] text-slate-400 font-mono">
                              <span>Source: transactions.csv</span>
                              <span>Case: {txn.case_id}</span>
                            </div>
                          </div>
                        );
                      }

                      if (wrapper.case_association) {
                        const cp = wrapper.case_association;
                        return (
                          <div key={idx} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1.5 text-amber-400 font-bold font-mono text-[11px]">
                                <FolderOpen size={13} />
                                Official Case Association • {cp.role}
                              </span>
                              <span className="font-mono text-[10px] text-slate-400">{cp.case_id}</span>
                            </div>
                            <p className="text-slate-300 text-xs font-mono">{cp.summary}</p>
                            <span className="text-[10px] text-slate-400 font-mono block">Source: case_persons.csv</span>
                          </div>
                        );
                      }

                      if (wrapper.metadata_linkage) {
                        const gt = wrapper.metadata_linkage;
                        return (
                          <div key={idx} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1.5 text-purple-400 font-bold font-mono text-[11px]">
                                <FileText size={13} />
                                Verified Registry Linkage • {gt.relationship_type}
                              </span>
                              <span className="font-mono text-[10px] text-slate-400">{gt.record_id}</span>
                            </div>
                            <p className="text-slate-300 text-xs font-mono">{gt.summary}</p>
                            <span className="text-[10px] text-slate-400 font-mono block">Source: ground_truth.csv ({gt.evidence_reference})</span>
                          </div>
                        );
                      }

                      return null;
                    })}
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Safety Disclaimer Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950 text-[11px] text-amber-300/80 flex items-center justify-between">
          <span>⚠️ {data?.safety_disclaimer || "SYNTHETIC DEMONSTRATION DATA • Potential Relationship • Analytical lead only. Human verification required."}</span>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-lg text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
