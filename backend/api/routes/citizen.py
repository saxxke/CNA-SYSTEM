"""
citizen.py
==========
Dedicated Citizen Portal API routes.

Provides object-level authorization for citizen users to access only their
explicitly authorized case status records.

Security Rules:
- Only accessible by users with CITIZEN role.
- Case access is filtered strictly by authenticated user_id.
- Changing case_id in URL/query/body must NEVER allow access to another citizen's case.
- Never exposes internal investigation notes, suspect lists, networks, or evidence.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.models import CitizenSafeCaseItem
from api.dependencies import (
    get_cases,
    require_role,
    get_citizen_access_repo,
    require_citizen_case_access,
    get_audit_repo,
)
from modules.auth.roles import UserRole
from modules.auth.models import User
from modules.auth.citizen_access import CitizenAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_service import log_citizen_case_view

router = APIRouter(prefix="/citizen", tags=["Citizen Portal"])


def format_citizen_safe_case(case_data: Dict[str, Any], user: User) -> CitizenSafeCaseItem:
    """
    Transforms a raw internal case record into a sanitized, citizen-safe representation.
    Strictly excludes suspects, internal notes, networks, analytics, and evidence.
    """
    # Details might be top-level or under details dict
    details = case_data.get("details", case_data)
    cid = case_data.get("case_id") or case_data.get("id") or details.get("case_id", "")

    return CitizenSafeCaseItem(
        case_id=str(cid),
        case_title=str(details.get("case_title") or case_data.get("case_title") or f"Case Record {cid}"),
        offence_category=str(details.get("offence_category") or case_data.get("offence_category") or "General Offence"),
        fir_number=details.get("fir_number") or case_data.get("fir_number"),
        date_opened=details.get("date_opened") or case_data.get("date_opened"),
        status=str(details.get("status") or case_data.get("status") or "UNDER REVIEW"),
        police_station=str(details.get("police_station") or case_data.get("police_station") or "Designated Police Station"),
        district=str(details.get("district") or case_data.get("district") or "District"),
        state=str(details.get("state") or case_data.get("state") or "State"),
        official_notice="Authorized citizen case inquiry record. For official assistance, contact your local police station.",
        authorized_for_user=user.username
    )


@router.get(
    "/cases",
    response_model=List[CitizenSafeCaseItem],
    summary="List cases explicitly authorized for the authenticated citizen",
    dependencies=[Depends(require_role(UserRole.CITIZEN))]
)
def list_citizen_authorized_cases(
    current_user: User = Depends(require_role(UserRole.CITIZEN)),
    citizen_repo: CitizenAccessRepository = Depends(get_citizen_access_repo),
    cases: List = Depends(get_cases)
):
    """
    Returns only the cases explicitly authorized for the authenticated citizen.
    If the citizen has zero authorized cases, returns empty list [].
    Never returns another citizen's cases.
    """
    authorized_case_ids = set(citizen_repo.get_authorized_case_ids(current_user.user_id, active_only=True))
    if not authorized_case_ids:
        return []

    results = []
    for c in cases:
        cid = c.get("case_id") or c.get("id")
        if cid and cid.strip().upper() in authorized_case_ids:
            results.append(format_citizen_safe_case(c, current_user))

    # Sort deterministically by case_id
    results.sort(key=lambda x: x.case_id)
    return results


@router.get(
    "/cases/{case_id}",
    response_model=CitizenSafeCaseItem,
    summary="Retrieve sanitized status for an explicitly authorized case",
    dependencies=[Depends(require_role(UserRole.CITIZEN))]
)
def get_citizen_case_details(
    case_id: str,
    request: Request,
    current_user: User = Depends(require_role(UserRole.CITIZEN)),
    case_record: Dict[str, Any] = Depends(require_citizen_case_access),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """
    Object-level authorization endpoint:
    - 401 if unauthenticated
    - 403 if authenticated user is not CITIZEN
    - 404 if case does not exist in case inventory
    - 403 if case exists but citizen is not authorized for it
    - 200 with sanitized citizen-safe fields if authorized
    """
    log_citizen_case_view(audit_repo, current_user, case_id.strip().upper(), request)
    return format_citizen_safe_case(case_record, current_user)
