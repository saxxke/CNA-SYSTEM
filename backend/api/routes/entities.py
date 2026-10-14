from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional, Dict, Any
import networkx as nx
from api.dependencies import (
    get_graph,
    get_cases,
    get_analytics,
    get_priority,
    require_permission,
    get_investigation_access_repo,
    get_audit_repo,
)
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_service import log_entity_view
from api.models import Entity, Edge, DuplicateCheckRequest, DuplicateCheckResponse
from modules.entities.person_service import (
    get_person_profile, 
    get_person_family_profile, 
    list_persons_summary
)
from modules.cases.case_service import _load_and_index_dataset
from modules.persistence.runtime_store import get_next_person_id
from modules.cases.case_registration_service import (
    check_person_duplicate,
    search_persons_for_linking
)

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.VIEW_PEOPLE, Permission.VIEW_NETWORK))]
)


def check_entity_access_or_raise(
    entity_id: str,
    current_user: User,
    inv_repo: InvestigationAccessRepository,
    inventory: list,
    G: nx.MultiDiGraph
):
    """
    Enforces object-level authorization for an entity.
    Raises 404 if entity does not exist.
    Raises 403 if entity is not linked to authorized cases or in officer jurisdiction.
    """
    clean_id = entity_id.strip()
    cache = _load_and_index_dataset()
    persons_by_id = cache.get("persons_by_id", {})
    cases_by_person = cache.get("cases_by_person", {})

    in_persons = clean_id in persons_by_id
    in_graph = clean_id in G and G.nodes[clean_id].get("type") not in ("CASE", "CASE_ID")

    if not in_persons and not in_graph:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    scope = inv_repo.get_jurisdiction(current_user.user_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    # 1. Check if person is linked to any authorized case
    linked_cids = cases_by_person.get(clean_id, [])
    if any(cid.strip().upper() in authorized_case_ids for cid in linked_cids):
        return

    # 2. Check if entity has an incident edge with an authorized case
    if in_graph:
        for _, _, _, d in G.in_edges(clean_id, data=True, keys=True):
            if (d.get("case_id") or "").strip().upper() in authorized_case_ids:
                return
        for _, _, _, d in G.out_edges(clean_id, data=True, keys=True):
            if (d.get("case_id") or "").strip().upper() in authorized_case_ids:
                return

    # 3. Check if person resides within officer's jurisdiction
    if in_persons and scope and scope.covers_person(persons_by_id[clean_id]):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: Entity '{clean_id}' is not associated with your authorized cases or jurisdiction."
    )


