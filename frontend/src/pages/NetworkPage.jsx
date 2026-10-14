/**
 * NetworkPage — 3-Panel Interactive Network Investigation Workspace.
 *
 * LAYOUT:
 * ┌──────────────┬──────────────────────────────┬──────────────────┐
 * │ Controls     │                              │ Selected Entity  │
 * │              │                              │                  │
 * │ Case         │        NETWORK GRAPH         │ Name             │
 * │ Search       │                              │ Type             │
 * │ Filters      │                              │ Details          │
 * │ Layout       │                              │ Evidence         │
 * │ Zoom         │                              │ Actions          │
 * └──────────────┴──────────────────────────────┴──────────────────┘
 *
 * DATA INTEGRITY:
 * - All nodes and edges come directly from GET /api/cases/{case_id}/graph
 * - No edges, relationships, confidence, or priority are calculated in the frontend
 * - Strictly non-accusatory terminology throughout
 */
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Network, Search, AlertTriangle, Loader2, Filter, 
  Layers, FolderOpen, RefreshCw, ChevronDown, Check, X
} from 'lucide-react';
import api from '../api/client';
import GraphViewer from '../components/network/GraphViewer';
import EntityDetails from '../components/network/EntityDetails';
import GraphLegend from '../components/network/GraphLegend';
import GraphControls from '../components/network/GraphControls';

function buildCytoscapeElements(graphData) {
  if (!graphData) return [];
  const elements = [];

  (graphData.nodes || []).forEach((node) => {
    elements.push({
      data: {
        id: node.id,
        label: node.label || node.id,
        type: node.type || 'UNKNOWN',
      },
    });
  });

  (graphData.edges || []).forEach((edge) => {
    elements.push({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        relationship_type: edge.relationship_type || '',
        confidence: edge.confidence ?? 0,
        evidence: edge.evidence || '',
        case_id: edge.case_id || '',
        detection_method: edge.detection_method || '',
      },
    });
  });

  return elements;
}

