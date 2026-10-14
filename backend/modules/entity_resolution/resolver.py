import difflib

# Global model instance for reuse
_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def calculate_string_similarity(str1: str, str2: str) -> float:
    if not str1 or not str2:
        return 0.0
    return difflib.SequenceMatcher(None, str1, str2).ratio()

def calculate_embedding_similarity(str1: str, str2: str) -> float:
    if not str1 or not str2:
        return 0.0
    from sklearn.metrics.pairwise import cosine_similarity
    model = get_model()
    embeddings = model.encode([str1, str2])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(max(0.0, sim))

def calculate_attribute_similarity(attrs1: dict, attrs2: dict) -> float:
    if not attrs1 and not attrs2:
        return 0.5 # Neutral score when no attributes available

    shared_keys = set(attrs1.keys()).intersection(set(attrs2.keys()))
    if not shared_keys:
        return 0.5 
    
    total_score = 0.0
    for k in shared_keys:
        if attrs1[k] == attrs2[k]:
            total_score += 1.0
        else:
            sim = calculate_string_similarity(str(attrs1[k]), str(attrs2[k]))
            total_score += sim
            
    return total_score / len(shared_keys)

def entity_resolution_score(
    entity_a: dict, 
    entity_b: dict, 
    threshold_match: float = 0.85, 
    threshold_possible: float = 0.65
) -> dict:
    type_a = entity_a.get("type") or entity_a.get("entity_type")
    type_b = entity_b.get("type") or entity_b.get("entity_type")
    
    # 9. ENTITY-TYPE AWARENESS: Never compare unrelated entity types
    if type_a and type_b and type_a != type_b:
        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "string_similarity": 0.0,
            "embedding_similarity": 0.0,
            "attribute_similarity": 0.0,
            "final_score": 0.0,
            "decision": "NO_MATCH"
        }
    
    val_a = entity_a.get("canonical_value") or entity_a.get("value", "")
    val_b = entity_b.get("canonical_value") or entity_b.get("value", "")
    
    str_sim = calculate_string_similarity(val_a, val_b)
    emb_sim = calculate_embedding_similarity(val_a, val_b)
    
    attrs_a = entity_a.get("attributes", {})
    attrs_b = entity_b.get("attributes", {})
    attr_sim = calculate_attribute_similarity(attrs_a, attrs_b)
    
    # Weights
    w_str = 0.40
    w_emb = 0.40
    w_attr = 0.20
    
    final_score = (str_sim * w_str) + (emb_sim * w_emb) + (attr_sim * w_attr)
    
    if final_score >= threshold_match:
        decision = "MATCH"
    elif final_score >= threshold_possible:
        decision = "POSSIBLE_MATCH"
    else:
        decision = "NO_MATCH"
        
    return {
        "entity_a": entity_a,
        "entity_b": entity_b,
        "string_similarity": str_sim,
        "embedding_similarity": emb_sim,
        "attribute_similarity": attr_sim,
        "final_score": final_score,
        "decision": decision
    }