@router.get("/persons", response_model=List[Dict[str, Any]])
def get_persons(
    search: Optional[str] = None,
    district: Optional[str] = None,
    limit: Optional[int] = Query(250, ge=1),
    current_user: User = Depends(require_permission(Permission.VIEW_PEOPLE)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases)
):
    """
    Returns synthetic person registry scoped to officer authorization:
    - Persons associated with authorized cases.
    - Persons residing within officer's territorial jurisdiction.
    """
    scope = inv_repo.get_jurisdiction(current_user.user_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    cache = _load_and_index_dataset()
    cases_by_person = cache.get("cases_by_person", {})

    all_persons = list_persons_summary(search=search, district=district, limit=limit)
    filtered = []
    for p in all_persons:
        pid = p["person_id"]
        linked = cases_by_person.get(pid, [])
        if any(cid.strip().upper() in authorized_case_ids for cid in linked):
            filtered.append(p)
        elif scope and scope.covers_person(p):
            filtered.append(p)

    return filtered[:limit]


@router.get("/persons/next-id")
def get_next_person_id_route():
    """Returns dynamically allocated next Person ID."""
    return {"next_person_id": get_next_person_id()}


@router.get("/persons/search-linking")
def search_persons_for_case_linking(
    q: str = Query("", description="Search term for linking person to case"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_permission(Permission.VIEW_PEOPLE)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases)
):
    """Searches registered persons for case linking, filtered to officer scope."""
    scope = inv_repo.get_jurisdiction(current_user.user_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    cache = _load_and_index_dataset()
    cases_by_person = cache.get("cases_by_person", {})

    candidates = search_persons_for_linking(query=q, limit=limit * 2)
    filtered = []
    for p in candidates:
        pid = p["person_id"]
        linked = cases_by_person.get(pid, [])
        if any(cid.strip().upper() in authorized_case_ids for cid in linked):
            filtered.append(p)
        elif scope and scope.covers_person(p):
            filtered.append(p)

    return filtered[:limit]


@router.post("/persons/check-duplicate", response_model=DuplicateCheckResponse)
def check_person_duplicate_route(
    payload: DuplicateCheckRequest
):
    """Advisory Entity Resolution check for duplicate or similar existing persons."""
    return check_person_duplicate(payload.model_dump())


@router.get("/entities", response_model=List[Entity])
def list_entities(
    type: Optional[str] = None,
    limit: Optional[int] = Query(100, ge=1),
    current_user: User = Depends(require_permission(Permission.VIEW_PEOPLE, Permission.VIEW_NETWORK)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    scope = inv_repo.get_jurisdiction(current_user.user_id)
    cache = _load_and_index_dataset()
    persons_by_id = cache.get("persons_by_id", {})
    cases_by_person = cache.get("cases_by_person", {})

    entities = []
    for n, d in G.nodes(data=True):
        t = d.get("type")
        if t in ("CASE", "CASE_ID"):
            continue
        if type and t != type:
            continue

        # Check authorization
        node_id = str(n)
        is_auth = False
        linked = cases_by_person.get(node_id, [])
        if any(cid.strip().upper() in authorized_case_ids for cid in linked):
            is_auth = True
        elif node_id in persons_by_id and scope and scope.covers_person(persons_by_id[node_id]):
            is_auth = True
        else:
            for _, _, _, ed in G.in_edges(node_id, data=True, keys=True):
                if (ed.get("case_id") or "").strip().upper() in authorized_case_ids:
                    is_auth = True
                    break
            if not is_auth:
                for _, _, _, ed in G.out_edges(node_id, data=True, keys=True):
                    if (ed.get("case_id") or "").strip().upper() in authorized_case_ids:
                        is_auth = True
                        break

        if is_auth:
            entities.append(Entity(
                id=node_id,
                type=t or "UNKNOWN",
                value=d.get("value"),
                details=d
            ))
            if len(entities) >= limit:
                break

    entities.sort(key=lambda x: x.id)
    return entities


@router.get("/entities/{entity_id}")
def get_entity_details(
    entity_id: str,
    request: Request,
    current_user: User = Depends(require_permission(Permission.VIEW_PEOPLE, Permission.VIEW_NETWORK)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph),
    analytics: dict = Depends(get_analytics),
    priority: list = Depends(get_priority)
):
    check_entity_access_or_raise(entity_id, current_user, inv_repo, inventory, G)

    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    # Check if entity is a person first (Step 18 Person Dossier)
    person_profile = get_person_profile(entity_id, G=G, analytics=analytics, priority=priority)
    if person_profile:
        # Sanitize profile associated cases to only authorized cases
        if "associated_cases" in person_profile:
            person_profile["associated_cases"] = [
                c for c in person_profile["associated_cases"]
                if (c.get("case_id") or "").strip().upper() in authorized_case_ids
            ]
            person_profile["associated_cases_count"] = len(person_profile["associated_cases"])
        log_entity_view(audit_repo, current_user, entity_id, request, is_family=False, is_person=True)
        return person_profile

    # Fallback to general graph entity
    if entity_id not in G or G.nodes[entity_id].get("type") in ("CASE", "CASE_ID"):
        raise HTTPException(status_code=404, detail="Entity not found")

    entity_data = G.nodes[entity_id]

    # Filter connected entities to those linked to authorized cases
    connected_entities = []
    neighbors = set(G.predecessors(entity_id)) | set(G.successors(entity_id))
    for neighbor in neighbors:
        connected_entities.append({"id": neighbor, "type": G.nodes[neighbor].get("type")})

    entity_analytics = {}
    for r in analytics.get("degree_centrality", []):
        if r["entity_id"] == entity_id:
            entity_analytics["degree_centrality"] = r["centrality_score"]
    for r in analytics.get("betweenness_centrality", []):
        if r["entity_id"] == entity_id:
            entity_analytics["betweenness_centrality"] = r["betweenness_score"]

    entity_priority = None
    for p in priority:
        if p["entity_id"] == entity_id:
            entity_priority = p
            break

    log_entity_view(audit_repo, current_user, entity_id, request, is_family=False, is_person=False)

    return {
        "entity_id": entity_id,
        "entity_type": entity_data.get("type", "UNKNOWN"),
        "value": entity_data.get("value"),
        "details": entity_data,
        "connected_entities": connected_entities,
        "graph_metrics": entity_analytics,
        "priority_information": entity_priority
    }


@router.get("/entities/{entity_id}/family")
def get_entity_family(
    entity_id: str,
    request: Request,
    current_user: User = Depends(require_permission(Permission.VIEW_PEOPLE)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    """
    Step 19: Dedicated Investigator Family Profile Endpoint.
    Enforces authorization: Civilian family data is accessible ONLY when the underlying person
    is within the officer's authorized investigation scope.
    """
    check_entity_access_or_raise(entity_id, current_user, inv_repo, inventory, G)
    family_profile = get_person_family_profile(entity_id)
    if not family_profile:
        raise HTTPException(status_code=404, detail="Person not found or entity is not a person")

    log_entity_view(audit_repo, current_user, entity_id, request, is_family=True, is_person=True)
    return family_profile


@router.get("/entities/{entity_id}/relationships", response_model=List[Edge])
def get_entity_relationships(
    entity_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_PEOPLE, Permission.VIEW_NETWORK)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    check_entity_access_or_raise(entity_id, current_user, inv_repo, inventory, G)

    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    edges = []
    edge_id = 0

    for u, v, k, d in G.in_edges(entity_id, data=True, keys=True):
        cid = (d.get("case_id") or "").strip().upper()
        # Strictly prune edges belonging to unauthorized cases
        if cid and cid not in authorized_case_ids:
            continue

        edges.append(Edge(
            id=f"e{edge_id}",
            source=u,
            target=v,
            relationship_type=d.get("relationship_type", "UNKNOWN"),
            confidence=d.get("confidence", 0.0),
            evidence=d.get("evidence", ""),
            case_id=d.get("case_id", ""),
            detection_method=d.get("detection_method", "")
        ))
        edge_id += 1

    for u, v, k, d in G.out_edges(entity_id, data=True, keys=True):
        cid = (d.get("case_id") or "").strip().upper()
        if cid and cid not in authorized_case_ids:
            continue

        edges.append(Edge(
            id=f"e{edge_id}",
            source=u,
            target=v,
            relationship_type=d.get("relationship_type", "UNKNOWN"),
            confidence=d.get("confidence", 0.0),
            evidence=d.get("evidence", ""),
            case_id=d.get("case_id", ""),
            detection_method=d.get("detection_method", "")
        ))
        edge_id += 1

    unique_edges = []
    seen = set()
    for e in edges:
        key = (e.source, e.target, e.relationship_type, e.case_id, e.evidence)
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    unique_edges.sort(key=lambda x: (x.source, x.target, x.relationship_type))
    return unique_edges

