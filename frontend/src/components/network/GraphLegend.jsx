/**
 * GraphLegend — Compact legend illustrating entity node types, semantic edge styles,
 * and optional interactive filter toggling.
 * 
 * Strict non-accusatory terminology: "Associated Person", "Potential Relationship", "Analytical Lead".
 */
import React, { useState } from 'react';
import { 
  ChevronDown, ChevronUp, Layers, Users, FolderOpen, 
  Smartphone, MessageSquare, Car, MapPin, Building2, CreditCard 
} from 'lucide-react';

const LEGEND_ITEMS = [
  { type: 'PERSON', label: 'Associated Person', icon: Users, color: '#38bdf8', tag: 'Lead', borderClass: 'border-sky-500/40 text-sky-400 bg-sky-950/40' },
  { type: 'CASE', label: 'Case Record', icon: FolderOpen, color: '#818cf8', tag: 'Case File', borderClass: 'border-indigo-500/40 text-indigo-400 bg-indigo-950/40' },
  { type: 'PHONE', label: 'Phone Identifier', icon: Smartphone, color: '#34d399', tag: 'Device', borderClass: 'border-emerald-500/40 text-emerald-400 bg-emerald-950/40' },
  { type: 'WHATSAPP', label: 'WhatsApp / Chat Channel', icon: MessageSquare, color: '#22c55e', tag: 'Channel', borderClass: 'border-green-500/40 text-green-400 bg-green-950/40' },
  { type: 'VEHICLE', label: 'Vehicle Asset', icon: Car, color: '#c084fc', tag: 'Vehicle Reg', borderClass: 'border-purple-500/40 text-purple-400 bg-purple-950/40' },
  { type: 'LOCATION', label: 'Locality / Address', icon: MapPin, color: '#f87171', tag: 'Geo Area', borderClass: 'border-rose-500/40 text-rose-400 bg-rose-950/40' },
  { type: 'ORGANIZATION', label: 'Organization / Business', icon: Building2, color: '#f472b6', tag: 'Business', borderClass: 'border-pink-500/40 text-pink-400 bg-pink-950/40' },
  { type: 'BANK_ACCOUNT', label: 'Bank Account', icon: CreditCard, color: '#fbbf24', tag: 'Financial', borderClass: 'border-amber-500/40 text-amber-400 bg-amber-950/40' },
];

export default function GraphLegend({ activeTypes, onToggleType, typeCounts = {} }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="border border-slate-800 rounded-lg bg-slate-900/90 overflow-hidden select-none">
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-3 py-2 flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 transition-colors"
      >
        <div className="flex items-center gap-1.5">
          <Layers size={13} className="text-indigo-400" />
          <span>Graph Legend & Styles</span>
        </div>
        {collapsed ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
      </button>

      {!collapsed && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-800/80 space-y-2.5 text-xs">
          {/* Node Entities */}
          <div className="space-y-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Node Entities {onToggleType && <span className="text-[9px] font-normal lowercase">(click to toggle)</span>}
            </div>
            {LEGEND_ITEMS.map((item) => {
              const Icon = item.icon;
              const count = typeCounts[item.type];
              const isInactive = activeTypes && !activeTypes.has(item.type);

              return (
                <div
                  key={item.type}
                  onClick={() => onToggleType?.(item.type)}
                  className={`flex items-center justify-between py-1 px-1.5 rounded transition-all ${
                    onToggleType ? 'cursor-pointer hover:bg-slate-800/60' : ''
                  } ${isInactive ? 'opacity-40 line-through' : 'opacity-100'}`}
                  title={onToggleType ? `Toggle ${item.label} filter` : item.label}
                >
                  <div className="flex items-center gap-2 truncate">
                    <div className={`w-5 h-5 rounded flex items-center justify-center border shrink-0 ${item.borderClass}`}>
                      <Icon size={11} />
                    </div>
                    <span className="text-slate-300 text-[11px] font-medium truncate">{item.label}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {count !== undefined && (
                      <span className="font-mono text-[10px] text-slate-400 font-bold">
                        {count}
                      </span>
                    )}
                    <span className="text-[10px] font-mono text-slate-400">{item.tag}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Edge Semantics */}
          <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Relationship Semantics
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-300">
              <div className="flex items-center gap-2">
                <span className="w-5 h-0.5 bg-slate-400 inline-block"></span>
                <span>Corroborated Lead</span>
              </div>
              <span className="text-[10px] text-emerald-400 font-mono">≥ 85% Solid</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-300">
              <div className="flex items-center gap-2">
                <span className="w-5 h-0.5 border-t border-dashed border-slate-400 inline-block"></span>
                <span>Metadata Linkage</span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Administrative</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
            <span>Arrow: Direction</span>
            <span>Click element to inspect</span>
          </div>
        </div>
      )}
    </div>
  );
}
