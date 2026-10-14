import networkx as nx

def _normalize(value: float, min_val: float, max_val: float) -> float:
    """
    Min-Max normalization. Returns 0.0 if max == min.
    """
    if max_val == min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)

def _get_max_confidence_evidence(G: nx.MultiDiGraph, entity_id: str):
    """
    Extracts the max confidence from all incident edges and preserves
    all edge evidence data tied for that max confidence.
    """
    max_conf = 0.0
    tied_evidence = []
    
    # Check all outgoing edges
    for u, v, data in G.out_edges(entity_id, data=True):
        conf = data.get("confidence", 0.0)
        if conf > max_conf:
            max_conf = conf
            tied_evidence = [data]
        elif conf == max_conf and max_conf > 0.0:
            tied_evidence.append(data)
            
    # Check all incoming edges
    for u, v, data in G.in_edges(entity_id, data=True):
        conf = data.get("confidence", 0.0)
        if conf > max_conf:
            max_conf = conf
            tied_evidence = [data]
        elif conf == max_conf and max_conf > 0.0:
            tied_evidence.append(data)
            
    # Deduplicate tied evidence logically
    unique_evidence = []
    seen = set()
    for ev in tied_evidence:
        # Create a unique key for the evidence dictionary
        key = (ev.get("source"), ev.get("target"), ev.get("relationship_type"), ev.get("evidence"), ev.get("case_id"))
        if key not in seen:
            seen.add(key)
            formatted_ev = f"{ev.get('relationship_type')} | Case: {ev.get('case_id')} | Conf: {ev.get('confidence', 0):.2f} | Method: {ev.get('detection_method')} | Evidence: {ev.get('evidence')}"
            unique_evidence.append(formatted_ev)
            
    return max_conf, unique_evidence

def calculate_priority_scores(G: nx.MultiDiGraph, analytics_results: dict) -> list:
    """
    Calculates the Investigation Priority Score for human analytical review.
    Does NOT predict criminality or guilt.
    """
    if not G or len(G) == 0:
        return []
        
    ELIGIBLE_TYPES = {"PERSON", "PHONE", "BANK_ACCOUNT", "VEHICLE", "LOCATION", "ORGANIZATION"}
    
    # Extract signals from Step 12 analytics
    raw_signals = {}
    
    # Find max/min for normalization across ELIGIBLE nodes only
    metrics = {
        "betweenness": {"values": []},
        "cross_case": {"values": []},
        "bridging": {"values": []},
        "diversity": {"values": []},
        "confidence": {"values": []}
    }
    
    for node in G.nodes():
        node_type = G.nodes[node].get("type", "UNKNOWN")
        if node_type not in ELIGIBLE_TYPES:
            continue
            
        raw_signals[node] = {
            "entity_type": node_type,
            "betweenness": 0.0,
            "cross_case": 0.0,
            "bridging": 0.0,
            "diversity": 0.0,
            "confidence": 0.0,
            "evidence_list": []
        }
        
    # Betweenness
    for r in analytics_results.get("betweenness_centrality", []):
        node = r["entity_id"]
        if node in raw_signals:
            raw_signals[node]["betweenness"] = r["betweenness_score"]
            metrics["betweenness"]["values"].append(r["betweenness_score"])
            
    # Cross-Case Connectivity
    for r in analytics_results.get("cross_case_connectivity", []):
        node = r["entity_id"]
        if node in raw_signals:
            raw_signals[node]["cross_case"] = float(r["case_count"])
            metrics["cross_case"]["values"].append(float(r["case_count"]))
            
    # Community Bridging
    for r in analytics_results.get("community_bridging", []):
        node = r["entity_id"]
        if node in raw_signals:
            raw_signals[node]["bridging"] = float(r["bridge_score"])
            metrics["bridging"]["values"].append(float(r["bridge_score"]))
            
    # Relationship Diversity
    for r in analytics_results.get("relationship_diversity", []):
        node = r["entity_id"]
        if node in raw_signals:
            raw_signals[node]["diversity"] = float(r["diversity_score"])
            metrics["diversity"]["values"].append(float(r["diversity_score"]))
            
    # Evidence Confidence (from Step 10 via Graph edges)
    for node in raw_signals.keys():
        max_conf, ev_list = _get_max_confidence_evidence(G, node)
        raw_signals[node]["confidence"] = max_conf
        raw_signals[node]["evidence_list"] = ev_list
        metrics["confidence"]["values"].append(max_conf)
        
    # Calculate min/max for normalization
    for m_name, m_data in metrics.items():
        vals = m_data["values"]
        m_data["min"] = min(vals) if vals else 0.0
        m_data["max"] = max(vals) if vals else 0.0
        
    # Calculate final scores
    results = []
    
    for node, signals in raw_signals.items():
        norm_btw = _normalize(signals["betweenness"], metrics["betweenness"]["min"], metrics["betweenness"]["max"])
        norm_cross = _normalize(signals["cross_case"], metrics["cross_case"]["min"], metrics["cross_case"]["max"])
        norm_bridge = _normalize(signals["bridging"], metrics["bridging"]["min"], metrics["bridging"]["max"])
        norm_div = _normalize(signals["diversity"], metrics["diversity"]["min"], metrics["diversity"]["max"])
        norm_conf = _normalize(signals["confidence"], metrics["confidence"]["min"], metrics["confidence"]["max"])
        
        # Priority Formula
        score = (
            (0.30 * norm_btw) +
            (0.25 * norm_cross) +
            (0.20 * norm_bridge) +
            (0.15 * norm_div) +
            (0.10 * norm_conf)
        )
        
        # Priority Levels
        if score >= 0.70:
            level = "HIGH"
        elif score >= 0.40:
            level = "MEDIUM"
        else:
            level = "LOW"
            
        # Reason Generation
        reasons = []
        if norm_btw >= 0.5:
            reasons.append("High betweenness centrality")
        if norm_cross >= 0.5:
            reasons.append("Connected to multiple cases")
        if norm_bridge >= 0.5:
            reasons.append("Bridges multiple graph communities")
        if norm_div >= 0.5:
            reasons.append("High relationship diversity")
        if norm_conf >= 0.5:
            reasons.append("Strong supporting relationship evidence")
            
        if not reasons:
            reasons.append("Base analytical signal")
            
        results.append({
            "entity_id": node,
            "entity_type": signals["entity_type"],
            "priority_score": round(score, 4),
            "priority_level": level,
            "reasons": reasons,
            "supporting_evidence": signals["evidence_list"]
        })
        
    # Deterministic Ranking: score descending, entity_id ascending
    results.sort(key=lambda x: (-x["priority_score"], x["entity_id"]))
    
    return results
