from fastapi import APIRouter, Depends
from api.models import SummaryResponse
from api.dependencies import get_graph, get_cases, require_permission
from modules.auth.permissions import Permission
import networkx as nx
from collections import defaultdict
from typing import List

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS, Permission.VIEW_AGGREGATED_ANALYTICS))]
)


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    G: nx.MultiDiGraph = Depends(get_graph),
    cases: List = Depends(get_cases)
):
    # The actual case inventory count (not just cases in graph)
    total_cases = len(cases)
    
    # Graph nodes that are entities (i.e. not cases)
    graph_cases = sum(1 for n, d in G.nodes(data=True) if d.get("type") in ("CASE", "CASE_ID"))
    total_entities = len(G) - graph_cases
    total_relationships = G.number_of_edges()
    
    node_counts = defaultdict(int)
    for n, d in G.nodes(data=True):
        node_counts[d.get("type", "UNKNOWN")] += 1
        
    edge_counts = defaultdict(int)
    for u, v, k, d in G.edges(data=True, keys=True):
        edge_counts[d.get("relationship_type", "UNKNOWN")] += 1
        
    return SummaryResponse(
        total_cases=total_cases,
        total_entities=total_entities,
        total_relationships=total_relationships,
        total_network_nodes=len(G),
        node_counts_by_type=dict(node_counts),
        relationship_counts_by_type=dict(edge_counts)
    )
