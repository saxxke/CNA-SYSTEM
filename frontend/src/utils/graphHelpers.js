/**
 * graphHelpers.js
 * 
 * Pure helper utilities for Cytoscape.js graph manipulation, element filtering,
 * neighborhood expansion merging, and path inspection.
 * 
 * Strict non-accusatory terminology: "Associated Person", "Potential Relationship", "Analytical Lead".
 */

/**
 * Builds standard Cytoscape elements from backend graph response.
 * @param {Object} graphData - { nodes: Array, edges: Array }
 * @returns {Array} Array of Cytoscape element objects
 */
export function buildCytoscapeElements(graphData) {
  if (!graphData) return [];
  const elements = [];
  const seenNodeIds = new Set();

  (graphData.nodes || []).forEach((node) => {
    if (!node || !node.id) return;
    const id = String(node.id);
    if (!seenNodeIds.has(id)) {
      seenNodeIds.add(id);
      elements.push({
        data: {
          id,
          label: node.label || node.id,
          type: node.type || 'UNKNOWN',
          details: node.details || {},
        },
      });
    }
  });

  (graphData.edges || []).forEach((edge, idx) => {
    if (!edge || !edge.source || !edge.target) return;
    const edgeId = edge.id || `e_${edge.source}_${edge.target}_${idx}`;
    elements.push({
      data: {
        id: String(edgeId),
        source: String(edge.source),
        target: String(edge.target),
        relationship_type: edge.relationship_type || 'RELATED_TO',
        confidence: typeof edge.confidence === 'number' ? edge.confidence : 0,
        evidence: edge.evidence || '',
        case_id: edge.case_id || '',
        detection_method: edge.detection_method || '',
      },
    });
  });

  return elements;
}

/**
 * Extracts unique available entity types and relationship types from Cytoscape elements,
 * along with their occurrence counts.
 * @param {Array} elements 
 * @returns {Object} { entityTypes: Object.<string, number>, relationshipTypes: Object.<string, number> }
 */
export function getAvailableTypes(elements) {
  const entityTypes = {};
  const relationshipTypes = {};

  (elements || []).forEach((el) => {
    if (!el || !el.data) return;
    if (!el.data.source) {
      // Node
      const type = el.data.type || 'UNKNOWN';
      entityTypes[type] = (entityTypes[type] || 0) + 1;
    } else {
      // Edge
      const rel = el.data.relationship_type || 'RELATED_TO';
      relationshipTypes[rel] = (relationshipTypes[rel] || 0) + 1;
    }
  });

  return { entityTypes, relationshipTypes };
}

/**
 * Filters elements based on active node type filters, relationship type filters,
 * confidence threshold, and optional search text.
 * 
 * @param {Array} allElements - All Cytoscape elements
 * @param {Object} options
 * @param {Set|Array} [options.selectedTypes] - Active node types (if empty or contains 'ALL', all are included)
 * @param {Set|Array} [options.selectedRels] - Active relationship types (if empty or contains 'ALL', all are included)
 * @param {number} [options.minConfidence=0] - Minimum confidence threshold (0.0 to 1.0)
 * @param {string} [options.searchQuery=''] - Optional text query
 * @returns {Array} Filtered Cytoscape elements with orphan edges safely removed
 */
