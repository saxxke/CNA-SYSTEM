import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.relationships.relationship_extractor import extract_relationships, extract_relationships_llm_assisted
from data.validate_dataset import load_csv

def test_contacted():
    text = "PERSON-017 contacted PERSON-043 using PHONE-004."
    entities = [
        {"type": "PERSON", "value": "PERSON-017", "evidence": "PERSON-017"},
        {"type": "PERSON", "value": "PERSON-043", "evidence": "PERSON-043"}
    ]
    rels = extract_relationships(text, entities, "CASE-001")
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "CONTACTED"
    assert rels[0]["source"] == "PERSON-017"
    assert rels[0]["target"] == "PERSON-043"
    assert rels[0]["case_id"] == "CASE-001"
    assert rels[0]["detection_method"] == "RULE"

def test_uses():
    text = "PERSON-017 used PHONE-004 for the operation."
    entities = [
        {"type": "PERSON", "value": "PERSON-017", "evidence": "PERSON-017"},
        {"type": "PHONE", "value": "PHONE-004", "evidence": "PHONE-004"}
    ]
    rels = extract_relationships(text, entities)
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "USES"
    
def test_transferred_to():
    text = "PERSON-A sent funds to PERSON-B."
    entities = [
        {"type": "PERSON", "value": "PERSON-A", "evidence": "PERSON-A"},
        {"type": "PERSON", "value": "PERSON-B", "evidence": "PERSON-B"}
    ]
    rels = extract_relationships(text, entities)
    assert rels[0]["relationship_type"] == "TRANSFERRED_TO"

def test_owns_passive():
    text = "VEHICLE-01 is owned by PERSON-C."
    entities = [
        {"type": "VEHICLE", "value": "VEHICLE-01", "evidence": "VEHICLE-01"},
        {"type": "PERSON", "value": "PERSON-C", "evidence": "PERSON-C"}
    ]
    rels = extract_relationships(text, entities)
    assert rels[0]["relationship_type"] == "OWNS"
    assert rels[0]["source"] == "PERSON-C" # Reverse directed
    assert rels[0]["target"] == "VEHICLE-01"

def test_located_at():
    text = "PERSON-A was present at LOCATION-B."
    entities = [
        {"type": "PERSON", "value": "PERSON-A", "evidence": "PERSON-A"},
        {"type": "LOCATION", "value": "LOCATION-B", "evidence": "LOCATION-B"}
    ]
    rels = extract_relationships(text, entities)
    assert rels[0]["relationship_type"] == "LOCATED_AT"

def test_works_for():
    text = "PERSON-X is employed by ORG-Y."
    entities = [
        {"type": "PERSON", "value": "PERSON-X", "evidence": "PERSON-X"},
        {"type": "ORGANIZATION", "value": "ORG-Y", "evidence": "ORG-Y"}
    ]
    rels = extract_relationships(text, entities)
    assert rels[0]["relationship_type"] == "WORKS_FOR"
    assert rels[0]["source"] == "PERSON-X"
    assert rels[0]["target"] == "ORG-Y"

def test_involved_in():
    text = "PERSON-Z was involved in CASE-123."
    entities = [
        {"type": "PERSON", "value": "PERSON-Z", "evidence": "PERSON-Z"},
        {"type": "CASE_ID", "value": "CASE-123", "evidence": "CASE-123"}
    ]
    rels = extract_relationships(text, entities)
    assert rels[0]["relationship_type"] == "INVOLVED_IN"

def test_related_to():
    text = "PERSON-M is related to PERSON-N."
    entities = [
        {"type": "PERSON", "value": "PERSON-M", "evidence": "PERSON-M"},
        {"type": "PERSON", "value": "PERSON-N", "evidence": "PERSON-N"}
    ]
    rels = extract_relationships(text, entities)
    assert rels[0]["relationship_type"] == "RELATED_TO"

def test_insufficient_evidence_and_cooccurrence():
    # Co-occurrence without relationship keyword
    text = "PERSON-017 and PERSON-043 were both mentioned in the report."
    entities = [
        {"type": "PERSON", "value": "PERSON-017", "evidence": "PERSON-017"},
        {"type": "PERSON", "value": "PERSON-043", "evidence": "PERSON-043"}
    ]
    rels = extract_relationships(text, entities)
    # Must NOT create a relationship
    assert len(rels) == 0

def test_missing_entities():
    # Only one entity provided
    text = "PERSON-017 contacted someone."
    entities = [
        {"type": "PERSON", "value": "PERSON-017", "evidence": "PERSON-017"}
    ]
    rels = extract_relationships(text, entities)
    assert len(rels) == 0

def test_duplicate_handling():
    # Multiple keywords in same sentence
    text = "PERSON-A called and spoke to PERSON-B."
    entities = [
        {"type": "PERSON", "value": "PERSON-A", "evidence": "PERSON-A"},
        {"type": "PERSON", "value": "PERSON-B", "evidence": "PERSON-B"}
    ]
    rels = extract_relationships(text, entities)
    # Should only return one CONTACTED relationship
    assert len(rels) == 1
    assert rels[0]["relationship_type"] == "CONTACTED"

def test_evidence_preservation():
    text = "Mr. John contacted Mr. Smith."
    entities = [
        {"type": "PERSON", "value": "John", "evidence": "John"},
        {"type": "PERSON", "value": "Smith", "evidence": "Smith"}
    ]
    rels = extract_relationships(text, entities)
    assert "John contacted Mr. Smith" in rels[0]["evidence"]

def test_llm_unavailable_behavior():
    # Calling the LLM assisted stub should gracefully fallback to rules for MVP
    text = "PERSON-017 contacted PERSON-043."
    entities = [
        {"type": "PERSON", "value": "PERSON-017", "evidence": "PERSON-017"},
        {"type": "PERSON", "value": "PERSON-043", "evidence": "PERSON-043"}
    ]
    rels = extract_relationships_llm_assisted(text, entities, "CASE-001")
    assert len(rels) == 1
    assert rels[0]["detection_method"] == "RULE"

def test_dataset_integration():
    # Verify behavior on actual synthetic dataset communications
    from modules.extraction.entity_extractor import extract_entities
    
    comms = load_csv("communications.csv")
    if not comms:
        return
        
    sample_text = comms[0]["description"]
    entities = extract_entities(sample_text)
    person_entities = [e for e in entities if e["type"] == "PERSON"]
    assert len(person_entities) >= 2, "Expected at least 2 PERSON entities in human-readable description"
    
    rels = extract_relationships(sample_text, entities)
    # Should identify CONTACTED
    assert len(rels) >= 1
    assert any(r["relationship_type"] == "CONTACTED" for r in rels)
