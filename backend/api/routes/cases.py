from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Dict, Any
import networkx as nx
from api.dependencies import (
    get_graph,
    get_cases,
    require_permission,
    get_investigation_access_repo,
    get_officer_authorized_case_ids,
    require_investigation_case_access,
    get_audit_repo,
)
from modules.auth.roles import UserRole
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_service import log_case_view, log_case_register
from api.models import Case, GraphResponse, Node, Edge, RegisterCaseRequest, RegisterCaseResponse
from modules.graph.graph_builder import get_case_subgraph
from modules.cases.case_service import (
    get_all_cases_enriched,
    get_case_record,
    get_case_associated_persons,
    get_case_related_entities,
    get_case_evidence_relationships,
    get_case_related_cases_details
)
from modules.cases.case_registration_service import (
    register_case_transaction,
    ValidationError
)
from modules.persistence.runtime_store import get_next_case_id

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES))]
)


@router.get("/cases", response_model=List[Case])
def list_cases(
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    G: nx.MultiDiGraph = Depends(get_graph),
    inventory: List = Depends(get_cases)
):
    """
    Returns cases filtered according to officer investigation authorization:
    - IPS_OFFICER: All cases within their state supervisory jurisdiction.
    - INVESTIGATING_OFFICER: Cases within their territorial jurisdiction:
        * Assigned cases: Full enriched dossier metadata (is_assigned=True).
        * Unassigned cases in jurisdiction: Limited station-awareness summary without sensitive dossier data (is_assigned=False).
        * Cases outside jurisdiction: Omitted.
    """
    scope = inv_repo.get_jurisdiction(current_user.user_id)
    if not scope:
        return []

    assigned_ids = inv_repo.get_assigned_case_ids(current_user.user_id, active_only=True)
    enriched = get_all_cases_enriched(G=G)
    cases_result = []

    for c in enriched:
        cid = (c.get("case_id") or c.get("id") or "").strip().upper()
        if not scope.covers_case(c):
            # Strictly omit cases outside territorial jurisdiction
            continue

        if current_user.role == UserRole.IPS_OFFICER:
            # Full supervisory view over state cases
            details = dict(c)
            details["is_assigned"] = True
            details["is_supervisory"] = True
            cases_result.append(Case(id=cid, type="CASE", details=details))

        elif current_user.role == UserRole.INVESTIGATING_OFFICER:
            if cid in assigned_ids:
                # Full investigation access to actively assigned cases
                details = dict(c)
                details["is_assigned"] = True
                cases_result.append(Case(id=cid, type="CASE", details=details))
            else:
                # Same-jurisdiction unassigned case: Redact sensitive dossier/evidence/suspects
                sanitized_details = {
                    "case_id": cid,
                    "title": c.get("title") or f"Case {cid}",
                    "case_title": c.get("case_title") or c.get("title") or f"Case {cid}",
                    "offence_category": c.get("offence_category", "General Enquiry"),
                    "legal_section": c.get("legal_section", "Not Specified"),
                    "fir_number": c.get("fir_number", "N/A"),
                    "date_opened": c.get("date_opened", ""),
                    "status": c.get("status", "OPEN"),
                    "police_station": c.get("police_station", ""),
                    "district": c.get("district", ""),
                    "state": c.get("state", ""),
                    "description": "Station awareness record. Sensitive investigation dossier restricted (Need-to-Know authorization required).",
                    "location_id": "",
                    "associated_persons_count": 0,
                    "related_entities_count": 0,
                    "evidence_count": 0,
                    "has_graph_relationships": False,
                    "type": "CASE",
                    "value": cid,
                    "is_assigned": False,
                    "sensitive_redacted": True
                }
                cases_result.append(Case(id=cid, type="CASE", details=sanitized_details))

    cases_result.sort(key=lambda x: x.id)
    return cases_result


@router.get("/cases/next-id")
def get_next_case_id_route():
    """Returns the dynamically allocated next Case ID."""
    return {"next_case_id": get_next_case_id()}


