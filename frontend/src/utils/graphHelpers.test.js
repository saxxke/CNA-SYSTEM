import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import {
  buildCytoscapeElements,
  getAvailableTypes,
  filterGraphElements,
  mergeNeighborhoodElements,
  findPathBetweenNodes,
  formatConfidence,
} from './graphHelpers.js';

describe('graphHelpers utilities', () => {
  const sampleGraphData = {
    nodes: [
      { id: 'PERSON_1', label: 'Vikram Singh', type: 'PERSON' },
      { id: 'PERSON_2', label: 'Amit Kumar', type: 'PERSON' },
      { id: 'PHONE_1', label: '+91 9876543210', type: 'PHONE' },
      { id: 'BANK_1', label: 'HDFC-8821', type: 'BANK_ACCOUNT' },
    ],
    edges: [
      {
        id: 'e1',
        source: 'PERSON_1',
        target: 'PHONE_1',
        relationship_type: 'USES',
        confidence: 0.95,
        evidence: 'Subscriber record verified',
        case_id: 'CASE_001',
      },
      {
        id: 'e2',
        source: 'PERSON_1',
        target: 'PERSON_2',
        relationship_type: 'CONTACTED',
        confidence: 0.75,
        evidence: 'Call logs corroborate communication',
        case_id: 'CASE_001',
      },
      {
        id: 'e3',
        source: 'PERSON_2',
        target: 'BANK_1',
        relationship_type: 'TRANSFERRED_TO',
        confidence: 0.88,
        evidence: 'RTGS transfer record',
        case_id: 'CASE_001',
      },
    ],
  };

  test('buildCytoscapeElements maps nodes and edges correctly', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    assert.equal(elements.length, 7); // 4 nodes + 3 edges

    const nodes = elements.filter((e) => !e.data.source);
    const edges = elements.filter((e) => e.data.source);

    assert.equal(nodes.length, 4);
    assert.equal(edges.length, 3);
    assert.equal(nodes[0].data.id, 'PERSON_1');
    assert.equal(edges[0].data.relationship_type, 'USES');
    assert.equal(edges[0].data.confidence, 0.95);
  });

  test('getAvailableTypes counts entity types and relationship types', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    const { entityTypes, relationshipTypes } = getAvailableTypes(elements);

    assert.equal(entityTypes['PERSON'], 2);
    assert.equal(entityTypes['PHONE'], 1);
    assert.equal(entityTypes['BANK_ACCOUNT'], 1);

    assert.equal(relationshipTypes['USES'], 1);
    assert.equal(relationshipTypes['CONTACTED'], 1);
    assert.equal(relationshipTypes['TRANSFERRED_TO'], 1);
  });

  test('filterGraphElements filters by entity types', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    const filtered = filterGraphElements(elements, {
      selectedTypes: ['PERSON'],
      selectedRels: ['ALL'],
    });

    const nodes = filtered.filter((e) => !e.data.source);
    const edges = filtered.filter((e) => e.data.source);

    assert.equal(nodes.length, 2);
    assert.ok(nodes.every((n) => n.data.type === 'PERSON'));
    // Only e2 connects PERSON_1 and PERSON_2; e1 and e3 connect to non-PERSON
    assert.equal(edges.length, 1);
    assert.equal(edges[0].data.id, 'e2');
  });

  test('filterGraphElements filters by relationship type', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    const filtered = filterGraphElements(elements, {
      selectedTypes: ['ALL'],
      selectedRels: ['TRANSFERRED_TO'],
    });

    const edges = filtered.filter((e) => e.data.source);
    assert.equal(edges.length, 1);
    assert.equal(edges[0].data.relationship_type, 'TRANSFERRED_TO');
  });

  test('filterGraphElements filters by minimum confidence', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    const filtered = filterGraphElements(elements, {
      selectedTypes: ['ALL'],
      selectedRels: ['ALL'],
      minConfidence: 0.85,
    });

    const edges = filtered.filter((e) => e.data.source);
    assert.equal(edges.length, 2); // 0.95 and 0.88 pass; 0.75 is excluded
    assert.ok(edges.every((e) => e.data.confidence >= 0.85));
  });

  test('filterGraphElements with filterMode dim retains all elements and adds dimmed class', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    const dimmed = filterGraphElements(elements, {
      selectedTypes: ['PERSON'],
      selectedRels: ['ALL'],
      filterMode: 'dim',
    });

    assert.equal(dimmed.length, elements.length);
    const phoneNode = dimmed.find((e) => e.data.id === 'PHONE_1');
    assert.ok(phoneNode.classes.includes('dimmed'));

    const personNode = dimmed.find((e) => e.data.id === 'PERSON_1');
    assert.equal(personNode.classes, '');
  });

  test('mergeNeighborhoodElements expands 1-hop connections without duplicating existing elements', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    const newEdges = [
      {
        id: 'new_e1',
        source: 'PERSON_2',
        target: 'PHONE_99',
        relationship_type: 'USES',
        confidence: 0.92,
        evidence: 'Discovered SIM linked to same KYC',
      },
      // Existing edge duplicate attempt
      {
        id: 'e2',
        source: 'PERSON_1',
        target: 'PERSON_2',
        relationship_type: 'CONTACTED',
        confidence: 0.75,
      },
    ];

    const { mergedElements, newNodesCount, newEdgesCount } = mergeNeighborhoodElements(
      elements,
      newEdges,
      'PERSON_2'
    );

    assert.equal(newNodesCount, 1); // PHONE_99
    assert.equal(newEdgesCount, 1); // new_e1
    assert.equal(mergedElements.length, elements.length + 2);
  });

  test('findPathBetweenNodes computes shortest path and sequence between nodes', () => {
    const elements = buildCytoscapeElements(sampleGraphData);
    // Path between PERSON_1 and BANK_1: PERSON_1 -> PERSON_2 -> BANK_1
    const path = findPathBetweenNodes(elements, 'PERSON_1', 'BANK_1');

    assert.ok(path);
    assert.equal(path.found, true);
    assert.equal(path.hops, 2);
    assert.deepEqual(path.pathNodes, ['PERSON_1', 'PERSON_2', 'BANK_1']);
    assert.equal(path.pathEdges.length, 2);
    assert.equal(path.pathEdges[0].data.id, 'e2');
    assert.equal(path.pathEdges[1].data.id, 'e3');
  });

  test('findPathBetweenNodes returns null when no path exists', () => {
    const elements = buildCytoscapeElements({
      nodes: [
        { id: 'A', label: 'Node A', type: 'PERSON' },
        { id: 'B', label: 'Node B', type: 'PERSON' },
      ],
      edges: [],
    });

    const path = findPathBetweenNodes(elements, 'A', 'B');
    assert.equal(path, null);
  });

  test('formatConfidence returns correct confidence levels and styles', () => {
    const high = formatConfidence(0.92);
    assert.equal(high.pct, 92);
    assert.equal(high.level, 'HIGH');
    assert.ok(high.colorClass.includes('emerald'));

    const med = formatConfidence(0.65);
    assert.equal(med.pct, 65);
    assert.equal(med.level, 'MEDIUM');
    assert.ok(med.colorClass.includes('amber'));

    const low = formatConfidence(0.4);
    assert.equal(low.pct, 40);
    assert.equal(low.level, 'LOW');
    assert.ok(low.colorClass.includes('slate'));
  });
});
