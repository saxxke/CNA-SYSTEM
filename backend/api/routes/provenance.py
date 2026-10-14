"""
provenance.py
=============
REST router for Phase 8A: Relationship Evidence Provenance.

Security & Authorization:
- Strict Phase 6 authorization enforcement.
- CITIZEN & HOME_MINISTRY: Denied (HTTP 403 Forbidden).
- INVESTIGATING_OFFICER: Active case assignment + jurisdiction required.
- IPS_OFFICER: State jurisdiction required.
- Full Phase 7 audit logging: PROVENANCE_EDGE_VIEW.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
import networkx as nx

from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_service import log_provenance_edge_view
from api.dependencies import (
    get_graph,
    get_cases,
    get_audit_repo,
    get_investigation_access_repo,
    require_permission,
)
from modules.provenance.models import EdgeProvenanceResponse
from modules.provenance.provenance_service import get_edge_provenance

router = APIRouter(
    prefix="/provenance",
    tags=["Provenance & Explainability"],
    dependencies=[Depends(require_permission(Permission.VIEW_NETWORK))]
)


@router.get("/edge", response_model=EdgeProvenanceResponse)
def get_edge_evidence_provenance(
    source: str = Query(..., description="Source entity ID"),
    target: str = Query(..., description="Target entity ID"),
    case_id: Optional[str] = Query(None, description="Optional case ID to disambiguate edge"),
    request: Request = None,
    current_user: User = Depends(require_permission(Permission.VIEW_NETWORK)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: List = Depends(get_cases),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    """
    Returns sanitized evidence provenance, detection method, and Confidence Evidence Breakdown
    for an analytical relationship edge.
    
    Enforces server-side Phase 6 authorization:
    - Never exposes evidence belonging exclusively to unauthorized cases.
    - Logs an immutable PROVENANCE_EDGE_VIEW audit event on success.
    """
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    clean_source = source.strip()
    clean_target = target.strip()
    clean_case_id = case_id.strip().upper() if case_id else None

    # If a specific case_id was requested, ensure it is within officer's authorized scope
    if clean_case_id and clean_case_id not in authorized_case_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge evidence not found or outside your authorized investigation scope."
        )

    # Retrieve edge provenance from verified knowledge graph
    result = get_edge_provenance(G, clean_source, clean_target, case_id=clean_case_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analytical relationship found between '{source}' and '{target}'."
        )

    # Enforce case authorization on the resolved edge
    edge_case = (result.case_id or "").strip().upper()
    if edge_case and edge_case not in authorized_case_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge evidence not found or outside your authorized investigation scope."
        )

    # Filter supporting records strictly to authorized cases
    filtered_records = []
    for r in result.supporting_records:
        rec_cid = ""
        if r.communication:
            rec_cid = r.communication.case_id
        elif r.transaction:
            rec_cid = r.transaction.case_id
        elif r.case_association:
            rec_cid = r.case_association.case_id
        elif r.metadata_linkage:
            rec_cid = r.metadata_linkage.case_id

        if not rec_cid or rec_cid.strip().upper() in authorized_case_ids:
            filtered_records.append(r)

    result = result.model_copy(update={"supporting_records": filtered_records})

    # Phase 7 Audit Logging
    log_provenance_edge_view(
        repo=audit_repo,
        user=current_user,
        request=request,
        edge_id=f"{clean_source}_{clean_target}",
        case_id=result.case_id,
        detection_method=result.detection_method.value
    )

    return result