export function filterGraphElements(allElements, {
  selectedTypes = [],
  selectedRels = [],
  minConfidence = 0,
  searchQuery = '',
  filterMode = 'hide',
} = {}) {
  if (!allElements || allElements.length === 0) return [];

  const typesSet = new Set(Array.isArray(selectedTypes) ? selectedTypes : Array.from(selectedTypes));
  const relsSet = new Set(Array.isArray(selectedRels) ? selectedRels : Array.from(selectedRels));
  const allowAllTypes = typesSet.size === 0 || typesSet.has('ALL');
  const allowAllRels = relsSet.size === 0 || relsSet.has('ALL');
  const query = searchQuery ? searchQuery.toLowerCase().trim() : '';

  // 1. Identify matching nodes
  const isNodeMatching = (el) => {
    const nodeType = el.data.type || 'UNKNOWN';

    // Type filter check
    if (!allowAllTypes && !typesSet.has(nodeType)) {
      return false;
    }

    // Search query check
    if (query) {
      const id = (el.data.id || '').toLowerCase();
      const label = (el.data.label || '').toLowerCase();
      const type = (el.data.type || '').toLowerCase();
      if (!id.includes(query) && !label.includes(query) && !type.includes(query)) {
        return false;
      }
    }

    return true;
  };

  const matchingNodeIds = new Set();
  allElements.forEach((el) => {
    if (!el.data.source && isNodeMatching(el)) {
      matchingNodeIds.add(el.data.id);
    }
  });

  // 2. Identify matching edges
  const isEdgeMatching = (el) => {
    if (!matchingNodeIds.has(el.data.source) || !matchingNodeIds.has(el.data.target)) {
      return false;
    }

    const rel = el.data.relationship_type || '';
    if (!allowAllRels && !relsSet.has(rel)) {
      return false;
    }

    const conf = el.data.confidence ?? 0;
    if (conf < minConfidence) {
      return false;
    }

    return true;
  };

  if (filterMode === 'dim') {
    // Retain all elements, but attach 'dimmed' class to non-matching elements
    return allElements.map((el) => {
      const isNode = !el.data.source;
      const matches = isNode ? matchingNodeIds.has(el.data.id) : isEdgeMatching(el);
      const existingClasses = (el.classes || '').replace(/\bdimmed\b/g, '').trim();

      if (!matches) {
        return {
          ...el,
          classes: existingClasses ? `${existingClasses} dimmed` : 'dimmed',
        };
      }
      return {
        ...el,
        classes: existingClasses,
      };
    });
  }

  // filterMode === 'hide' (default)
  const matchingNodes = allElements.filter((el) => !el.data.source && matchingNodeIds.has(el.data.id));
  const matchingEdges = allElements.filter((el) => el.data.source && isEdgeMatching(el));

  return [...matchingNodes, ...matchingEdges];
}

/**
 * Merges newly discovered 1-hop relationships into the existing Cytoscape elements array,
 * avoiding duplicate nodes or edges.
 * 
 * @param {Array} currentElements - Current Cytoscape elements
 * @param {Array} newEdgesFromApi - Edges returned from /api/entities/{id}/relationships
 * @param {string} focalNodeId - The entity ID that was expanded
 * @returns {{ mergedElements: Array, newNodesCount: number, newEdgesCount: number }}
 */
export function mergeNeighborhoodElements(currentElements, newEdgesFromApi, focalNodeId) {
  if (!newEdgesFromApi || newEdgesFromApi.length === 0) {
    return { mergedElements: currentElements, newNodesCount: 0, newEdgesCount: 0 };
  }

  const existingNodeIds = new Set();
  const existingEdgeKeys = new Set();

  (currentElements || []).forEach((el) => {
    if (!el.data.source) {
      existingNodeIds.add(el.data.id);
    } else {
      const key = `${el.data.source}->${el.data.target}::${el.data.relationship_type || ''}`;
      existingEdgeKeys.add(key);
    }
  });

  const addedNodes = [];
  const addedEdges = [];

  newEdgesFromApi.forEach((edge, idx) => {
    const src = String(edge.source);
    const tgt = String(edge.target);
    const rel = edge.relationship_type || 'RELATED_TO';

    // Check source node
    if (!existingNodeIds.has(src)) {
      existingNodeIds.add(src);
      addedNodes.push({
        data: {
          id: src,
          label: edge.source_label || src,
          type: edge.source_type || inferEntityTypeFromId(src),
          expandedFrom: focalNodeId,
        },
      });
    }

    // Check target node
    if (!existingNodeIds.has(tgt)) {
      existingNodeIds.add(tgt);
      addedNodes.push({
        data: {
          id: tgt,
          label: edge.target_label || tgt,
          type: edge.target_type || inferEntityTypeFromId(tgt),
          expandedFrom: focalNodeId,
        },
      });
    }

    // Check edge uniqueness
    const edgeKey = `${src}->${tgt}::${rel}`;
    if (!existingEdgeKeys.has(edgeKey)) {
      existingEdgeKeys.add(edgeKey);
      const edgeId = edge.id || `expanded_e_${src}_${tgt}_${Date.now()}_${idx}`;
      addedEdges.push({
        data: {
          id: String(edgeId),
          source: src,
          target: tgt,
          relationship_type: rel,
          confidence: typeof edge.confidence === 'number' ? edge.confidence : 0,
          evidence: edge.evidence || '',
          case_id: edge.case_id || '',
          detection_method: edge.detection_method || 'NEIGHBORHOOD_EXPANSION',
        },
      });
    }
  });

  return {
    mergedElements: [...(currentElements || []), ...addedNodes, ...addedEdges],
    newNodesCount: addedNodes.length,
    newEdgesCount: addedEdges.length,
  };
}

