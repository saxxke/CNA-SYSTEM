import os
import sys
import networkx as nx

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.graph.graph_builder import (
    create_graph, add_entity, add_relationship, get_entity, 
    get_neighbors, get_case_subgraph, find_shortest_path, 
    find_related_cases, get_graph_statistics
)
from modules.graph.dataset_integration import build_dataset_graph

def test_graph_creation():
    G = create_graph()
    assert isinstance(G, nx.MultiDiGraph)
    assert len(G) == 0

def test_node_insertion():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "PERSON-123", "evidence": "John Doe"})
    assert G.has_node("PERSON-123")
    node = get_entity(G, "PERSON-123")
    assert node["type"] == "PERSON"
    assert node["label"] == "PERSON-123"
    assert node["evidence"] == "John Doe"

def test_node_type_validation():
    G = create_graph()
    # Invalid type
    add_entity(G, {"type": "INVALID_TYPE", "value": "123"})
    assert not G.has_node("123")
    # CASE_ID mapping to CASE
    add_entity(G, {"type": "CASE_ID", "value": "CASE-999"})
    node = get_entity(G, "CASE-999")
    assert node is not None
    assert node["type"] == "CASE"

def test_relationship_insertion_and_validation():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "P1"})
    add_entity(G, {"type": "PERSON", "value": "P2"})
    
    # Valid relationship
    add_relationship(G, {
        "source": "P1", "target": "P2", "relationship_type": "CONTACTED",
        "evidence": "P1 called P2", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9
    })
    assert G.has_edge("P1", "P2")
    
    # Invalid relationship type
    add_relationship(G, {
        "source": "P1", "target": "P2", "relationship_type": "INVALID",
        "evidence": "P1 invalid P2", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9
    })
    edges = G.get_edge_data("P1", "P2")
    assert len(edges) == 1 # Only the valid one exists
    
    # Missing source/target node in graph
    add_relationship(G, {
        "source": "P3", "target": "P4", "relationship_type": "CONTACTED",
        "evidence": "P3 called P4", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9
    })
    assert not G.has_node("P3")
    assert not G.has_node("P4")

def test_duplicate_relationship_handling():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "P1"})
    add_entity(G, {"type": "PERSON", "value": "P2"})
    
    add_relationship(G, {
        "source": "P1", "target": "P2", "relationship_type": "CONTACTED",
        "evidence": "First call", "case_id": "C1", "detection_method": "RULE", "confidence": 0.8
    })
    add_relationship(G, {
        "source": "P1", "target": "P2", "relationship_type": "CONTACTED",
        "evidence": "Second call", "case_id": "C1", "detection_method": "RULE", "confidence": 0.95
    })
    
    edges = G.get_edge_data("P1", "P2")
    assert len(edges) == 1 # Merged into one edge
    edge_data = list(edges.values())[0]
    assert "First call" in edge_data["evidence"]
    assert "Second call" in edge_data["evidence"]
    assert edge_data["confidence"] == 0.95 # Max confidence preserved

def test_neighbors_and_subgraph():
    G = create_graph()
    for n in ["A", "B", "C"]:
        add_entity(G, {"type": "PERSON", "value": n})
        
    add_relationship(G, {"source": "A", "target": "B", "relationship_type": "CONTACTED", "evidence": "X", "case_id": "CASE-1", "detection_method": "R", "confidence": 0.9})
    add_relationship(G, {"source": "B", "target": "C", "relationship_type": "CONTACTED", "evidence": "X", "case_id": "CASE-2", "detection_method": "R", "confidence": 0.9})
    
    assert len(get_neighbors(G, "B", "both")) == 2
    assert len(get_neighbors(G, "B", "outgoing")) == 1 # C
    
    subgraph = get_case_subgraph(G, "CASE-1")
    assert subgraph.number_of_nodes() == 2 # A and B
    assert not subgraph.has_node("C")

def test_shortest_path():
    G = create_graph()
    for n in ["A", "B", "C"]:
        add_entity(G, {"type": "PERSON", "value": n})
    add_relationship(G, {"source": "A", "target": "B", "relationship_type": "CONTACTED", "evidence": "X", "case_id": "C1", "detection_method": "R", "confidence": 0.9})
    add_relationship(G, {"source": "B", "target": "C", "relationship_type": "CONTACTED", "evidence": "X", "case_id": "C1", "detection_method": "R", "confidence": 0.9})
    
    path = find_shortest_path(G, "A", "C")
    assert path == ["A", "B", "C"]
    
    # Verify undirected nature of search
    path_rev = find_shortest_path(G, "C", "A")
    assert path_rev == ["C", "B", "A"]

def test_related_cases():
    G = create_graph()
    for n in ["P1", "P2", "P3"]: add_entity(G, {"type": "PERSON", "value": n})
    
    add_relationship(G, {"source": "P1", "target": "P2", "relationship_type": "CONTACTED", "evidence": "E1", "case_id": "CASE-A", "detection_method": "R", "confidence": 0.9})
    add_relationship(G, {"source": "P2", "target": "P3", "relationship_type": "CONTACTED", "evidence": "E2", "case_id": "CASE-B", "detection_method": "R", "confidence": 0.9})
    
    related = find_related_cases(G, "CASE-A")
    assert "CASE-B" in related

def test_graph_statistics():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "A"})
    add_entity(G, {"type": "PERSON", "value": "B"})
    add_relationship(G, {"source": "A", "target": "B", "relationship_type": "CONTACTED", "evidence": "E", "case_id": "C1", "detection_method": "R", "confidence": 0.9})
    
    stats = get_graph_statistics(G)
    assert stats["node_count"] == 2
    assert stats["edge_count"] == 1
    assert stats["node_types"].get("PERSON") == 2
    assert stats["edge_types"].get("CONTACTED") == 1

def test_dataset_integration_path():
    G = build_dataset_graph()
    
    # Must find structured association connecting persons to cases from case_persons.csv
    assert G.has_edge("PERSON-001", "CASE-001") or G.has_edge("CASE-001", "PERSON-001")
    edge_data = G.get_edge_data("PERSON-001", "CASE-001")
    assert edge_data is not None
    # Verify structured metadata association provenance
    assert any("case_persons.csv" in str(d.get("evidence", "")) for d in edge_data.values())
    
    # Verify related cases discovered via shared entities purely from data
    related = find_related_cases(G, "CASE-001")
    assert "CASE-002" in related
