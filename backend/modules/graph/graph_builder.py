import networkx as nx

VALID_NODE_TYPES = {
    "CASE", "PERSON", "PHONE", "BANK_ACCOUNT", 
    "VEHICLE", "LOCATION", "ORGANIZATION"
}

VALID_EDGE_TYPES = {
    "INVOLVED_IN", "USES", "CONTACTED", "OWNS", 
    "TRANSFERRED_TO", "LOCATED_AT", "WORKS_FOR", "RELATED_TO"
}

def create_graph() -> nx.MultiDiGraph:
    """Initialize and return a new NetworkX MultiDiGraph."""
    return nx.MultiDiGraph()

def add_entity(G: nx.MultiDiGraph, entity: dict):
    """
    Validates and adds an entity to the graph as a node.
    Maps CASE_ID type to CASE.
    """
    if not entity:
        return
        
    node_id = str(entity.get("value", "")).strip()
    node_type = str(entity.get("type", "")).upper()
    
    # Map CASE_ID to CASE as per rules
    if node_type == "CASE_ID":
        node_type = "CASE"
        
    if not node_id or node_type not in VALID_NODE_TYPES:
        return

    # Add or update node, preserving original label/attributes
    if not G.has_node(node_id):
        G.add_node(
            node_id,
            id=node_id,
            type=node_type,
            label=node_id,
            evidence=entity.get("evidence", ""),
            confidence=entity.get("confidence", 1.0)
        )

def add_relationship(G: nx.MultiDiGraph, rel: dict):
    """
    Validates and adds a relationship as an edge.
    Merges duplicate evidence/confidence if the same semantic edge already exists.
    """
    source = str(rel.get("source", "")).strip()
    target = str(rel.get("target", "")).strip()
    rel_type = str(rel.get("relationship_type", "")).upper()
    evidence = str(rel.get("evidence", "")).strip()
    case_id = str(rel.get("case_id", "")).strip()
    det_method = str(rel.get("detection_method", "")).strip()
    
    # Validation
    if not source or not target:
        return
    if not G.has_node(source) or not G.has_node(target):
        return
    if rel_type not in VALID_EDGE_TYPES:
        return
    if not evidence or not case_id or not det_method:
        return
        
    # Confidence validation
    try:
        confidence = float(rel.get("confidence", 0.0))
    except (ValueError, TypeError):
        return
    if not (0.0 <= confidence <= 1.0):
        return

    # Check for exact duplicate edges to merge
    if G.has_edge(source, target):
        for key, attr in G[source][target].items():
            if attr.get("relationship_type") == rel_type and attr.get("case_id") == case_id:
                # Same edge context found. Merge evidence and take max confidence.
                existing_ev = attr.get("evidence", "")
                if evidence not in existing_ev:
                    attr["evidence"] = existing_ev + " | " + evidence
                attr["confidence"] = max(attr.get("confidence", 0.0), confidence)
                if rel.get("features") and not attr.get("features"):
                    attr["features"] = rel.get("features", {})
                new_records = rel.get("record_ids", [])
                existing_records = attr.setdefault("record_ids", [])
                for rid in new_records:
                    if rid and rid not in existing_records:
                        existing_records.append(rid)
                return

    # Create new edge
    G.add_edge(
        source,
        target,
        relationship_type=rel_type,
        confidence=confidence,
        evidence=evidence,
        case_id=case_id,
        detection_method=det_method,
        features=rel.get("features", {}),
        record_ids=list(rel.get("record_ids", []))
    )


def get_entity(G: nx.MultiDiGraph, node_id: str):
    """Return the node attributes if it exists."""
    if G.has_node(node_id):
        return G.nodes[node_id]
    return None

def get_neighbors(G: nx.MultiDiGraph, node_id: str, direction: str = "both") -> list:
    """
    Return neighbors of a node. 
    direction can be 'outgoing', 'incoming', or 'both'.
    """
    if not G.has_node(node_id):
        return []
        
    neighbors = set()
    if direction in ["outgoing", "both"]:
        neighbors.update(G.successors(node_id))
    if direction in ["incoming", "both"]:
        neighbors.update(G.predecessors(node_id))
        
    return [G.nodes[n] for n in neighbors]

def get_case_subgraph(G: nx.MultiDiGraph, case_id: str) -> nx.MultiDiGraph:
    """
    Returns a subgraph containing only edges that belong to the given case_id,
    along with their connected nodes.
    """
    selected_edges = []
    for u, v, k, d in G.edges(keys=True, data=True):
        if d.get("case_id") == case_id:
            selected_edges.append((u, v, k))
            
    return G.edge_subgraph(selected_edges).copy()

def find_shortest_path(G: nx.MultiDiGraph, source_id: str, target_id: str) -> list:
    """
    Finds the shortest path regardless of edge direction (using undirected representation).
    Returns a list of node IDs forming the path, or empty list if no path exists.
    """
    if not G.has_node(source_id) or not G.has_node(target_id):
        return []
        
    # Convert to undirected to allow connectivity analysis ignoring strict direction
    U = G.to_undirected()
    try:
        path = nx.shortest_path(U, source=source_id, target=target_id)
        return path
    except nx.NetworkXNoPath:
        return []

def find_related_cases(G: nx.MultiDiGraph, case_id: str) -> list:
    """
    Finds all other case IDs connected to any node involved in the given case_id.
    This explores the network based on actual evidence connections.
    """
    subgraph = get_case_subgraph(G, case_id)
    nodes_in_case = set(subgraph.nodes())
    
    related_cases = set()
    # For every node in the given case, look at all its edges in the full graph
    for node in nodes_in_case:
        # Outgoing
        for _, _, data in G.out_edges(node, data=True):
            cid = data.get("case_id")
            if cid and cid != case_id:
                related_cases.add(cid)
        # Incoming
        for _, _, data in G.in_edges(node, data=True):
            cid = data.get("case_id")
            if cid and cid != case_id:
                related_cases.add(cid)
                
    return list(related_cases)

def get_graph_statistics(G: nx.MultiDiGraph) -> dict:
    """
    Returns basic graph statistics.
    """
    node_types = {}
    for _, d in G.nodes(data=True):
        t = d.get("type", "UNKNOWN")
        node_types[t] = node_types.get(t, 0) + 1
        
    edge_types = {}
    for _, _, d in G.edges(data=True):
        t = d.get("relationship_type", "UNKNOWN")
        edge_types[t] = edge_types.get(t, 0) + 1
        
    # Number of weakly connected components
    components = nx.number_weakly_connected_components(G) if len(G) > 0 else 0
    
    return {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "node_types": node_types,
        "edge_types": edge_types,
        "connected_components": components
    }