/**
 * Infer entity type from common identifier prefixes if missing.
 * @param {string} id 
 * @returns {string}
 */
export function inferEntityTypeFromId(id) {
  if (!id) return 'UNKNOWN';
  const upper = id.toUpperCase();
  if (upper.startsWith('PERSON') || upper.startsWith('P_')) return 'PERSON';
  if (upper.startsWith('CASE') || upper.startsWith('C_')) return 'CASE';
  if (upper.startsWith('PH_') || upper.startsWith('PHONE')) return 'PHONE';
  if (upper.startsWith('WA_') || upper.startsWith('WHATSAPP')) return 'WHATSAPP';
  if (upper.startsWith('ACC_') || upper.startsWith('BANK') || upper.startsWith('BA_')) return 'BANK_ACCOUNT';
  if (upper.startsWith('VEH_') || upper.startsWith('VH_') || upper.startsWith('VEHICLE')) return 'VEHICLE';
  if (upper.startsWith('LOC_') || upper.startsWith('LOCATION')) return 'LOCATION';
  if (upper.startsWith('ORG_') || upper.startsWith('COMPANY')) return 'ORGANIZATION';
  return 'ENTITY';
}

/**
 * Breadth-First-Search pathfinder between two nodes in Cytoscape elements.
 * Returns the shortest path nodes and connecting edges with evidence.
 * 
 * @param {Array} elements - All Cytoscape elements
 * @param {string} startNodeId 
 * @param {string} targetNodeId 
 * @returns {Object|null} Path object { pathNodes: Array, pathEdges: Array, hops: number } or null
 */
export function findPathBetweenNodes(elements, startNodeId, targetNodeId) {
  if (!startNodeId || !targetNodeId || startNodeId === targetNodeId) return null;

  // Build adjacency list (undirected or bidirectional traversal for investigation paths)
  const adj = new Map();

  (elements || []).forEach((el) => {
    if (!el.data.source) {
      if (!adj.has(el.data.id)) adj.set(el.data.id, []);
    } else {
      const u = el.data.source;
      const v = el.data.target;
      if (!adj.has(u)) adj.set(u, []);
      if (!adj.has(v)) adj.set(v, []);
      adj.get(u).push({ neighbor: v, edge: el });
      adj.get(v).push({ neighbor: u, edge: el });
    }
  });

  if (!adj.has(startNodeId) || !adj.has(targetNodeId)) return null;

  // BFS
  const queue = [startNodeId];
  const visited = new Set([startNodeId]);
  const parent = new Map(); // child -> { parent, edge }

  let found = false;

  while (queue.length > 0) {
    const current = queue.shift();
    if (current === targetNodeId) {
      found = true;
      break;
    }

    const neighbors = adj.get(current) || [];
    for (const { neighbor, edge } of neighbors) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        parent.set(neighbor, { parent: current, edge });
        queue.push(neighbor);
      }
    }
  }

  if (!found) return null;

  // Reconstruct path
  const pathNodes = [];
  const pathEdges = [];
  let curr = targetNodeId;

  while (curr !== startNodeId) {
    pathNodes.unshift(curr);
    const pInfo = parent.get(curr);
    if (!pInfo) break;
    pathEdges.unshift(pInfo.edge);
    curr = pInfo.parent;
  }
  pathNodes.unshift(startNodeId);

  return {
    pathNodes,
    pathEdges,
    hops: pathEdges.length,
    found: true,
  };
}

/**
 * Formats a confidence float value (0.0 to 1.0) into level and style tokens.
 * @param {number} value 
 * @returns {Object} { pct: number, level: string, colorClass: string, badgeBg: string }
 */
export function formatConfidence(value) {
  const num = typeof value === 'number' ? value : 0;
  const pct = Math.round(num * 100);

  if (pct >= 80) {
    return {
      pct,
      level: 'HIGH',
      colorClass: 'text-emerald-300 border-emerald-500/40 bg-emerald-950/80',
      badgeBg: 'bg-emerald-500',
    };
  }
  if (pct >= 60) {
    return {
      pct,
      level: 'MEDIUM',
      colorClass: 'text-amber-300 border-amber-500/40 bg-amber-950/80',
      badgeBg: 'bg-amber-500',
    };
  }
  return {
    pct,
    level: 'LOW',
    colorClass: 'text-slate-300 border-slate-600 bg-slate-800',
    badgeBg: 'bg-slate-500',
  };
}
