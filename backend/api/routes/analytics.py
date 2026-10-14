"""
analytics.py
============
Analytics API routes with RBAC protection.
- /analytics: Aggregated investigation and network metrics (IO, IPS, HOME_MINISTRY)
- /analytics/cross-case: Multi-case connectivity & community bridging (IPS)
- /analytics/trends & /analytics/strategic-trends: Strategic trends over time (HOME_MINISTRY)
- /analytics/regional-statistics: District and regional stats (HOME_MINISTRY)
- /analytics/reports: Strategic and operational summary reports (IPS, HOME_MINISTRY)
- /analytics/entities/{entity_id}: Entity-level analytics (IO, IPS only)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Dict, Any
from api.dependencies import (
    get_analytics,
    get_cases,
    get_graph,
    require_permission,
    get_investigation_access_repo,
    get_audit_repo,
)
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_models import AuditEventType, AuditStatus
from modules.auth.audit_service import create_event
from modules.cases.case_service import _load_and_index_dataset

router = APIRouter()



@router.get(
    "/analytics",
    dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS, Permission.VIEW_AGGREGATED_ANALYTICS))]
)
def get_all_analytics(analytics: dict = Depends(get_analytics)):
    """
    Returns complete high-level graph analytics.
    Accessible to INVESTIGATING_OFFICER, IPS_OFFICER, and HOME_MINISTRY.
    """
    return analytics


@router.get(
    "/analytics/cross-case",
    dependencies=[Depends(require_permission(Permission.VIEW_CROSS_CASE_ANALYTICS))]
)
def get_cross_case_analytics(
    request: Request,
    current_user: User = Depends(require_permission(Permission.VIEW_CROSS_CASE_ANALYTICS)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: list = Depends(get_cases),
    analytics: dict = Depends(get_analytics)
):
    """
    Multi-case connectivity patterns and bridging entities.
    Accessible strictly to IPS_OFFICER supervisory tier.
    Scoped to cases within officer's state supervisory jurisdiction.
    """
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    raw_conn = analytics.get("cross_case_connectivity", [])
    filtered_conn = []
    for item in raw_conn:
        c1 = (item.get("case_1") or item.get("case_id_1") or "").strip().upper()
        c2 = (item.get("case_2") or item.get("case_id_2") or "").strip().upper()
        # At least one case must be within the officer's authorized state scope
        if (c1 and c1 in authorized_case_ids) or (c2 and c2 in authorized_case_ids):
            # If one is external, indicate cross-state connection
            entry = dict(item)
            if c1 and c1 not in authorized_case_ids:
                entry["case_1_external"] = True
                entry["case_1_notice"] = "External State Case"
            if c2 and c2 not in authorized_case_ids:
                entry["case_2_external"] = True
                entry["case_2_notice"] = "External State Case"
            filtered_conn.append(entry)

    raw_bridging = analytics.get("community_bridging", [])
    filtered_bridging = []
    for b in raw_bridging:
        # Check if bridging entity touches an authorized case
        b_cases = [c.strip().upper() for c in b.get("connected_cases", [])]
        if not b_cases or any(c in authorized_case_ids for c in b_cases):
            filtered_bridging.append(b)

    create_event(
        repo=audit_repo,
        event_type=AuditEventType.CROSS_CASE_ANALYTICS_VIEW,
        action="VIEW_CROSS_CASE",
        target_type="ANALYTICS",
        target_id="CROSS_CASE",
        user=current_user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={"connectivity_count": len(filtered_conn), "bridging_count": len(filtered_bridging)}
    )

    return {
        "cross_case_connectivity": filtered_conn,
        "community_bridging": filtered_bridging,
        "communities_count": len(analytics.get("communities", [])),
    }



@router.get(
    "/analytics/trends",
    dependencies=[Depends(require_permission(Permission.VIEW_TRENDS, Permission.VIEW_AGGREGATED_ANALYTICS))]
)
@router.get(
    "/analytics/strategic-trends",
    dependencies=[Depends(require_permission(Permission.VIEW_TRENDS, Permission.VIEW_AGGREGATED_ANALYTICS))]
)
def get_strategic_trends(analytics: dict = Depends(get_analytics)):
    """
    Macro crime trends and strategic indicators.
    Accessible to HOME_MINISTRY oversight.
    """
    return {
        "trend_summary": "Macro incident indicators across reporting periods",
        "communities_overview": [
            {"community_id": c["community_id"], "size": len(c.get("entities", []))}
            for c in analytics.get("communities", [])[:10]
        ],
        "degree_distribution_top": analytics.get("degree_centrality", [])[:10],
    }


@router.get(
    "/analytics/regional-statistics",
    dependencies=[Depends(require_permission(Permission.VIEW_REGIONAL_STATISTICS))]
)
def get_regional_statistics(analytics: dict = Depends(get_analytics)):
    """
    Regional and state-level statistical breakdowns.
    Accessible to HOME_MINISTRY oversight.
    """
    return {
        "jurisdiction_scope": "National / Regional Aggregates",
        "total_communities_monitored": len(analytics.get("communities", [])),
        "high_centrality_nodes": len(analytics.get("betweenness_centrality", [])),
        "status": "Aggregated strategic telemetry ready",
    }


@router.get(
    "/analytics/reports",
    dependencies=[Depends(require_permission(Permission.GENERATE_REPORTS, Permission.GENERATE_STRATEGIC_REPORTS))]
)
def generate_reports(analytics: dict = Depends(get_analytics)):
    """
    Generates operational or strategic intelligence reports.
    Accessible to IPS_OFFICER and HOME_MINISTRY.
    """
    return {
        "report_type": "Executive Intelligence Brief",
        "total_cross_case_links": len(analytics.get("cross_case_connectivity", [])),
        "top_bridging_entities": analytics.get("community_bridging", [])[:5],
        "generated_status": "CONFIDENTIAL_OFFICIAL",
    }


@router.get(
    "/analytics/entities/{entity_id}",
    dependencies=[Depends(require_permission(Permission.VIEW_ANALYTICS))]
)
def get_entity_analytics(
    entity_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_ANALYTICS)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    inventory: list = Depends(get_cases),
    G = Depends(get_graph),
    analytics: dict = Depends(get_analytics)
):
    """
    Entity-specific graph metrics.
    Restricted to field investigators and supervisory officers (IO, IPS).
    Denied to HOME_MINISTRY and CITIZEN.
    Scoped to authorized investigation scope.
    """
    clean_id = entity_id.strip()
    cache = _load_and_index_dataset()
    persons_by_id = cache.get("persons_by_id", {})
    cases_by_person = cache.get("cases_by_person", {})

    scope = inv_repo.get_jurisdiction(current_user.user_id)
    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )

    # Check authorization
    is_auth = False
    linked = cases_by_person.get(clean_id, [])
    if any(cid.strip().upper() in authorized_case_ids for cid in linked):
        is_auth = True
    elif clean_id in persons_by_id and scope and scope.covers_person(persons_by_id[clean_id]):
        is_auth = True
    elif G is not None and clean_id in G:
        for _, _, _, ed in G.in_edges(clean_id, data=True, keys=True):
            if (ed.get("case_id") or "").strip().upper() in authorized_case_ids:
                is_auth = True
                break
        if not is_auth:
            for _, _, _, ed in G.out_edges(clean_id, data=True, keys=True):
                if (ed.get("case_id") or "").strip().upper() in authorized_case_ids:
                    is_auth = True
                    break

    if not is_auth:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Analytics for entity '{clean_id}' requires authorized case or jurisdiction scope."
        )

    entity_analytics = {}
    found = False

    for r in analytics.get("degree_centrality", []):
        if r["entity_id"] == entity_id:
            entity_analytics["degree_centrality"] = r["centrality_score"]
            found = True

    for r in analytics.get("betweenness_centrality", []):
        if r["entity_id"] == entity_id:
            entity_analytics["betweenness_centrality"] = r["betweenness_score"]
            found = True

    for r in analytics.get("cross_case_connectivity", []):
        if r["entity_id"] == entity_id:
            entity_analytics["cross_case_connectivity"] = r
            found = True

    for r in analytics.get("community_bridging", []):
        if r["entity_id"] == entity_id:
            entity_analytics["community_bridging"] = r
            found = True

    for r in analytics.get("relationship_diversity", []):
        if r["entity_id"] == entity_id:
            entity_analytics["relationship_diversity"] = r
            found = True

    for c in analytics.get("communities", []):
        if entity_id in c["entities"]:
            entity_analytics["community_id"] = c["community_id"]
            found = True

    if not found:
        raise HTTPException(status_code=404, detail="Analytics for entity not found")

    return entity_analytics

