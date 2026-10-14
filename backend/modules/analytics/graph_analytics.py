import networkx as nx

def _get_undirected_projection(G: nx.MultiDiGraph) -> nx.Graph:
    """
    Creates an undirected, single-edge projection of the MultiDiGraph.
    This prevents multiple evidence records (parallel edges) or directionality
    from artificially inflating topological metrics (like degree or betweenness).
    """
    if G is None:
        return nx.Graph()
    # G.to_undirected() on a MultiDiGraph returns a MultiGraph.
    # We then pass it to Graph() to collapse parallel edges into single edges.
    return nx.Graph(G.to_undirected())

def calculate_degree_centrality(G: nx.MultiDiGraph) -> list:
    """
    Calculates degree centrality using the undirected, unweighted projection.
    Definition: The fraction of nodes a node is connected to. It measures how 
    highly connected an entity is regardless of direction or multiple evidence records.
    """
    results = []
    if not G or len(G) == 0:
        return results
        
    U = _get_undirected_projection(G)
    centrality = nx.degree_centrality(U)
    
    for node, score in centrality.items():
        node_type = G.nodes[node].get("type", "UNKNOWN")
        results.append({
            "entity_id": node,
            "entity_type": node_type,
            "centrality_score": score
        })
        
    return sorted(results, key=lambda x: x["centrality_score"], reverse=True)

def calculate_betweenness_centrality(G: nx.MultiDiGraph) -> list:
    """
    Calculates betweenness centrality using the undirected, unweighted projection.
    This identifies entities that frequently lie on the shortest paths between 
    other entities, acting as structural bridges.
    """
    results = []
    if not G or len(G) == 0:
        return results
        
    U = _get_undirected_projection(G)
    centrality = nx.betweenness_centrality(U)
    
    for node, score in centrality.items():
        node_type = G.nodes[node].get("type", "UNKNOWN")
        results.append({
            "entity_id": node,
            "entity_type": node_type,
            "betweenness_score": score
        })
        
    return sorted(results, key=lambda x: x["betweenness_score"], reverse=True)

def detect_communities(G: nx.MultiDiGraph) -> list:
    """
    Detects communities using Louvain community detection on the undirected projection.
    A fixed seed (42) is used to guarantee deterministic outputs for identical graphs.
    """
    results = []
    if not G or len(G) == 0:
        return results
        
    U = _get_undirected_projection(G)
    
    if len(U.edges) == 0:
        # If no edges, each node is its own community
        for idx, node in enumerate(U.nodes()):
            results.append({
                "community_id": idx,
                "entities": [node]
            })
        return results

    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(U, seed=42)
    except Exception:
        # Fallback to greedy modularity if louvain is unavailable (older networkx)
        from networkx.algorithms.community import greedy_modularity_communities
        communities = greedy_modularity_communities(U)
        
    for idx, comm in enumerate(communities):
        results.append({
            "community_id": idx,
            "entities": list(comm)
        })
        
    return results

def calculate_cross_case_connectivity(G: nx.MultiDiGraph) -> list:
    """
    Identifies entities associated with multiple distinct cases through actual graph edges.
    Evaluates neighbors of type CASE or CASE_ID. Does not hardcode any case IDs.
    """
    results = []
    if not G or len(G) == 0:
        return results
        
    U = _get_undirected_projection(G)
    
    for node in U.nodes():
        node_type = G.nodes[node].get("type", "UNKNOWN")
        
        # We only evaluate non-case entities for cross-case connectivity
        if node_type in ["CASE", "CASE_ID"]:
            continue
            
        connected_cases = set()
        for neighbor in U.neighbors(node):
            neighbor_type = G.nodes[neighbor].get("type", "UNKNOWN")
            if neighbor_type in ["CASE", "CASE_ID"]:
                connected_cases.add(neighbor)
                
        if len(connected_cases) > 1:
            results.append({
                "entity_id": node,
                "entity_type": node_type,
                "connected_cases": sorted(list(connected_cases)),
                "case_count": len(connected_cases)
            })
            
    return sorted(results, key=lambda x: x["case_count"], reverse=True)

def calculate_community_bridging(G: nx.MultiDiGraph, communities: list) -> list:
    """
    Identifies entities that connect to multiple distinct communities.
    The bridge_score is the number of distinct communities the entity's neighbors belong to.
    """
    results = []
    if not G or len(G) == 0 or not communities:
        return results
        
    # Map nodes to their assigned community_id
    node_to_comm = {}
    for comm in communities:
        comm_id = comm["community_id"]
        for node in comm["entities"]:
            node_to_comm[node] = comm_id
            
    U = _get_undirected_projection(G)
    
    for node in U.nodes():
        neighbor_comms = set()
        for neighbor in U.neighbors(node):
            if neighbor in node_to_comm:
                neighbor_comms.add(node_to_comm[neighbor])
                
        # A node is a bridge if it connects to communities other than its own,
        # or just if it connects to >1 distinct community.
        if len(neighbor_comms) > 1:
            results.append({
                "entity_id": node,
                "community_ids": sorted(list(neighbor_comms)),
                "bridge_score": len(neighbor_comms)
            })
            
    return sorted(results, key=lambda x: x["bridge_score"], reverse=True)

def calculate_relationship_diversity(G: nx.MultiDiGraph) -> list:
    """
    Measures the diversity of relationship types associated with each entity.
    Iterates over all incident edges (in and out) in the original MultiDiGraph 
    to capture all existing relationship_type attributes.
    """
    results = []
    if not G or len(G) == 0:
        return results
        
    for node in G.nodes():
        rel_types = set()
        
        # Outgoing edges
        for _, _, data in G.out_edges(node, data=True):
            if "relationship_type" in data:
                rel_types.add(data["relationship_type"])
                
        # Incoming edges
        for _, _, data in G.in_edges(node, data=True):
            if "relationship_type" in data:
                rel_types.add(data["relationship_type"])
                
        results.append({
            "entity_id": node,
            "relationship_types": sorted(list(rel_types)),
            "relationship_type_count": len(rel_types),
            "diversity_score": len(rel_types)
        })
        
    return sorted(results, key=lambda x: x["diversity_score"], reverse=True)

def analyze_graph(G: nx.MultiDiGraph) -> dict:
    """
    Master function to run all analytics on the graph and return a structured summary.
    Does NOT calculate priority scores. Output identifies analytical leads, not guilt.
    """
    if not G or len(G) == 0:
        return {
            "degree_centrality": [],
            "betweenness_centrality": [],
            "communities": [],
            "cross_case_connectivity": [],
            "community_bridging": [],
            "relationship_diversity": []
        }
        
    degree = calculate_degree_centrality(G)
    betweenness = calculate_betweenness_centrality(G)
    communities = detect_communities(G)
    cross_case = calculate_cross_case_connectivity(G)
    community_bridging = calculate_community_bridging(G, communities)
    rel_diversity = calculate_relationship_diversity(G)
    
    return {
        "degree_centrality": degree,
        "betweenness_centrality": betweenness,
        "communities": communities,
        "cross_case_connectivity": cross_case,
        "community_bridging": community_bridging,
        "relationship_diversity": rel_diversity
    }

def analyze_case_network(G: nx.MultiDiGraph, case_id: str) -> dict:
    """
    Runs analytics strictly on the subgraph connected to a specific case.
    Does not fabricate relationships or include unrelated entities.
    """
    # Import locally to avoid circular dependency
    from modules.graph.graph_builder import get_case_subgraph
    
    subgraph = get_case_subgraph(G, case_id)
    return analyze_graph(subgraph)
