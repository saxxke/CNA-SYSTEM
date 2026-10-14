/**
 * EntityDetails — displays rich dossier details for selected graph elements.
 * When nothing is selected, displays network summary statistics for the active case.
 *
 * DATA INTEGRITY:
 * - Only renders data returned by GET /api/cases/{case_id}/graph
 * - Strictly non-accusatory terminology: "Associated Person", "Potential Relationship", "Analytical Lead"
 * - Does NOT calculate or alter confidence/priority
 */
import React, { useState } from 'react';
import { 
  X, Info, ExternalLink, ShieldAlert, Crosshair, Users, 
  FolderOpen, Phone, Smartphone, CreditCard, Car, Building2, MapPin, 
  FileText, Activity, Link2, Eye, MessageSquare
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { resolveVisualType } from './graphIcons';
import EvidenceProvenanceModal from '../provenance/EvidenceProvenanceModal';

const TYPE_ICONS = {
  CASE: FolderOpen,
  PERSON: Users,
  PHONE: Smartphone,
  WHATSAPP: MessageSquare,
  BANK_ACCOUNT: CreditCard,
  VEHICLE: Car,
  LOCATION: MapPin,
  ORGANIZATION: Building2,
};

function ConfidenceBadge({ value }) {
  const pct = Math.round((value || 0) * 100);
  const color = 
    pct >= 80 ? 'text-emerald-300 bg-emerald-950/80 border-emerald-500/40' :
    pct >= 60 ? 'text-amber-300 bg-amber-950/80 border-amber-500/40' :
    'text-slate-300 bg-slate-800 border-slate-600';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${color}`}>
      {pct}% Confidence
    </span>
  );
}

export default function EntityDetails({ selected, graphData, onClose, onCenterNode }) {
  const navigate = useNavigate();
  const [provenanceOpen, setProvenanceOpen] = useState(false);


  // If nothing is selected, show Case Network Summary
  if (!selected) {
    const nodes = graphData?.nodes || [];
    const edges = graphData?.edges || [];

    // Count by type
    const typeCounts = {};
    nodes.forEach((n) => {
      const t = n.type || 'OTHER';
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });

    return (
      <div className="flex flex-col h-full bg-slate-950 text-slate-200 select-none">
        <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={15} className="text-indigo-400" />
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-300">Case Network Summary</h3>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {/* Quick Metrics */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400">Total Entities</div>
              <div className="text-xl font-mono font-bold text-slate-100 mt-0.5">{nodes.length}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400">Relationships</div>
              <div className="text-xl font-mono font-bold text-slate-100 mt-0.5">{edges.length}</div>
            </div>
          </div>

          {/* Breakdown by Type */}
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              Entity Distribution
            </div>
            <div className="space-y-1.5">
              {Object.entries(typeCounts).map(([type, count]) => {
                const Icon = TYPE_ICONS[type] || Users;
                return (
                  <div key={type} className="flex items-center justify-between px-2.5 py-1.5 rounded bg-slate-900/80 border border-slate-800/80 text-xs">
                    <div className="flex items-center gap-2 text-slate-300 font-medium">
                      <Icon size={13} className="text-slate-400" />
                      <span>{type}</span>
                    </div>
                    <span className="font-mono text-xs font-bold text-slate-200">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Interactive Hint */}
          <div className="p-3 bg-indigo-950/30 border border-indigo-500/20 rounded-lg text-xs text-indigo-200/90 leading-relaxed space-y-1">
            <div className="font-semibold text-indigo-300 flex items-center gap-1.5">
              <Eye size={13} /> Graph Interaction Tip
            </div>
            <p className="text-[11px] text-indigo-200/70">
              Click any node or edge to inspect validated evidence records. Double-click an entity to open its comprehensive investigation profile.
            </p>
          </div>
        </div>

        {/* Bottom Safety Disclaimer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/40 text-[10px] text-amber-300/80">
          ⚠️ Analytical decision-support only. Requires human verification.
        </div>
      </div>
    );
  }

  const { elementType, data } = selected;

  // Render Selected Node
  if (elementType === 'node') {
    const isPerson = data.type === 'PERSON';
    const isCase = data.type === 'CASE';
    const visualType = resolveVisualType(data);
    const Icon = TYPE_ICONS[visualType] || TYPE_ICONS[data.type] || Users;

    return (
      <div className="flex flex-col h-full bg-slate-950 text-slate-200 select-none">
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon size={15} className="text-indigo-400" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-300">Entity Details</span>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 text-slate-400 hover:text-slate-200 rounded hover:bg-slate-800 transition-colors"
            title="Deselect"
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Identity Block */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                {data.type}
              </span>
              <span className="font-mono text-[10px] text-slate-400">{data.id}</span>
            </div>
            <div className="text-sm font-bold text-slate-100">
              {data.label || data.id}
            </div>
          </div>

          {/* Direct Actions */}
          <div className="space-y-2">
            {isPerson && (
              <button
                onClick={() => navigate(`/entities/${data.id}`)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-sm"
              >
                <span>Open Person Investigation Profile</span>
                <ExternalLink size={13} />
              </button>
            )}
            {isCase && (
              <button
                onClick={() => navigate(`/cases/${data.id}`)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-sm"
              >
                <span>Open Case Intelligence Dossier</span>
                <ExternalLink size={13} />
              </button>
            )}
            <button
              onClick={() => onCenterNode?.(data.id)}
              className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 transition-colors"
            >
              <Crosshair size={13} />
              <span>Center in Viewport</span>
            </button>
          </div>

          {/* Metadata rows */}
          <div className="border-t border-slate-800/80 pt-3 space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/40">
              <span className="text-slate-400 font-medium">Identifier</span>
              <span className="font-mono text-slate-200">{data.id}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/40">
              <span className="text-slate-400 font-medium">Category</span>
              <span className="text-slate-200">{data.type}</span>
            </div>
            {data.label && data.label !== data.id && (
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400 font-medium">Display Name</span>
                <span className="text-slate-200 font-semibold">{data.label}</span>
              </div>
            )}
          </div>
        </div>

        {/* Safety Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/40 text-[10px] text-amber-300/80">
          ⚠️ Analytical lead only. Does not imply guilt or criminality.
        </div>
      </div>
    );
  }

  // Render Selected Edge
  if (elementType === 'edge') {
    return (
      <div className="flex flex-col h-full bg-slate-950 text-slate-200 select-none">
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link2 size={15} className="text-indigo-400" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-300">Relationship Evidence</span>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 text-slate-400 hover:text-slate-200 rounded hover:bg-slate-800 transition-colors"
            title="Deselect"
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Relationship Tag & Confidence */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-950 text-indigo-300 border border-indigo-800/60">
                {data.relationship_type || 'RELATIONSHIP'}
              </span>
              <ConfidenceBadge value={data.confidence} />
            </div>
            <div className="text-xs text-slate-300 font-medium flex items-center gap-2">
              <span className="font-mono text-slate-400">{data.source}</span>
              <span className="text-indigo-400">→</span>
              <span className="font-mono text-slate-400">{data.target}</span>
            </div>
          </div>

          {/* Quick Actions to Source / Target */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            {data.source?.startsWith('PERSON') && (
              <button
                onClick={() => navigate(`/entities/${data.source}`)}
                className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-medium truncate text-center"
                title={`Open profile for ${data.source}`}
              >
                View Source Profile
              </button>
            )}
            {data.target?.startsWith('PERSON') && (
              <button
                onClick={() => navigate(`/entities/${data.target}`)}
                className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-medium truncate text-center"
                title={`Open profile for ${data.target}`}
              >
                View Target Profile
              </button>
            )}
          </div>

          {/* Inspect Evidence Provenance Action */}
          <button
            onClick={() => setProvenanceOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-sm"
          >
            <FileText size={13} />
            <span>Inspect Evidence Provenance</span>
          </button>

          {/* Supporting Evidence Text */}
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <FileText size={13} /> Corroborating Evidence
            </div>
            <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-lg text-xs text-slate-300 leading-relaxed font-mono">
              {data.evidence || 'No detailed evidence narrative available.'}
            </div>
          </div>

          {/* Metadata */}
          <div className="border-t border-slate-800/80 pt-3 space-y-1.5 text-xs">
            {data.detection_method && (
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Detection Method</span>
                <span className="text-slate-200 font-mono text-[11px]">{data.detection_method}</span>
              </div>
            )}
            {data.case_id && (
              <div className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-400">Associated Case</span>
                <span className="text-slate-200 font-mono text-[11px]">{data.case_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Safety Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/40 text-[10px] text-amber-300/80">
          ⚠️ Potential relationship only. Human verification required.
        </div>

        {/* Evidence Provenance Modal */}
        <EvidenceProvenanceModal
          isOpen={provenanceOpen}
          onClose={() => setProvenanceOpen(false)}
          sourceId={data.source}
          targetId={data.target}
          caseId={data.case_id}
        />
      </div>
    );
  }

  return null;
}

