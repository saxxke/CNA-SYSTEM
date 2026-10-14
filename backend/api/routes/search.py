from fastapi import APIRouter, Depends, Request
from typing import List
import networkx as nx
from api.dependencies import (
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
from modules.auth.audit_service import log_search_query
from modules.cases.case_service import _load_and_index_dataset
from api.models import SearchResponse, SearchResult
from modules.entities.person_service import list_persons_summary

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.SEARCH_INVESTIGATION_DATA))]
)


@router.get("/search", response_model=SearchResponse)
def search(
    request: Request,
    q: str = "",
    current_user: User = Depends(require_permission(Permission.SEARCH_INVESTIGATION_DATA)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: List = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph)
):
    if not q:
        return SearchResponse(results=[])

    scope = inv_repo.get_jurisdiction(current_user.user_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    jurisdiction_case_ids = inv_repo.get_jurisdiction_case_ids(
        current_user.user_id,
        inventory
    )
    cache = _load_and_index_dataset()
    persons_by_id = cache.get("persons_by_id", {})
    cases_by_person = cache.get("cases_by_person", {})

    query = q.lower().strip()
    results = []
    seen_ids = set()

    # 1. Search NetworkX graph nodes with server-side authorization check
    for n, d in G.nodes(data=True):
        node_id = str(n).lower()
        original_value = str(d.get("value", "")).lower()
        normalized_value = str(d.get("normalized_value", "")).lower()

        if query in node_id or query in original_value or query in normalized_value:
            node_type = d.get("type", "UNKNOWN")
            raw_node_id = str(n)

            # Check authorization for this node
            is_auth = False
            if node_type in ("CASE", "CASE_ID"):
                match_type = "case"
                if raw_node_id.upper() in jurisdiction_case_ids:
                    is_auth = True
            else:
                match_type = "entity"
                linked = cases_by_person.get(raw_node_id, [])
                if any(cid.strip().upper() in authorized_case_ids for cid in linked):
                    is_auth = True
                elif raw_node_id in persons_by_id and scope and scope.covers_person(persons_by_id[raw_node_id]):
                    is_auth = True
                else:
                    for _, _, _, ed in G.in_edges(raw_node_id, data=True, keys=True):
                        if (ed.get("case_id") or "").strip().upper() in authorized_case_ids:
                            is_auth = True
                            break
                    if not is_auth:
                        for _, _, _, ed in G.out_edges(raw_node_id, data=True, keys=True):
                            if (ed.get("case_id") or "").strip().upper() in authorized_case_ids:
                                is_auth = True
                                break

            if is_auth and n not in seen_ids:
                seen_ids.add(n)
                results.append(SearchResult(
                    id=n,
                    type=node_type,
                    label=d.get("value") or n,
                    match_type=match_type
                ))

    # 2. Search synthetic person registry scoped to authorization
    matching_persons = list_persons_summary(search=query, limit=50)
    for p in matching_persons:
        pid = p["person_id"]
        if pid not in seen_ids:
            linked = cases_by_person.get(pid, [])
            is_auth = False
            if any(cid.strip().upper() in authorized_case_ids for cid in linked):
                is_auth = True
            elif scope and scope.covers_person(p):
                is_auth = True

            if is_auth:
                seen_ids.add(pid)
                label = p["full_name"]
                if p.get("primary_alias"):
                    label += f' ("{p["primary_alias"]}")'
                results.append(SearchResult(
                    id=pid,
                    type="PERSON",
                    label=label,
                    match_type="entity"
                ))

    # Sort for deterministic output
    results.sort(key=lambda x: (x.match_type, x.id))
    final_results = results[:30]

    # Audit log sanitized search execution (never raw query)
    log_search_query(
        audit_repo,
        current_user,
        request,
        search_mode="SIMPLE",
        filter_keys=["q"] if q else [],
        query_length=len(q),
        result_count=len(final_results)
    )

    return SearchResponse(results=final_results)


# --- Step 20: Advanced Search & Investigation Filtering Endpoints ---
from api.models import AdvancedSearchRequest, AdvancedSearchResponse
from modules.search.search_service import advanced_search, get_search_metadata


@router.post("/search/advanced", response_model=AdvancedSearchResponse)
def run_advanced_search(
    payload: AdvancedSearchRequest,
    request: Request,
    current_user: User = Depends(require_permission(Permission.SEARCH_INVESTIGATION_DATA)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: List = Depends(get_cases)
):
    """
    Step 20: Advanced deterministic search & investigation filtering.
    Applies authorization BEFORE returning search results.
    """
    scope = inv_repo.get_jurisdiction(current_user.user_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    jurisdiction_case_ids = inv_repo.get_jurisdiction_case_ids(
        current_user.user_id,
        inventory
    )
    cache = _load_and_index_dataset()
    persons_by_id = cache.get("persons_by_id", {})
    cases_by_person = cache.get("cases_by_person", {})

    res = advanced_search(payload.model_dump())

    # Filter cases: only within jurisdiction
    filtered_cases = []
    for c in res.get("cases", []):
        cid = (c.case_id if hasattr(c, "case_id") else c.get("case_id", "")).strip().upper()
        if cid in jurisdiction_case_ids:
            filtered_cases.append(c)

    # Filter persons: only connected to authorized cases or in jurisdiction
    filtered_persons = []
    for p in res.get("persons", []):
        pid = p.person_id if hasattr(p, "person_id") else p.get("person_id", "")
        linked = cases_by_person.get(pid, [])
        if any(cid.strip().upper() in authorized_case_ids for cid in linked):
            filtered_persons.append(p)
        elif pid in persons_by_id and scope and scope.covers_person(persons_by_id[pid]):
            filtered_persons.append(p)

    total_results = len(filtered_persons) + len(filtered_cases)

    # Audit log sanitized search execution (never raw query)
    active_filters = [k for k, v in payload.model_dump().items() if v and k not in ("query", "name")]
    log_search_query(
        audit_repo,
        current_user,
        request,
        search_mode=payload.mode or "ALL",
        filter_keys=active_filters,
        query_length=len(payload.query or "") + len(payload.name or ""),
        result_count=total_results
    )

    return AdvancedSearchResponse(
        mode=res.get("mode", payload.mode or "ALL"),
        total_persons=len(filtered_persons),
        total_cases=len(filtered_cases),
        total_results=total_results,
        persons=filtered_persons,
        cases=filtered_cases,
        safety_notice=res.get("safety_notice", "Analytical lead only. Requires human verification.")
    )


@router.get("/search/metadata")
def get_filter_metadata():
    """
    Returns available filter choices (offence categories, districts, statuses, years)
    for advanced search dropdowns directly from indexed dataset.
    """
    return get_search_metadata()



