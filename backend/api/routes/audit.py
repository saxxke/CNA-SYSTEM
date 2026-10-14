"""
audit.py
========
Read-only Audit Log inquiry endpoints for supervisory and oversight roles:
- IPS_OFFICER: State supervisory compliance
- HOME_MINISTRY: National oversight compliance

Security Rules:
- Enforces Permission.VIEW_AUDIT_LOGS.
- Strictly read-only: No create/update/delete endpoints exist.
- Investigating Officers and Citizens are denied with HTTP 403 Forbidden.
- Unauthenticated requests are rejected with HTTP 401 Unauthorized.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    require_permission,
    get_audit_repo,
    require_authenticated_user,
)
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.audit_models import (
    AuditEvent,
    AuditLogQueryResponse,
    AuditEventType,
    AuditStatus,
)
from modules.auth.audit_repository import AuditLogRepository

router = APIRouter(
    prefix="/audit",
    tags=["Audit Logging"],
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))]
)


@router.get("/logs", response_model=AuditLogQueryResponse)
def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by actor user ID or username"),
    role: Optional[str] = Query(None, description="Filter by actor role (CITIZEN, INVESTIGATING_OFFICER, IPS_OFFICER, HOME_MINISTRY)"),
    event_type: Optional[str] = Query(None, description="Filter by specific event type"),
    status: Optional[str] = Query(None, description="Filter by outcome status (SUCCESS, DENIED, FAILED)"),
    target_id: Optional[str] = Query(None, description="Filter by target object ID (case ID, person ID)"),
    from_date: Optional[str] = Query(None, description="ISO timestamp start filter"),
    to_date: Optional[str] = Query(None, description="ISO timestamp end filter"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """
    Retrieves immutable audit trail records with optional filtering.
    Restricted exclusively to supervisory and oversight authorities (IPS and Home Ministry).
    """
    events = audit_repo.query_logs(
        user_id=user_id,
        role=role,
        event_type=event_type,
        status=status,
        target_id=target_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset
    )
    total_count = audit_repo.count_logs(
        user_id=user_id,
        role=role,
        event_type=event_type,
        status=status,
        target_id=target_id,
        from_date=from_date,
        to_date=to_date
    )

    return AuditLogQueryResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        events=events
    )


@router.get("/logs/{event_id}", response_model=AuditEvent)
def get_audit_event_by_id(
    event_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
    audit_repo: AuditLogRepository = Depends(get_audit_repo)
):
    """
    Inspects a single immutable audit event by its unique ID.
    """
    event = audit_repo.get_by_id(event_id)
    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Audit event '{event_id}' not found.")
    return event