@router.post("/cases/register", response_model=RegisterCaseResponse)
def register_new_case_route(
    payload: RegisterCaseRequest,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CREATE_CASE)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """
    Step 27: Register New Case + Create / Link Person.
    Authorization Rules:
    - Officer may register a case only within their territorial jurisdiction.
    - Automatically creates an active assignment for the registering IO.
    - Client cannot reassign case to another officer through request payload.
    """
    case_dict = {
        "district": payload.case.district,
        "state": payload.case.state,
        "police_station": payload.case.police_station
    }
    if not inv_repo.is_case_in_jurisdiction(current_user.user_id, case_dict):
        scope = inv_repo.get_jurisdiction(current_user.user_id)
        user_loc = (scope.district or scope.state or "assigned jurisdiction") if scope else "assigned jurisdiction"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot register case outside your territorial jurisdiction ({user_loc})."
        )

    try:
        result = register_case_transaction(
            payload.model_dump(),
            app_state=request.app.state
        )
        new_case_id = result.case_id if hasattr(result, "case_id") else result.get("case_id")

        # Automatically assign new case to the registering officer
        if new_case_id:
            inv_repo.assign_case(
                user_id=current_user.user_id,
                case_id=new_case_id,
                role_in_case="LEAD_INVESTIGATOR",
                assigned_by=current_user.username,
                active=True,
                metadata={"source": "registration_auto_assign"}
            )
            # Record audit event for case registration
            log_case_register(audit_repo, current_user, new_case_id, request)
        return result
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail={"message": ve.message, "errors": ve.errors})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Case registration failed: {str(e)}")


@router.get("/cases/{case_id}")
def get_case_details(
    case_id: str,
    request: Request,
    case_row: dict = Depends(require_investigation_case_access),
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    G: nx.MultiDiGraph = Depends(get_graph),
    inventory: List = Depends(get_cases)
):
    clean_case_id = case_id.strip().upper()
    title = case_row.get("case_title") or case_row.get("title") or f"Case {clean_case_id}"
    case_data = {
        "case_id": clean_case_id,
        "type": "CASE",
        "value": clean_case_id,
        "title": title,
        "case_title": title,
        "offence_category": case_row.get("offence_category", "General Enquiry"),
        "legal_section": case_row.get("legal_section", "Not Specified"),
        "fir_number": case_row.get("fir_number", "N/A"),
        "date_opened": case_row.get("date_opened", ""),
        "status": case_row.get("status", "OPEN"),
        "police_station": case_row.get("police_station", ""),
        "district": case_row.get("district", ""),
        "state": case_row.get("state", ""),
        "description": case_row.get("description", ""),
        "location_id": case_row.get("location_id", "")
    }

    # Check if case is in graph to supplement details and get connected entities
    connected_entities = []
    if clean_case_id in G and G.nodes[clean_case_id].get("type") in ("CASE", "CASE_ID"):
        case_data.update(G.nodes[clean_case_id])
        case_data["case_id"] = clean_case_id
        case_data["title"] = title

        for neighbor in G.neighbors(clean_case_id):
            connected_entities.append({"id": neighbor, "details": G.nodes[neighbor]})
        for pred in G.predecessors(clean_case_id):
            if pred not in [c["id"] for c in connected_entities]:
                connected_entities.append({"id": pred, "details": G.nodes[pred]})

    # Investigator-oriented analytical sections
    associated_persons = get_case_associated_persons(clean_case_id)
    related_entities = get_case_related_entities(clean_case_id)
    relationships = get_case_evidence_relationships(clean_case_id, G=G)
    related_cases = get_case_related_cases_details(clean_case_id, G=G)

    # Scoping of related cross-case connections
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    sanitized_related_cases = []
    for rc in related_cases:
        rc_id = (rc.get("case_id") or "").strip().upper()
        if rc_id in authorized_case_ids:
            sanitized_related_cases.append(rc)
        else:
            # Cross-state or unassigned related case: provide limited external indicator
            sanitized_related_cases.append({
                "case_id": rc_id,
                "title": f"External Investigation Lead [{rc.get('district', 'Outside Jurisdiction')}]",
                "offence_category": rc.get("offence_category", "Cross-Case Lead"),
                "status": rc.get("status", "UNDER REVIEW"),
                "district": rc.get("district", "External Jurisdiction"),
                "state": rc.get("state", "External State"),
                "connecting_entities_count": rc.get("connecting_entities_count", 1),
                "is_external_jurisdiction": True,
                "access_notice": "Analytical lead only. Requires supervisory or inter-state clearance for case dossier inspection."
            })

    case_data["associated_persons_count"] = len(associated_persons)
    case_data["related_entities_count"] = related_entities.get("total_count", 0)
    case_data["evidence_count"] = len(relationships)

    # Audit log successful dossier view
    log_case_view(audit_repo, current_user, clean_case_id, request, is_graph=False)

    return {
        "case_id": clean_case_id,
        "details": case_data,
        "connected_entities": connected_entities,
        "associated_persons": associated_persons,
        "related_entities": related_entities,
        "relationships": relationships,
        "related_cases": sanitized_related_cases
    }


