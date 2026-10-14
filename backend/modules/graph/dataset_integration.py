import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data.validate_dataset import load_csv
from modules.extraction.entity_extractor import extract_entities
from modules.relationships.relationship_extractor import extract_relationships
from modules.ml.relationship_confidence import predict_confidence
from modules.graph.graph_builder import create_graph, add_entity, add_relationship

def extract_synthetic_ids(text):
    """
    Adapter helper to extract synthetic dataset IDs (PERSON-001, PHONE-004, etc.)
    that generic spaCy NER or generic formatting regex naturally misses.
    """
    extracted = []
    
    patterns = {
        "PERSON": r'\bPERSON-\d{3}(?:-V\d)?\b',
        "LOCATION": r'\bLOCATION-\d{3}(?:-V\d)?\b',
        "ORGANIZATION": r'\bORG-\d{3}(?:-V\d)?\b',
        "PHONE": r'\bPHONE-\d{3}(?:-V\d)?\b',
        "BANK_ACCOUNT": r'\bBANK-\d{3}(?:-V\d)?\b',
        "VEHICLE": r'\bVEHICLE-\d{3}(?:-V\d)?\b',
        "CASE_ID": r'\bCASE-\d{3}\b'
    }
    
    for ent_type, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            extracted.append({"type": ent_type, "value": match.group(), "evidence": match.group(), "source": "SYNTHETIC_ID"})
            
    return extracted

def get_type_from_id(entity_id):
    if entity_id.startswith("PERSON"): return "PERSON"
    if entity_id.startswith("CASE"): return "CASE_ID"
    if entity_id.startswith("PHONE"): return "PHONE"
    if entity_id.startswith("BANK"): return "BANK_ACCOUNT"
    if entity_id.startswith("VEHICLE"): return "VEHICLE"
    if entity_id.startswith("LOCATION"): return "LOCATION"
    if entity_id.startswith("ORG"): return "ORGANIZATION"
    return "UNKNOWN"

def get_case_inventory():
    """Returns the full inventory of synthetic cases."""
    return load_csv("cases.csv") or []

def build_dataset_graph():
    """
    Builds the NetworkX graph by running the actual dataset through
    Step 9 (relationship extraction) and Step 10 (relationship confidence).
    """
    G = create_graph()
    
    # Load synthetic dataset
    comms = load_csv("communications.csv")
    txns = load_csv("transactions.csv")
    gt = load_csv("ground_truth.csv")
    
    texts_with_context = []
    
    if comms:
        for row in comms:
            case_id = row.get("case_id", "")
            rec_id = row.get("communication_id", "")
            texts_with_context.append((row.get("description", ""), case_id, rec_id))
            
    if txns:
        for row in txns:
            case_id = row.get("case_id", "")
            rec_id = row.get("transaction_id", "")
            texts_with_context.append((row.get("description", ""), case_id, rec_id))

    # Process unstructured text records
    for text, case_id, rec_id in texts_with_context:
        if not text:
            continue
            
        # 1. Extract entities via existing pipeline
        entities = extract_entities(text)
        
        # 1b. Adapter: Inject synthetic IDs missed by generic NLP / Regex
        synthetic_entities = extract_synthetic_ids(text)
        existing_vals = {e["value"] for e in entities}
        for se in synthetic_entities:
            if se["value"] not in existing_vals:
                entities.append(se)
                existing_vals.add(se["value"])
        
        # Add extracted entities to graph
        for ent in entities:
            add_entity(G, ent)
            
        # 2. Extract relationships (Step 9)
        rels = extract_relationships(text, entities, case_id)
        
        # 3. Predict confidence (Step 10) and add to graph (Step 11)
        for rel in rels:
            if rec_id:
                rel["record_ids"] = [rec_id]
            try:
                conf_result = predict_confidence(rel)
                rel["confidence"] = conf_result.get("relationship_confidence", 0.85)
                rel["features"] = conf_result.get("features", {})
            except Exception:
                rel["confidence"] = 0.85
                rel["features"] = {}
                
            add_relationship(G, rel)

    # Process structured metadata directly (avoiding fabricated text)
    if gt:
        for row in gt:
            if row.get("relationship_type") == "INVOLVED_IN" and row.get("evidence_reference") in ("cases.csv", "case_persons.csv"):
                source = row.get("source_entity_id")
                target = row.get("target_entity_id")
                gt_id = row.get("ground_truth_id", "")
                
                # Ensure entities exist in the graph
                add_entity(G, {"type": get_type_from_id(source), "value": source, "evidence": source, "source": "STRUCTURED_METADATA"})
                add_entity(G, {"type": get_type_from_id(target), "value": target, "evidence": target, "source": "STRUCTURED_METADATA"})
                
                # Create direct structured relationship
                ev_ref = row.get("evidence_reference", "case_persons.csv")
                rel = {
                    "source": source,
                    "target": target,
                    "relationship_type": "INVOLVED_IN",
                    "evidence": f"Structured metadata association from {ev_ref}",
                    "case_id": target if target.startswith("CASE") else source if source.startswith("CASE") else "",
                    "detection_method": "STRUCTURED_METADATA",
                    "record_ids": [gt_id] if gt_id else []
                }
                
                # Still respect Step 10 confidence predictions for the edge
                try:
                    conf_result = predict_confidence(rel)
                    rel["confidence"] = conf_result.get("relationship_confidence", 0.85)
                    rel["features"] = conf_result.get("features", {})
                except Exception:
                    rel["confidence"] = 0.85
                    rel["features"] = {}
                    
                add_relationship(G, rel)

    # Process all case_persons records (including runtime) to guarantee restart persistence
    all_case_persons = load_csv("case_persons.csv") or []
    for cp in all_case_persons:
        cid = cp.get("case_id")
        pid = cp.get("person_id")
        role = cp.get("role", "SUBJECT")
        cp_id = f"CP-{cid}-{pid}"
        if cid and pid:
            add_entity(G, {"type": "CASE_ID", "value": cid, "evidence": cid, "source": "STRUCTURED_METADATA", "confidence": 1.0})
            add_entity(G, {"type": "PERSON", "value": pid, "evidence": pid, "source": "STRUCTURED_METADATA", "confidence": 1.0})
            if not G.has_edge(cid, pid):
                add_relationship(G, {
                    "source": cid,
                    "target": pid,
                    "relationship_type": "INVOLVED_IN",
                    "evidence": f"Structured metadata association from case_persons.csv as {role}",
                    "case_id": cid,
                    "detection_method": "STRUCTURED_METADATA",
                    "confidence": 1.0,
                    "record_ids": [cp_id]
                })
            
    return G
