"""
audit_service.py
================
Helper service for constructing and recording sanitized AuditEvent records.

Guarantees:
- Server-authoritative actor identity.
- Strict data sanitization: No credentials, tokens, PII, full FIR text, or raw LLM transcripts.
- Helper methods for each domain operation.
- Single-point denial recording helper.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import Request

from .audit_models import AuditEvent, AuditEventType, AuditStatus
from .audit_repository import AuditLogRepository
from .models import User


def get_client_ip(request: Request) -> str:
    """Extracts client IP address safely from request."""
    if not request:
        return "127.0.0.1"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def create_event(
    repo: AuditLogRepository,
    event_type: AuditEventType,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    user: Optional[User] = None,
    status: AuditStatus = AuditStatus.SUCCESS,
    status_code: int = 200,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """
    Constructs and records an immutable AuditEvent in the given repository.
    """
    actor_user_id = user.user_id if user else "anonymous"
    actor_username = user.username if user else "anonymous"
    actor_role = user.role.value if (user and hasattr(user.role, "value")) else ("ANONYMOUS" if not user else str(user.role))
    actor_jurisdiction = getattr(user, "jurisdiction", None) if user else None

    req_path = request.url.path if request else "internal"
    ip = get_client_ip(request) if request else "127.0.0.1"

    event = AuditEvent(
        event_id=f"audit_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor_user_id=actor_user_id,
        actor_username=actor_username,
        actor_role=actor_role,
        actor_jurisdiction=actor_jurisdiction,
        event_type=event_type,
        action=action,
        target_type=target_type,
        target_id=target_id,
        status=status,
        status_code=status_code,
        request_path=req_path,
        ip_address=ip,
        details=details or {}
    )

    if repo is not None:
        repo.record_event(event)

    return event


# --- Domain-Specific Audit Recorders ---

def log_auth_success(repo: AuditLogRepository, user: User, request: Request) -> AuditEvent:
    return create_event(
        repo=repo,
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        action="LOGIN",
        target_type="AUTH",
        target_id=user.username,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={"notice": "Session authenticated successfully."}
    )


def log_auth_failure(repo: AuditLogRepository, username: str, request: Request, reason: str = "Invalid credentials") -> AuditEvent:
    if request:
        request.state.audit_denial_recorded = True
    return create_event(
        repo=repo,
        event_type=AuditEventType.AUTH_LOGIN_FAILURE,
        action="LOGIN",
        target_type="AUTH",
        target_id=username if username else "unknown",
        user=None,
        status=AuditStatus.DENIED,
        status_code=401,
        request=request,
        details={"reason": reason}
    )


def log_auth_logout(repo: AuditLogRepository, user: User, request: Request) -> AuditEvent:
    return create_event(
        repo=repo,
        event_type=AuditEventType.AUTH_LOGOUT,
        action="LOGOUT",
        target_type="AUTH",
        target_id=user.username,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={"notice": "Session terminated."}
    )


def log_case_view(repo: AuditLogRepository, user: User, case_id: str, request: Request, is_graph: bool = False) -> AuditEvent:
    evt_type = AuditEventType.CASE_VIEW_GRAPH if is_graph else AuditEventType.CASE_VIEW_DOSSIER
    return create_event(
        repo=repo,
        event_type=evt_type,
        action="VIEW_GRAPH" if is_graph else "VIEW_DOSSIER",
        target_type="CASE",
        target_id=case_id,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request
    )


def log_case_register(repo: AuditLogRepository, user: User, new_case_id: str, request: Request) -> AuditEvent:
    return create_event(
        repo=repo,
        event_type=AuditEventType.CASE_REGISTER,
        action="REGISTER",
        target_type="CASE",
        target_id=new_case_id,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=201,
        request=request,
        details={"notice": "Case registered and automatically assigned to registering officer."}
    )


def log_entity_view(repo: AuditLogRepository, user: User, entity_id: str, request: Request, is_family: bool = False, is_person: bool = True) -> AuditEvent:
    if is_family:
        evt_type = AuditEventType.FAMILY_VIEW_PROFILE
        action = "VIEW_FAMILY"
    elif is_person:
        evt_type = AuditEventType.PERSON_VIEW_DOSSIER
        action = "VIEW_PERSON"
    else:
        evt_type = AuditEventType.ENTITY_VIEW
        action = "VIEW_ENTITY"

    return create_event(
        repo=repo,
        event_type=evt_type,
        action=action,
        target_type="PERSON" if (is_person or is_family) else "ENTITY",
        target_id=entity_id,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request
    )


def log_search_query(
    repo: AuditLogRepository,
    user: User,
    request: Request,
    search_mode: str,
    filter_keys: Optional[List[str]] = None,
    query_length: int = 0,
    result_count: int = 0
) -> AuditEvent:
    """
    CRITICAL SEARCH PRIVACY: Never stores raw free-text query string.
    Only stores search mode, active filter keys, query length, and result count.
    """
    return create_event(
        repo=repo,
        event_type=AuditEventType.SEARCH_EXECUTE,
        action="SEARCH",
        target_type="SEARCH",
        target_id=search_mode,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={
            "search_mode": search_mode,
            "filter_keys": filter_keys or [],
            "query_length": query_length,
            "result_count": result_count
        }
    )


def log_priority_view(repo: AuditLogRepository, user: User, request: Request, lead_count: int = 0) -> AuditEvent:
    return create_event(
        repo=repo,
        event_type=AuditEventType.PRIORITY_LEADS_VIEW,
        action="VIEW_PRIORITY",
        target_type="PRIORITY",
        target_id="PRIORITY_LEADS",
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={"lead_count": lead_count}
    )


def log_assistant_query(
    repo: AuditLogRepository,
    user: User,
    request: Request,
    intent: str,
    response_state: str,
    question_length: int
) -> AuditEvent:
    """
    CRITICAL AI PRIVACY: Never stores raw investigator question or generated markdown text.
    Only stores structured intent, response state, and character length.
    """
    return create_event(
        repo=repo,
        event_type=AuditEventType.ASSISTANT_QUERY,
        action="QUERY_ASSISTANT",
        target_type="ASSISTANT",
        target_id=intent,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={
            "intent": intent,
            "response_state": response_state,
            "question_length": question_length
        }
    )


def log_citizen_case_view(repo: AuditLogRepository, user: User, case_id: str, request: Request) -> AuditEvent:
    return create_event(
        repo=repo,
        event_type=AuditEventType.CITIZEN_CASE_VIEW,
        action="VIEW_CITIZEN_CASE",
        target_type="CASE",
        target_id=case_id,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request
    )


def log_unauthorized_access_denied(
    repo: AuditLogRepository,
    request: Request,
    status_code: int = 403,
    reason: str = "Access forbidden",
    user: Optional[User] = None,
    target_type: str = "RESOURCE",
    target_id: Optional[str] = None
) -> AuditEvent:
    """
    Authoritative handler for 401/403 denials.
    """
    if request:
        request.state.audit_denial_recorded = True

    return create_event(
        repo=repo,
        event_type=AuditEventType.UNAUTHORIZED_ACCESS_DENIED,
        action="ACCESS_DENIED",
        target_type=target_type,
        target_id=target_id or (request.url.path if request else "unknown"),
        user=user,
        status=AuditStatus.DENIED,
        status_code=status_code,
        request=request,
        details={"reason": reason}
    )


def log_provenance_edge_view(
    repo: AuditLogRepository,
    user: User,
    request: Request,
    edge_id: str,
    case_id: str,
    detection_method: str
) -> AuditEvent:
    return create_event(
        repo=repo,
        event_type=AuditEventType.PROVENANCE_EDGE_VIEW,
        action="VIEW_EDGE_PROVENANCE",
        target_type="GRAPH_EDGE",
        target_id=edge_id,
        user=user,
        status=AuditStatus.SUCCESS,
        status_code=200,
        request=request,
        details={
            "case_id": case_id,
            "detection_method": detection_method
        }
    )

