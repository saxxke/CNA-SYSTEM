import pytest
import networkx as nx

from modules.analytics.graph_analytics import (
    calculate_degree_centrality,
    calculate_betweenness_centrality,
    detect_communities,
    calculate_cross_case_connectivity,
    calculate_community_bridging,
    calculate_relationship_diversity,
    analyze_graph,
    analyze_case_network
)
from modules.graph.graph_builder import create_graph, add_entity, add_relationship
from modules.graph.dataset_integration import build_dataset_graph

@pytest.fixture
def sample_graph():
    G = create_graph()
    
    # Add nodes
    add_entity(G, {"type": "PERSON", "value": "P1", "evidence": "text"})
    add_entity(G, {"type": "PERSON", "value": "P2", "evidence": "text"})
    add_entity(G, {"type": "PERSON", "value": "P3", "evidence": "text"})
    add_entity(G, {"type": "CASE", "value": "C1", "evidence": "text"})
    add_entity(G, {"type": "CASE", "value": "C2", "evidence": "text"})
    
    # P1 connected to C1
    add_relationship(G, {"source": "P1", "target": "C1", "relationship_type": "INVOLVED_IN", "evidence": "text", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9})
    # P1 connected to C2
    add_relationship(G, {"source": "P1", "target": "C2", "relationship_type": "INVOLVED_IN", "evidence": "text", "case_id": "C2", "detection_method": "RULE", "confidence": 0.9})
    # P1 contacts P2
    add_relationship(G, {"source": "P1", "target": "P2", "relationship_type": "CONTACTED", "evidence": "text", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9})
    # P2 connected to C1
    add_relationship(G, {"source": "P2", "target": "C1", "relationship_type": "INVOLVED_IN", "evidence": "text", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9})
    
    # P3 uses some object
    add_entity(G, {"type": "PHONE", "value": "PH1", "evidence": "text"})
    add_relationship(G, {"source": "P3", "target": "PH1", "relationship_type": "USES", "evidence": "text", "case_id": "C2", "detection_method": "RULE", "confidence": 0.9})
    # P1 contacts P3
    add_relationship(G, {"source": "P1", "target": "P3", "relationship_type": "CONTACTED", "evidence": "text", "case_id": "C2", "detection_method": "RULE", "confidence": 0.9})
    
    return G

def test_degree_centrality(sample_graph):
    res = calculate_degree_centrality(sample_graph)
    # P1 connects to C1, C2, P2, P3 -> degree 4
    # Total nodes = 6 (P1, P2, P3, C1, C2, PH1) -> denominator = 5
    # P1 score = 4/5 = 0.8
    p1_res = next(r for r in res if r["entity_id"] == "P1")
    assert p1_res["centrality_score"] > 0
    assert p1_res["entity_type"] == "PERSON"
    # Ensure no criminal terminology
    assert "criminal" not in str(res).lower()

def test_betweenness_centrality(sample_graph):
    res = calculate_betweenness_centrality(sample_graph)
    p1_res = next(r for r in res if r["entity_id"] == "P1")
    # P1 is a bridge between P2/C1 and P3/C2/PH1
    assert p1_res["betweenness_score"] > 0
    
def test_community_detection(sample_graph):
    comms = detect_communities(sample_graph)
    assert len(comms) > 0
    # ensure no fabricated entities
    nodes_in_comms = set()
    for c in comms:
        nodes_in_comms.update(c["entities"])
    
    assert nodes_in_comms == set(sample_graph.nodes())

def test_cross_case_connectivity(sample_graph):
    res = calculate_cross_case_connectivity(sample_graph)
    p1_res = next((r for r in res if r["entity_id"] == "P1"), None)
    assert p1_res is not None
    assert p1_res["case_count"] == 2
    assert set(p1_res["connected_cases"]) == {"C1", "C2"}

def test_community_bridging(sample_graph):
    comms = detect_communities(sample_graph)
    res = calculate_community_bridging(sample_graph, comms)
    # Even if there's only 1 community or 2, verify output structure and nodes
    for r in res:
        assert r["bridge_score"] > 0
        assert len(r["community_ids"]) == r["bridge_score"]
        
def test_relationship_diversity(sample_graph):
    res = calculate_relationship_diversity(sample_graph)
    p1_res = next(r for r in res if r["entity_id"] == "P1")
    # P1 has INVOLVED_IN and CONTACTED (2 types)
    assert p1_res["relationship_type_count"] == 2
    assert set(p1_res["relationship_types"]) == {"INVOLVED_IN", "CONTACTED"}

def test_analyze_graph(sample_graph):
    res = analyze_graph(sample_graph)
    assert "degree_centrality" in res
    assert "betweenness_centrality" in res
    assert "communities" in res
    assert "cross_case_connectivity" in res
    assert "community_bridging" in res
    assert "relationship_diversity" in res

def test_analyze_case_network(sample_graph):
    res = analyze_case_network(sample_graph, "C1")
    # Only P1, P2, C1 should be in C1's subgraph
    nodes = {n["entity_id"] for n in res["degree_centrality"]}
    assert "P1" in nodes
    assert "P2" in nodes
    assert "C1" in nodes
    assert "P3" not in nodes

def test_empty_graph_handling():
    G = create_graph()
    res = analyze_graph(G)
    assert len(res["degree_centrality"]) == 0
    assert len(res["communities"]) == 0

def test_single_node_handling():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "P1", "evidence": "t"})
    res = analyze_graph(G)
    assert len(res["degree_centrality"]) == 1
    assert res["degree_centrality"][0]["centrality_score"] == 1.0

def test_no_edge_graph():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "P1", "evidence": "t"})
    add_entity(G, {"type": "PERSON", "value": "P2", "evidence": "t"})
    res = analyze_graph(G)
    assert len(res["degree_centrality"]) == 2
    assert len(res["communities"]) == 2

def test_deterministic_output(sample_graph):
    res1 = detect_communities(sample_graph)
    res2 = detect_communities(sample_graph)
    assert res1 == res2
    
def test_no_fabricated_entities():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "P1", "evidence": "t"})
    res = analyze_graph(G)
    entities = {x["entity_id"] for x in res["degree_centrality"]}
    assert "P2" not in entities

def test_actual_connectivity_on_dataset():
    # Load actual dataset graph
    G = build_dataset_graph()
    res = analyze_graph(G)
    
    # Verify core analytical metrics are populated on the graph
    cross = res["cross_case_connectivity"]
    assert len(cross) > 0, "Expected cross-case connectivity leads on actual dataset"
    
    dc = res["degree_centrality"]
    assert len(dc) > 0, "Expected degree centrality leads on actual dataset"
    
    btw = res["betweenness_centrality"]
    assert len(btw) > 0, "Expected betweenness centrality leads on actual dataset"
    
    # Verify that leading entities have positive centrality scores and multi-case connectivity
    assert any(r["centrality_score"] > 0 for r in dc)
    assert any(r["betweenness_score"] > 0 for r in btw)
    assert any(r["case_count"] >= 2 for r in cross)
    
    # Ensure safe terminology in keys
    assert "criminal" not in str(res).lower()
    assert "guilty" not in str(res).lower()
