import re

RELATIONSHIP_TYPES = {
    "INVOLVED_IN": [r'was involved in', r'linked to case', r'participated in', r'involved in'],
    "USES": [r'used', r'using', r'operated', r'accessed'],
    "CONTACTED": [r'contacted', r'called', r'spoke to', r'communicated with'],
    "OWNS": [r'owns', r'owned by', r'registered to'],
    "TRANSFERRED_TO": [r'transferred', r'sent funds to', r'paid'],
    "LOCATED_AT": [r'located at', r'was at', r'present at'],
    "WORKS_FOR": [r'works for', r'employed by', r'associated with'],
    "RELATED_TO": [r'related to']
}

def extract_relationships(text: str, entities: list, case_id: str = None) -> list:
    """
    Extracts relationships from text between provided entities using deterministic rules.
    Only creates relationships when both entities are present in the text and connected by a keyword.
    Co-occurrence alone is not sufficient.
    """
    if not text or not entities or len(entities) < 2:
        return []

    relationships = []
    
    # Simple segmentation: just use newlines or treat as single block for MVP.
    # The 120-char between_text limit naturally prevents cross-sentence false positives.
    sentences = [s.strip() for s in text.split('\n') if s.strip()]
    
    for sentence in sentences:
        sentence_entities = []
        for ent in entities:
            evidence = ent.get("evidence", "")
            if evidence and evidence in sentence:
                sentence_entities.append(ent)
                
        if len(sentence_entities) < 2:
            continue
            
        # Check all directed pairs in the sentence
        for i in range(len(sentence_entities)):
            for j in range(len(sentence_entities)):
                if i == j:
                    continue
                ent_a = sentence_entities[i]
                ent_b = sentence_entities[j]
                
                val_a = ent_a.get("evidence", "")
                val_b = ent_b.get("evidence", "")
                
                # Check for: Entity A [relationship keyword] Entity B
                idx_a = sentence.find(val_a)
                idx_b = sentence.find(val_b, idx_a + len(val_a))
                
                if idx_a != -1 and idx_b != -1 and idx_a < idx_b:
                    between_text = sentence[idx_a + len(val_a) : idx_b]
                    
                    # Require entities to be somewhat close in the sentence to avoid false links
                    if len(between_text) > 120:
                        continue
                        
                    matched = False
                    for rel_type, keywords in RELATIONSHIP_TYPES.items():
                        if matched: break
                        
                        for kw in keywords:
                            if re.search(r'\b' + kw + r'\b', between_text.lower()):
                                # Special passive cases where target acts on source
                                source = ent_a
                                target = ent_b
                                
                                # "A owned by B" -> "B OWNS A"
                                # "A employed by B" -> "A WORKS_FOR B" (no swap)
                                if kw in ["owned by"]:
                                    source = ent_b
                                    target = ent_a
                                
                                rel = {
                                    "source": source.get("value"),
                                    "target": target.get("value"),
                                    "relationship_type": rel_type,
                                    "evidence": sentence.strip(),
                                    "case_id": case_id,
                                    "detection_method": "RULE"
                                }
                                relationships.append(rel)
                                matched = True
                                break

    # Deduplicate relationships exactly as required
    unique_rels = {}
    for r in relationships:
        key = (r["source"], r["target"], r["relationship_type"], r["case_id"])
        if key not in unique_rels:
            unique_rels[key] = r
            
    return list(unique_rels.values())

def extract_relationships_llm_assisted(text: str, entities: list, case_id: str = None) -> list:
    """
    Optional LLM assistance pathway (stub for MVP).
    LLM must not directly create graph edges. Suggestions must pass validation.
    """
    # For MVP, fallback strictly to rule-based execution.
    # Even if LLM were implemented, it would just suggest pairs and we'd validate the span.
    return extract_relationships(text, entities, case_id)
