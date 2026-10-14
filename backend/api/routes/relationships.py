from fastapi import APIRouter, Depends, Query
from typing import List, Optional
import networkx as nx
from api.dependencies import (
    get_graph,
    get_cases,
    require_permission,
    get_investigation_access_repo,
)
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from api.models import Edge, Node, GraphResponse


router = APIRouter(
    dependencies=[Depends(require_permission(Permission.VIEW_NETWORK))]
)


@router.get("/relationships", response_model=List[Edge])
def list_relationships(
    relationship_type: Optional[str] = None,
    case_id: Optional[str] = None,
    min_confidence: Optional[float] = 0.0,
    limit: Optional[int] = Query(100, ge=1),
    current_user: User = Depends(require_permission(Permission.VIEW_NETWORK)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    if case_id and case_id.strip().upper() not in authorized_case_ids:
        # Officer requested relationships for an unauthorized case -> return empty list
        return []

    edges = []
    edge_id = 0

    for u, v, k, d in G.edges(data=True, keys=True):
        rel_type = d.get("relationship_type", "")
        conf = d.get("confidence", 0.0)
        cid = (d.get("case_id") or "").strip().upper()

        # Enforce server-side authorization
        if cid and cid not in authorized_case_ids:
            continue
        if relationship_type and rel_type != relationship_type:
            continue
        if case_id and cid != case_id.strip().upper():
            continue
        if conf < min_confidence:
            continue

        edges.append(Edge(
            id=f"e{edge_id}",
            source=u,
            target=v,
            relationship_type=rel_type,
            confidence=conf,
            evidence=d.get("evidence", ""),
            case_id=cid,
            detection_method=d.get("detection_method", "")
        ))
        edge_id += 1
        if len(edges) >= limit:
            break

    return edges


@router.get("/network", response_model=GraphResponse)
def get_network(
    limit: Optional[int] = Query(200, ge=1),
    current_user: User = Depends(require_permission(Permission.VIEW_NETWORK)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    """
    Returns investigation network graph scoped strictly to officer's authorized cases:
    - Never leaks nodes/edges belonging exclusively to unauthorized cases.
    - Server-side filtering before serialization.
    """
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    edges = []
    retained_nodes = set()

    for u, v, k, d in G.edges(data=True, keys=True):
        cid = (d.get("case_id") or "").strip().upper()
        if cid and cid not in authorized_case_ids:
            continue

        edges.append(Edge(
            id=f"e_{u}_{v}_{k}",
            source=str(u),
            target=str(v),
            relationship_type=d.get("relationship_type", "UNKNOWN"),
            confidence=float(d.get("confidence", 0.0)),
            evidence=str(d.get("evidence", "")),
            case_id=str(d.get("case_id", "")),
            detection_method=str(d.get("detection_method", ""))
        ))
        retained_nodes.add(str(u))
        retained_nodes.add(str(v))
        if len(edges) >= limit:
            break

    # Also include authorized case nodes
    for cid in authorized_case_ids:
        if cid in G:
            retained_nodes.add(cid)

    nodes = []
    for n in retained_nodes:
        if n in G:
            d = G.nodes[n]
            nodes.append(Node(
                id=str(n),
                label=str(d.get("value") or n),
                type=str(d.get("type", "UNKNOWN"))
            ))

    return GraphResponse(nodes=nodes, edges=edges)


