"""
auth
====
Authentication data models, role definitions, security primitives, and user store.
"""

from .roles import UserRole, ROLE_METADATA, validate_role
from .security import hash_password, verify_password, parse_hash_string
from .models import User, UserPublic, UserCreate
from .repository import UserRepository
from .tokens import TokenSession, TokenStore
from .demo_users import (
    DEMO_CREDENTIALS,
    DEMO_USER_DEFINITIONS,
    create_demo_users,
    get_demo_user_repository
)

from .permissions import (
    Permission,
    ROLE_PERMISSIONS,
    has_permission,
    get_role_permissions,
    check_role_has_any_permission,
)
from .citizen_access import (
    CitizenCaseAccess,
    CitizenAccessRepository,
    DEMO_CITIZEN_AUTHORIZED_CASES,
    create_demo_citizen_access_repository,
)
from .investigation_access import (
    JurisdictionLevel,
    JurisdictionScope,
    OfficerCaseAssignment,
    InvestigationAccessRepository,
    DEMO_IO_ASSIGNED_CASES,
    create_demo_investigation_access_repository,
)
from .audit_models import (
    AuditStatus,
    AuditEventType,
    AuditEvent,
    AuditLogQueryResponse,
)
from .audit_repository import (
    AuditLogRepository,
    create_demo_audit_repository,
)
from .audit_service import (
    create_event,
    log_auth_success,
    log_auth_failure,
    log_auth_logout,
    log_case_view,
    log_case_register,
    log_entity_view,
    log_search_query,
    log_priority_view,
    log_assistant_query,
    log_citizen_case_view,
    log_unauthorized_access_denied,
)

__all__ = [
    "UserRole",
    "ROLE_METADATA",
    "validate_role",
    "hash_password",
    "verify_password",
    "parse_hash_string",
    "User",
    "UserPublic",
    "UserCreate",
    "UserRepository",
    "TokenSession",
    "TokenStore",
    "DEMO_CREDENTIALS",
    "DEMO_USER_DEFINITIONS",
    "create_demo_users",
    "get_demo_user_repository",
    "Permission",
    "ROLE_PERMISSIONS",
    "has_permission",
    "get_role_permissions",
    "check_role_has_any_permission",
    "CitizenCaseAccess",
    "CitizenAccessRepository",
    "DEMO_CITIZEN_AUTHORIZED_CASES",
    "create_demo_citizen_access_repository",
    "JurisdictionLevel",
    "JurisdictionScope",
    "OfficerCaseAssignment",
    "InvestigationAccessRepository",
    "DEMO_IO_ASSIGNED_CASES",
    "create_demo_investigation_access_repository",
    "AuditStatus",
    "AuditEventType",
    "AuditEvent",
    "AuditLogQueryResponse",
    "AuditLogRepository",
    "create_demo_audit_repository",
    "create_event",
    "log_auth_success",
    "log_auth_failure",
    "log_auth_logout",
    "log_case_view",
    "log_case_register",
    "log_entity_view",
    "log_search_query",
    "log_priority_view",
    "log_assistant_query",
    "log_citizen_case_view",
    "log_unauthorized_access_denied",
]