@router.get("/cases/{case_id}/graph", response_model=GraphResponse)
def get_case_graph(
    case_id: str,
    request: Request,
    case_row: dict = Depends(require_investigation_case_access),
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    G: nx.MultiDiGraph = Depends(get_graph),
    inventory: List = Depends(get_cases)
):
    clean_case_id = case_id.strip().upper()

    if clean_case_id not in G or G.nodes[clean_case_id].get("type") not in ("CASE", "CASE_ID"):
        return GraphResponse(
            nodes=[Node(id=clean_case_id, label=clean_case_id, type="CASE")],
            edges=[]
        )

    subgraph = get_case_subgraph(G, clean_case_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    # Server-side graph filtering: Never allow traversal to leak edges belonging exclusively to unauthorized cases
    nodes = []
    edges = []
    edge_id = 0
    retained_node_ids = set()

    for u, v, k, d in subgraph.edges(data=True, keys=True):
        edge_cid = (d.get("case_id") or "").strip().upper()
        # Edge must belong to the active case or an authorized case
        if edge_cid and edge_cid != clean_case_id and edge_cid not in authorized_case_ids:
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
        retained_node_ids.add(u)
        retained_node_ids.add(v)
        edge_id += 1

    # Ensure central case node is included even if no edges
    retained_node_ids.add(clean_case_id)

    for n, d in subgraph.nodes(data=True):
        if n in retained_node_ids:
            nodes.append(Node(
                id=n,
                label=d.get("value") or n,
                type=d.get("type", "UNKNOWN")
            ))

    # Log case graph view audit event
    log_case_view(audit_repo, current_user, clean_case_id, request, is_graph=True)

    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/cases/{case_id}/related")
def get_related_cases(
    case_id: str,
    case_row: dict = Depends(require_investigation_case_access),
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    G: nx.MultiDiGraph = Depends(get_graph),
    inventory: List = Depends(get_cases)
):
    clean_case_id = case_id.strip().upper()
    related_cases_details = get_case_related_cases_details(clean_case_id, G=G)
    related_ids = [r["case_id"] for r in related_cases_details]

    if clean_case_id in G and G.nodes[clean_case_id].get("type") in ("CASE", "CASE_ID"):
        incident_entities = set(G.predecessors(clean_case_id)) | set(G.successors(clean_case_id))
        for ent in incident_entities:
            if G.nodes[ent].get("type") in ("CASE", "CASE_ID"):
                continue
            ent_neighbors = set(G.predecessors(ent)) | set(G.successors(ent))
            for en in ent_neighbors:
                if G.nodes[en].get("type") in ("CASE", "CASE_ID") and en != clean_case_id:
                    if en not in related_ids:
                        related_ids.append(en)

    return {
        "related_cases": sorted(list(set(related_ids))),
        "related_cases_details": related_cases_details
    }


