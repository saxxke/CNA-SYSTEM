from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional
import networkx as nx
from api.dependencies import (
    get_priority,
    get_graph,
    get_cases,
    require_permission,
    get_investigation_access_repo,
    get_audit_repo,
)
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_service import log_priority_view
from modules.cases.case_service import _load_and_index_dataset
from api.models import PriorityResult

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.VIEW_PRIORITY_LEADS))]
)


@router.get("/priority", response_model=List[PriorityResult])
def get_priority_scores(
    request: Request,
    entity_type: Optional[str] = None,
    priority_level: Optional[str] = None,
    limit: Optional[int] = Query(100, ge=1),
    current_user: User = Depends(require_permission(Permission.VIEW_PRIORITY_LEADS)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph),
    priority: list = Depends(get_priority)
):
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    cache = _load_and_index_dataset()
    cases_by_person = cache.get("cases_by_person", {})

    results = []
    for p in priority:
        if entity_type and p["entity_type"] != entity_type:
            continue
        if priority_level and p["priority_level"] != priority_level:
            continue

        eid = p["entity_id"]
        # Check connection to authorized case
        is_connected = False
        linked_cids = cases_by_person.get(eid, [])
        if any(cid.strip().upper() in authorized_case_ids for cid in linked_cids):
            is_connected = True
        elif eid in G:
            for _, _, _, d in G.in_edges(eid, data=True, keys=True):
                if (d.get("case_id") or "").strip().upper() in authorized_case_ids:
                    is_connected = True
                    break
            if not is_connected:
                for _, _, _, d in G.out_edges(eid, data=True, keys=True):
                    if (d.get("case_id") or "").strip().upper() in authorized_case_ids:
                        is_connected = True
                        break

        if is_connected:
            results.append(p)
            if len(results) >= limit:
                break

    # Log priority view audit event
    log_priority_view(audit_repo, current_user, request, lead_count=len(results))

    return results

