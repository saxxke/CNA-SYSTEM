"""
audit_models.py
===============
Core data models and enums for Phase 7 Audit Logging.

Guarantees:
- Immutable audit record model (frozen Pydantic model).
- Strict event type taxonomy.
- Standardized accountability attributes (actor, action, target, status, IP, timestamp).
- Zero raw credential or sensitive dossier leakage in schema.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILED = "FAILED"


class AuditEventType(str, Enum):
    # Authentication events
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILURE = "AUTH_LOGIN_FAILURE"
    AUTH_LOGOUT = "AUTH_LOGOUT"

    # Case operational events
    CASE_VIEW_DOSSIER = "CASE_VIEW_DOSSIER"
    CASE_VIEW_GRAPH = "CASE_VIEW_GRAPH"
    CASE_REGISTER = "CASE_REGISTER"

    # Entity & Family events
    PERSON_VIEW_DOSSIER = "PERSON_VIEW_DOSSIER"
    ENTITY_VIEW = "ENTITY_VIEW"
    FAMILY_VIEW_PROFILE = "FAMILY_VIEW_PROFILE"

    # Intelligence & Discovery events
    SEARCH_EXECUTE = "SEARCH_EXECUTE"
    PRIORITY_LEADS_VIEW = "PRIORITY_LEADS_VIEW"
    ASSISTANT_QUERY = "ASSISTANT_QUERY"
    CROSS_CASE_ANALYTICS_VIEW = "CROSS_CASE_ANALYTICS_VIEW"

    # Citizen Portal events
    CITIZEN_CASE_VIEW = "CITIZEN_CASE_VIEW"

    # Provenance events (Phase 8)
    PROVENANCE_EDGE_VIEW = "PROVENANCE_EDGE_VIEW"

    # Security & Access Control events
    UNAUTHORIZED_ACCESS_DENIED = "UNAUTHORIZED_ACCESS_DENIED"


class AuditEvent(BaseModel):
    """
    Immutable representation of an audited security or operational event.
    frozen=True prevents modification or monkey-patching after creation.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(description="Unique monotonic/UUID identifier for the audit record.")
    timestamp: str = Field(description="ISO 8601 UTC timestamp of the event.")
    actor_user_id: str = Field(description="Server-verified user ID of the actor or 'anonymous'.")
    actor_username: str = Field(description="Server-verified username or 'anonymous'.")
    actor_role: str = Field(description="Server-verified role (CITIZEN, INVESTIGATING_OFFICER, IPS_OFFICER, HOME_MINISTRY, or ANONYMOUS).")
    actor_jurisdiction: Optional[str] = Field(default=None, description="Officer's configured territorial/supervisory jurisdiction.")
    
    event_type: AuditEventType = Field(description="Categorized event type.")
    action: str = Field(description="Action verb: LOGIN, LOGOUT, VIEW, SEARCH, REGISTER, QUERY, ACCESS_DENIED.")
    target_type: str = Field(description="Target classification: CASE, PERSON, ENTITY, NETWORK, SEARCH, ASSISTANT, AUTH, SYSTEM.")
    target_id: Optional[str] = Field(default=None, description="Specific target ID touched (e.g. CASE-001, PERSON-001).")
    
    status: AuditStatus = Field(description="Outcome: SUCCESS, DENIED, or FAILED.")
    status_code: int = Field(description="HTTP status code associated with the outcome.")
    request_path: str = Field(description="API endpoint path requested.")
    ip_address: Optional[str] = Field(default="127.0.0.1", description="Client IP address.")
    details: Dict[str, Any] = Field(default_factory=dict, description="Sanitized, non-sensitive operational metadata.")


class AuditLogQueryResponse(BaseModel):
    """
    Paginated read-only response for supervisory audit log queries.
    """
    model_config = ConfigDict(frozen=True)

    total_count: int
    limit: int
    offset: int
    events: List[AuditEvent]
