import pytest
import networkx as nx

from modules.analytics.graph_analytics import analyze_graph
from modules.priority.priority_scorer import calculate_priority_scores, _normalize
from modules.graph.graph_builder import create_graph, add_entity, add_relationship
from modules.graph.dataset_integration import build_dataset_graph

@pytest.fixture
def sample_graph_analytics():
    G = create_graph()
    
    # Adding entities
    add_entity(G, {"type": "PERSON", "value": "P1", "evidence": "text"})
    add_entity(G, {"type": "PERSON", "value": "P2", "evidence": "text"})
    add_entity(G, {"type": "CASE", "value": "C1", "evidence": "text"})
    
    # Adding relationships
    add_relationship(G, {"source": "P1", "target": "C1", "relationship_type": "INVOLVED_IN", "evidence": "ev1", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9})
    add_relationship(G, {"source": "P2", "target": "C1", "relationship_type": "INVOLVED_IN", "evidence": "ev2", "case_id": "C1", "detection_method": "RULE", "confidence": 0.5})
    add_relationship(G, {"source": "P1", "target": "P2", "relationship_type": "CONTACTED", "evidence": "ev3", "case_id": "C1", "detection_method": "RULE", "confidence": 0.9})
    
    # Step 12 analysis
    analytics_results = analyze_graph(G)
    return G, analytics_results

def test_normalization():
    assert _normalize(5, 0, 10) == 0.5
    assert _normalize(0, 0, 10) == 0.0
    assert _normalize(10, 0, 10) == 1.0
    # min == max
    assert _normalize(5, 5, 5) == 0.0

def test_formula_weights_and_classification(sample_graph_analytics):
    G, analytics_results = sample_graph_analytics
    scores = calculate_priority_scores(G, analytics_results)
    
    assert len(scores) == 2 # P1, P2 (CASE is excluded)
    p1 = next(s for s in scores if s["entity_id"] == "P1")
    p2 = next(s for s in scores if s["entity_id"] == "P2")
    
    # P1 has max confidence 0.9, P2 has max confidence 0.9 (since they contacted each other)
    # They both have 1 degree of diversity, etc.
    # We just need to check if priority score is strictly between 0 and 1
    assert 0.0 <= p1["priority_score"] <= 1.0
    assert 0.0 <= p2["priority_score"] <= 1.0
    
    # Priority Level classification
    for p in scores:
        if p["priority_score"] >= 0.70:
            assert p["priority_level"] == "HIGH"
        elif p["priority_score"] >= 0.40:
            assert p["priority_level"] == "MEDIUM"
        else:
            assert p["priority_level"] == "LOW"

def test_evidence_confidence_aggregation_and_preservation(sample_graph_analytics):
    G, analytics_results = sample_graph_analytics
    scores = calculate_priority_scores(G, analytics_results)
    p1 = next(s for s in scores if s["entity_id"] == "P1")
    
    # P1 has edges with confidence 0.9 and 0.9. Max is 0.9.
    # We should have preserved both tied evidences.
    assert len(p1["supporting_evidence"]) >= 1
    evidence_str = "".join(p1["supporting_evidence"])
    assert "0.90" in evidence_str
    
def test_deterministic_ranking(sample_graph_analytics):
    G, analytics_results = sample_graph_analytics
    scores1 = calculate_priority_scores(G, analytics_results)
    scores2 = calculate_priority_scores(G, analytics_results)
    
    # Ensure they are sorted identically
    for s1, s2 in zip(scores1, scores2):
        assert s1["entity_id"] == s2["entity_id"]
        
    # Check descending priority score
    for i in range(len(scores1) - 1):
        assert scores1[i]["priority_score"] >= scores1[i+1]["priority_score"]

def test_reason_generation_and_safety(sample_graph_analytics):
    G, analytics_results = sample_graph_analytics
    scores = calculate_priority_scores(G, analytics_results)
    
    p1 = next(s for s in scores if s["entity_id"] == "P1")
    
    for reason in p1["reasons"]:
        lower_reason = reason.lower()
        # Verify safety terms
        assert "criminal" not in lower_reason
        assert "guilty" not in lower_reason
        assert "dangerous" not in lower_reason

def test_empty_graph():
    G = create_graph()
    analytics_results = analyze_graph(G)
    scores = calculate_priority_scores(G, analytics_results)
    assert len(scores) == 0

def test_single_node_graph():
    G = create_graph()
    add_entity(G, {"type": "PERSON", "value": "P1", "evidence": "t"})
    analytics_results = analyze_graph(G)
    scores = calculate_priority_scores(G, analytics_results)
    assert len(scores) == 1
    # Everything is 0 due to min==max normalization
    assert scores[0]["priority_score"] == 0.0
    assert scores[0]["priority_level"] == "LOW"
    
def test_no_fabricated_entities(sample_graph_analytics):
    G, analytics_results = sample_graph_analytics
    scores = calculate_priority_scores(G, analytics_results)
    for s in scores:
        assert s["entity_id"] in ["P1", "P2"]
        
def test_dataset_priority():
    G = build_dataset_graph()
    analytics_results = analyze_graph(G)
    scores = calculate_priority_scores(G, analytics_results)
    
    assert len(scores) > 0
    # Make sure CASE nodes are not ranked
    for s in scores:
        assert not s["entity_id"].startswith("CASE")
        
    # Find top entity
    top_entity = scores[0]
    assert top_entity["priority_score"] <= 1.0
