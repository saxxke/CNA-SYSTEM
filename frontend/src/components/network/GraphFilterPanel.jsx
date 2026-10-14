/**
 * GraphFilterPanel — Multi-faceted entity-type, relationship-type, confidence,
 * and filter-mode controls for the Network Graph.
 * 
 * Strict non-accusatory terminology: "Associated Person", "Potential Relationship", "Analytical Lead".
 */
import React, { useState } from 'react';
import { 
  Filter, Layers, ShieldCheck, ChevronDown, ChevronUp, 
  RotateCcw, CheckSquare, Square, Eye, EyeOff
} from 'lucide-react';

export default function GraphFilterPanel({
  availableTypes = {},
  availableRels = {},
  selectedTypes = new Set(),
  selectedRels = new Set(),
  onToggleType,
  onSelectAllTypes,
  onClearAllTypes,
  onToggleRel,
  onSelectAllRels,
  onClearAllRels,
  minConfidence = 0,
  onChangeMinConfidence,
  filterMode = 'hide',
  onChangeFilterMode,
  onResetFilters,
  hasActiveFilters = false,
}) {
  const [typesCollapsed, setTypesCollapsed] = useState(false);
  const [relsCollapsed, setRelsCollapsed] = useState(false);
  const [confCollapsed, setConfCollapsed] = useState(true);

  const typeEntries = Object.entries(availableTypes).sort(([a], [b]) => a.localeCompare(b));
  const relEntries = Object.entries(availableRels).sort(([a], [b]) => a.localeCompare(b));

  const allTypesSelected = typeEntries.length > 0 && typeEntries.every(([t]) => selectedTypes.has(t));
  const allRelsSelected = relEntries.length > 0 && relEntries.every(([r]) => selectedRels.has(r));

  return (
    <div className="space-y-3 select-none">
      {/* Filter Mode & Reset Bar */}
      <div className="flex items-center justify-between gap-2 pt-1 pb-1">
        <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-[10px]">
          <button
            type="button"
            onClick={() => onChangeFilterMode('hide')}
            className={`px-2 py-1 rounded font-medium flex items-center gap-1 transition-colors ${
              filterMode === 'hide'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Exclude non-matching nodes from the graph layout"
          >
            <EyeOff size={11} />
            <span>Hide Filtered</span>
          </button>
          <button
            type="button"
            onClick={() => onChangeFilterMode('dim')}
            className={`px-2 py-1 rounded font-medium flex items-center gap-1 transition-colors ${
              filterMode === 'dim'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Keep graph topology visible but dim non-matching nodes"
          >
            <Eye size={11} />
            <span>Dim Filtered</span>
          </button>
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={onResetFilters}
            className="flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold text-indigo-300 hover:text-indigo-100 hover:bg-indigo-950/60 border border-indigo-900/50 transition-colors"
            title="Reset all filters to show full case graph"
          >
            <RotateCcw size={10} />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* 1. Entity Type Filters */}
      <div className="border border-slate-800/90 rounded-lg bg-slate-950/60 overflow-hidden">
        <div className="px-3 py-2 bg-slate-900/70 border-b border-slate-800/80 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setTypesCollapsed(!typesCollapsed)}
            className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-300 hover:text-white"
          >
            <Filter size={12} className="text-indigo-400" />
            <span>Entity Types</span>
            <span className="font-mono text-[10px] text-slate-400 font-normal">
              ({selectedTypes.size}/{typeEntries.length})
            </span>
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={allTypesSelected ? onClearAllTypes : onSelectAllTypes}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold"
            >
              {allTypesSelected ? 'None' : 'All'}
            </button>
            <button
              type="button"
              onClick={() => setTypesCollapsed(!typesCollapsed)}
              className="text-slate-400 hover:text-slate-200 p-0.5"
            >
              {typesCollapsed ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
            </button>
          </div>
        </div>

        {!typesCollapsed && (
          <div className="p-2 space-y-1 max-h-48 overflow-y-auto">
            {typeEntries.length === 0 ? (
              <div className="text-[11px] text-slate-400 py-1 px-2 italic">No entity types present</div>
            ) : (
              typeEntries.map(([type, count]) => {
                const isSelected = selectedTypes.has(type);
                return (
                  <button
                    key={type}
                    type="button"
                    onClick={() => onToggleType(type)}
                    className={`w-full flex items-center justify-between px-2 py-1 rounded text-xs transition-colors ${
                      isSelected
                        ? 'bg-slate-900 text-slate-100 font-semibold border border-slate-700/80'
                        : 'text-slate-400 hover:bg-slate-900/40 hover:text-slate-300 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {isSelected ? (
                        <CheckSquare size={13} className="text-indigo-400 shrink-0" />
                      ) : (
                        <Square size={13} className="text-slate-400 shrink-0" />
                      )}
                      <span className="truncate">{type}</span>
                    </div>
                    <span className="font-mono text-[10px] px-1.5 py-0.2 bg-slate-950 text-slate-400 rounded border border-slate-800 shrink-0">
                      {count}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* 2. Relationship Type Filters */}
      <div className="border border-slate-800/90 rounded-lg bg-slate-950/60 overflow-hidden">
        <div className="px-3 py-2 bg-slate-900/70 border-b border-slate-800/80 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setRelsCollapsed(!relsCollapsed)}
            className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-300 hover:text-white"
          >
            <Layers size={12} className="text-indigo-400" />
            <span>Relationship Types</span>
            <span className="font-mono text-[10px] text-slate-400 font-normal">
              ({selectedRels.size}/{relEntries.length})
            </span>
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={allRelsSelected ? onClearAllRels : onSelectAllRels}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold"
            >
              {allRelsSelected ? 'None' : 'All'}
            </button>
            <button
              type="button"
              onClick={() => setRelsCollapsed(!relsCollapsed)}
              className="text-slate-400 hover:text-slate-200 p-0.5"
            >
              {relsCollapsed ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
            </button>
          </div>
        </div>

        {!relsCollapsed && (
          <div className="p-2 space-y-1 max-h-48 overflow-y-auto">
            {relEntries.length === 0 ? (
              <div className="text-[11px] text-slate-400 py-1 px-2 italic">No relationships present</div>
            ) : (
              relEntries.map(([rel, count]) => {
                const isSelected = selectedRels.has(rel);
                return (
                  <button
                    key={rel}
                    type="button"
                    onClick={() => onToggleRel(rel)}
                    className={`w-full flex items-center justify-between px-2 py-1 rounded text-xs transition-colors ${
                      isSelected
                        ? 'bg-slate-900 text-slate-100 font-semibold border border-slate-700/80'
                        : 'text-slate-400 hover:bg-slate-900/40 hover:text-slate-300 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      {isSelected ? (
                        <CheckSquare size={13} className="text-indigo-400 shrink-0" />
                      ) : (
                        <Square size={13} className="text-slate-400 shrink-0" />
                      )}
                      <span className="truncate">{rel}</span>
                    </div>
                    <span className="font-mono text-[10px] px-1.5 py-0.2 bg-slate-950 text-slate-400 rounded border border-slate-800 shrink-0">
                      {count}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* 3. Evidence Confidence Threshold */}
      <div className="border border-slate-800/90 rounded-lg bg-slate-950/60 overflow-hidden">
        <div className="px-3 py-2 bg-slate-900/70 border-b border-slate-800/80 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setConfCollapsed(!confCollapsed)}
            className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-300 hover:text-white"
          >
            <ShieldCheck size={12} className="text-indigo-400" />
            <span>Evidence Confidence</span>
            <span className="font-mono text-[10px] text-slate-400 font-normal">
              {minConfidence > 0 ? `≥ ${Math.round(minConfidence * 100)}%` : 'All'}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setConfCollapsed(!confCollapsed)}
            className="text-slate-400 hover:text-slate-200 p-0.5"
          >
            {confCollapsed ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
          </button>
        </div>

        {!confCollapsed && (
          <div className="p-3 space-y-2">
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Threshold</span>
              <span className="font-mono font-bold text-slate-200">{Math.round(minConfidence * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="0.95"
              step="0.05"
              value={minConfidence}
              onChange={(e) => onChangeMinConfidence(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            />
            <div className="grid grid-cols-4 gap-1 text-[10px] text-center">
              {[0, 0.5, 0.75, 0.9].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onChangeMinConfidence(val)}
                  className={`py-0.5 rounded border transition-colors ${
                    minConfidence === val
                      ? 'bg-indigo-950 text-indigo-300 border-indigo-700 font-bold'
                      : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {val === 0 ? 'All' : `${Math.round(val * 100)}%+`}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
