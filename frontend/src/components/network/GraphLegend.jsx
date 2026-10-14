/**
 * GraphLegend — compact legend illustrating node types and edge semantics.
 */
import React, { useState } from 'react';
import { 
  ChevronDown, ChevronUp, Layers, Users, FolderOpen, 
  Smartphone, MessageSquare, Car, MapPin, Building2, CreditCard 
} from 'lucide-react';

const LEGEND_ITEMS = [
  { type: 'PERSON', label: 'Associated Person', icon: Users, color: '#38bdf8', tag: 'Primary Lead', borderClass: 'border-sky-500/40 text-sky-400 bg-sky-950/40' },
  { type: 'CASE', label: 'Case Record', icon: FolderOpen, color: '#818cf8', tag: 'Case File', borderClass: 'border-indigo-500/40 text-indigo-400 bg-indigo-950/40' },
  { type: 'PHONE', label: 'Phone Identifier', icon: Smartphone, color: '#34d399', tag: 'Device', borderClass: 'border-emerald-500/40 text-emerald-400 bg-emerald-950/40' },
  { type: 'WHATSAPP', label: 'WhatsApp / Chat Channel', icon: MessageSquare, color: '#22c55e', tag: 'Channel', borderClass: 'border-green-500/40 text-green-400 bg-green-950/40' },
  { type: 'VEHICLE', label: 'Vehicle Asset', icon: Car, color: '#c084fc', tag: 'Vehicle Reg', borderClass: 'border-purple-500/40 text-purple-400 bg-purple-950/40' },
  { type: 'LOCATION', label: 'Locality / Address', icon: MapPin, color: '#f87171', tag: 'Geo Area', borderClass: 'border-rose-500/40 text-rose-400 bg-rose-950/40' },
  { type: 'ORGANIZATION', label: 'Organization / Business', icon: Building2, color: '#f472b6', tag: 'Business', borderClass: 'border-pink-500/40 text-pink-400 bg-pink-950/40' },
  { type: 'BANK_ACCOUNT', label: 'Bank Account', icon: CreditCard, color: '#fbbf24', tag: 'Financial', borderClass: 'border-amber-500/40 text-amber-400 bg-amber-950/40' },
];

export default function GraphLegend() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="border border-slate-800 rounded-lg bg-slate-900/90 overflow-hidden select-none">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-3 py-2 flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 transition-colors"
      >
        <div className="flex items-center gap-1.5">
          <Layers size={13} className="text-indigo-400" />
          <span>Entity Legend</span>
        </div>
        {collapsed ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
      </button>

      {!collapsed && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-800/80 space-y-2 text-xs">
          {LEGEND_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.type} className="flex items-center justify-between py-0.5">
                <div className="flex items-center gap-2">
                  <div className={`w-5 h-5 rounded flex items-center justify-center border ${item.borderClass}`}>
                    <Icon size={11} />
                  </div>
                  <span className="text-slate-300 text-[11px] font-medium">{item.label}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">{item.tag}</span>
              </div>
            );
          })}
          <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
            <span>Edge Arrow: Target</span>
            <span>Click: Inspect Dossier</span>
          </div>
        </div>
      )}
    </div>
  );
}
