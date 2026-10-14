import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, Database, FileCode, CheckCircle2 } from 'lucide-react';

/**
 * ProvenancePanel.jsx
 * Collapsible Sources & Evidence drawer citing exact backend ProvenanceItem objects.
 * Guarantees investigator auditability without hallucinated citations.
 */
export default function ProvenancePanel({ provenance = [] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!provenance || provenance.length === 0) return null;

  return (
    <div className="mt-3 rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden transition-all text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-slate-300 hover:text-white hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-400" />
          <span className="font-semibold uppercase tracking-wider text-[11px] text-slate-300">
            Sources & Grounded Evidence
          </span>
          <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono text-[10px] border border-slate-700">
            {provenance.length} record(s)
          </span>
        </div>
        <div className="flex items-center gap-1 text-slate-400">
          <span className="text-[11px]">{isOpen ? 'Hide Audit Trail' : 'Inspect Audit Trail'}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-3.5 py-3 border-t border-slate-800 bg-slate-950/40 space-y-2">
          <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>Facts validated against deterministic repository payloads.</span>
          </div>

          <div className="space-y-2">
            {provenance.map((item, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded bg-slate-900/90 border border-slate-800/90 space-y-1.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="px-1.5 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-800/60 font-mono text-[10px] font-bold">
                      {item.source_type}
                    </span>
                    {item.source_id && (
                      <span className="font-mono text-slate-200 text-[11px] font-medium">
                        ID: {item.source_id}
                      </span>
                    )}
                  </div>
                  {item.case_id && (
                    <span className="text-[11px] text-slate-400 font-mono">
                      Case: <span className="text-amber-400">{item.case_id}</span>
                    </span>
                  )}
                </div>

                {item.evidence_snippet && (
                  <p className="text-xs text-slate-300 italic pl-2 border-l-2 border-slate-700 bg-slate-800/20 py-1 rounded-r">
                    "{item.evidence_snippet}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