export default function NetworkPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const paramCaseId = searchParams.get('caseId') || searchParams.get('case');

  // Case registry
  const [cases, setCases] = useState([]);
  const [casesLoading, setCasesLoading] = useState(true);
  const [casesError, setCasesError] = useState(null);

  // Active Case & Graph data
  const [selectedCaseId, setSelectedCaseId] = useState(paramCaseId || '');
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphError, setGraphError] = useState(null);

  // Selected element (node or edge)
  const [selected, setSelected] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTypeFilter, setSelectedTypeFilter] = useState('ALL');
  const [selectedRelFilter, setSelectedRelFilter] = useState('ALL');

  // Cytoscape ref
  const cyRef = useRef(null);

  // Load cases on mount
  useEffect(() => {
    const loadCases = async () => {
      try {
        setCasesLoading(true);
        const res = await api.get('/api/cases');
        setCases(res.data);
        setCasesError(null);

        // Auto-select requested case or first available
        if (paramCaseId && res.data.some((c) => c.id === paramCaseId)) {
          setSelectedCaseId(paramCaseId);
        } else if (!selectedCaseId && res.data.length > 0) {
          setSelectedCaseId(res.data[0].id);
        }
      } catch (err) {
        setCasesError('Unable to load case records from API.');
      } finally {
        setCasesLoading(false);
      }
    };
    loadCases();
  }, [paramCaseId]);

  // Sync paramCaseId
  useEffect(() => {
    if (paramCaseId && cases.some((c) => c.id === paramCaseId)) {
      setSelectedCaseId(paramCaseId);
    }
  }, [paramCaseId, cases]);

  // Load graph for selected case
  useEffect(() => {
    if (!selectedCaseId) return;

    const loadGraph = async () => {
      try {
        setGraphLoading(true);
        setGraphError(null);
        setSelected(null);
        const res = await api.get(`/api/cases/${selectedCaseId}/graph`);
        setGraphData(res.data);
      } catch (err) {
        setGraphError('Unable to load graph for case record.');
        setGraphData(null);
      } finally {
        setGraphLoading(false);
      }
    };
    loadGraph();
  }, [selectedCaseId]);

  // Derive unique entity types & relationship types present in this case graph
  const { availableTypes, availableRelTypes } = useMemo(() => {
    const types = new Set();
    const rels = new Set();

    (graphData?.nodes || []).forEach((n) => {
      if (n.type) types.add(n.type);
    });
    (graphData?.edges || []).forEach((e) => {
      if (e.relationship_type) rels.add(e.relationship_type);
    });

    return {
      availableTypes: Array.from(types).sort(),
      availableRelTypes: Array.from(rels).sort(),
    };
  }, [graphData]);

  // Filter Cytoscape elements
  const allElements = useMemo(() => buildCytoscapeElements(graphData), [graphData]);

  const filteredElements = useMemo(() => {
    let nodes = allElements.filter((el) => !el.data.source);
    let edges = allElements.filter((el) => el.data.source);

    // Filter by entity type
    if (selectedTypeFilter !== 'ALL') {
      nodes = nodes.filter((n) => n.data.type === selectedTypeFilter);
    }

    // Filter by relationship type
    if (selectedRelFilter !== 'ALL') {
      edges = edges.filter((e) => e.data.relationship_type === selectedRelFilter);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      nodes = nodes.filter(
        (n) =>
          n.data.id?.toLowerCase().includes(q) ||
          n.data.label?.toLowerCase().includes(q) ||
          n.data.type?.toLowerCase().includes(q)
      );
    }

    // Retain only edges whose source and target are still in nodes
    const validNodeIds = new Set(nodes.map((n) => n.data.id));
    edges = edges.filter(
      (e) => validNodeIds.has(e.data.source) && validNodeIds.has(e.data.target)
    );

    return [...nodes, ...edges];
  }, [allElements, selectedTypeFilter, selectedRelFilter, searchQuery]);

  // Layout reset handler
  const handleResetLayout = useCallback(() => {
    if (cyRef.current && cyRef.runLayout) {
      cyRef.runLayout();
    }
  }, []);

  // Center on node by ID
  const handleCenterNode = useCallback((nodeId) => {
    const cy = cyRef.current;
    if (!cy) return;
    const targetNode = cy.$(`node#${nodeId}`);
    if (targetNode.length > 0) {
      cy.fit(targetNode, 80);
      cy.elements().removeClass('dimmed highlighted');
      cy.$(':selected').unselect();
      targetNode.select();
      targetNode.neighborhood().addClass('highlighted');
      cy.elements().not(targetNode).not(targetNode.neighborhood()).addClass('dimmed');
    }
  }, []);

  // Handle double-click navigation
  const handleNodeNavigate = useCallback((nodeData) => {
    if (!nodeData) return;
    if (nodeData.type === 'PERSON') {
      navigate(`/entities/${nodeData.id}`);
    } else if (nodeData.type === 'CASE') {
      navigate(`/cases/${nodeData.id}`);
    }
  }, [navigate]);

  // Selected case metadata
  const currentCase = cases.find((c) => c.id === selectedCaseId);
  const currentCaseTitle = currentCase?.details?.title || currentCase?.details?.case_title || selectedCaseId;

  return (
    <div className="flex-1 flex overflow-hidden h-full bg-slate-950 text-slate-100 select-none">
      {/* ── LEFT PANEL: CONTROLS & FILTERS (270px) ─────────────────────────── */}
      <div className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col h-full shrink-0 overflow-hidden">
        {/* Left Panel Header */}
        <div className="px-4 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network size={16} className="text-indigo-400" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-200">Network Controls</span>
          </div>
          <span className="text-[11px] font-mono font-semibold text-slate-400">
            {graphData?.nodes?.length || 0}N • {graphData?.edges?.length || 0}E
          </span>
        </div>

        {/* Controls Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Case Selector */}
          <div className="space-y-1.5">
            <label htmlFor="case-select" className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <FolderOpen size={13} className="text-indigo-400" /> Case Record
            </label>
            {casesLoading ? (
              <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400">
                <Loader2 size={13} className="animate-spin" /> Loading cases…
              </div>
            ) : casesError ? (
              <div className="text-xs text-red-400 p-2 rounded-lg bg-red-950/40 border border-red-800/50">
                {casesError}
              </div>
            ) : (
              <select
                id="case-select"
                value={selectedCaseId}
                onChange={(e) => {
                  const id = e.target.value;
                  setSelectedCaseId(id);
                  setSearchParams({ caseId: id });
                  setSearchQuery('');
                  setSelectedTypeFilter('ALL');
                  setSelectedRelFilter('ALL');
                }}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 truncate"
              >
                {cases.map((c) => {
                  const title = c.details?.title || c.details?.case_title;
                  const label = title ? `${c.id} — ${title.slice(0, 24)}…` : c.id;
                  return (
                    <option key={c.id} value={c.id}>
                      {label}
                    </option>
                  );
                })}
              </select>
            )}
            {currentCase?.details?.offence_category && (
              <div className="text-[11px] text-slate-400 font-medium px-1 flex items-center justify-between">
                <span>{currentCase.details.offence_category}</span>
                <span className="font-mono text-[10px] text-slate-400">{currentCase.details.status}</span>
              </div>
            )}
          </div>

          {/* Search Nodes */}
          <div className="space-y-1.5">
            <label htmlFor="node-search" className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Search size={13} className="text-indigo-400" /> Filter Nodes
            </label>
            <div className="relative">
              <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                id="node-search"
                type="text"
                placeholder="Search by name, ID, type…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-7 py-1.5 rounded-lg bg-slate-950 border border-slate-700/80 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-0.5"
                >
                  <X size={12} />
                </button>
              )}
            </div>
          </div>

          {/* Filter by Entity Type */}
          <div className="space-y-1.5">
            <label htmlFor="type-filter" className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Filter size={13} className="text-indigo-400" /> Entity Type
            </label>
            <select
              id="type-filter"
              value={selectedTypeFilter}
              onChange={(e) => setSelectedTypeFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Entity Types</option>
              {availableTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Filter by Relationship Type */}
          {availableRelTypes.length > 0 && (
            <div className="space-y-1.5">
              <label htmlFor="rel-filter" className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Layers size={13} className="text-indigo-400" /> Relationship Type
              </label>
              <select
                id="rel-filter"
                value={selectedRelFilter}
                onChange={(e) => setSelectedRelFilter(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="ALL">All Relationship Types</option>
                {availableRelTypes.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Viewport Actions */}
          <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Canvas Controls
            </div>
            <GraphControls cyRef={cyRef} onResetLayout={handleResetLayout} />
          </div>

          {/* Collapsible Entity Legend */}
          <div className="pt-1">
            <GraphLegend />
          </div>
        </div>
      </div>

      {/* ── CENTER PANEL: LARGE GRAPH CANVAS (flex-1) ─────────────────────── */}
      <div className="flex-1 flex flex-col relative h-full overflow-hidden bg-slate-950">
        {/* Canvas Top Bar */}
        <div className="px-4 py-2 bg-slate-900/90 border-b border-slate-800/80 flex items-center justify-between text-xs z-10">
          <div className="flex items-center gap-3 overflow-hidden">
            <span className="font-bold text-slate-200 truncate">
              {selectedCaseId} {currentCaseTitle !== selectedCaseId ? `• ${currentCaseTitle}` : ''}
            </span>
            {(selectedTypeFilter !== 'ALL' || selectedRelFilter !== 'ALL' || searchQuery) && (
              <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px] font-semibold">
                Filters Active
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-slate-400 text-[11px] shrink-0 font-mono">
            <span>Showing {filteredElements.filter(e => !e.data.source).length} nodes, {filteredElements.filter(e => e.data.source).length} edges</span>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 relative overflow-hidden" style={{ minHeight: 0 }}>
          {/* Loading state */}
          {graphLoading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm">
              <Loader2 size={36} className="animate-spin text-indigo-400 mb-3" />
              <p className="text-sm font-semibold text-slate-200">Loading Network Graph…</p>
              <p className="text-xs text-slate-400 mt-1">Retrieving validated relational evidence for {selectedCaseId}</p>
            </div>
          )}

          {/* Error state */}
          {graphError && !graphLoading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center p-8 bg-slate-950">
              <AlertTriangle size={36} className="text-red-400 mb-3" />
              <p className="text-base font-bold text-red-300 mb-1">Graph Data Unavailable</p>
              <p className="text-xs text-slate-400 text-center max-w-sm">{graphError}</p>
            </div>
          )}

          {/* Empty case state */}
          {!graphLoading && !graphError && allElements.length === 0 && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-8 bg-slate-950 text-center">
              <Network size={40} className="text-slate-600 mb-3" />
              <p className="text-base font-bold text-slate-300 mb-1">No Validated Connections Extracted</p>
              <p className="text-xs text-slate-400 max-w-md">
                No relationship edges were extracted or validated for case record {selectedCaseId}.
              </p>
            </div>
          )}

          {/* Filtered to zero */}
          {!graphLoading && !graphError && allElements.length > 0 && filteredElements.length === 0 && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-8 bg-slate-950 text-center">
              <Search size={32} className="text-slate-600 mb-2" />
              <p className="text-sm font-semibold text-slate-300">No Elements Match Filter Criteria</p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedTypeFilter('ALL');
                  setSelectedRelFilter('ALL');
                }}
                className="mt-3 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 hover:bg-indigo-600/40"
              >
                Reset Filters
              </button>
            </div>
          )}

          {/* Cytoscape Graph Canvas */}
          {!graphLoading && !graphError && filteredElements.length > 0 && (
            <GraphViewer
              elements={filteredElements}
              cyRef={cyRef}
              onNodeSelect={(sel) => setSelected(sel)}
              onEdgeSelect={(sel) => setSelected(sel)}
              onNodeNavigate={handleNodeNavigate}
            />
          )}
        </div>
      </div>

      {/* ── RIGHT PANEL: SELECTED ENTITY DOSSIER / SUMMARY (320px) ─────────── */}
      <div className="w-80 bg-slate-950 border-l border-slate-800 flex flex-col h-full shrink-0 overflow-hidden">
        <EntityDetails
          selected={selected}
          graphData={graphData}
          onClose={() => {
            setSelected(null);
            cyRef.current?.$(':selected').unselect();
            cyRef.current?.elements().removeClass('dimmed highlighted');
          }}
          onCenterNode={handleCenterNode}
        />
      </div>
    </div>
  );
}
