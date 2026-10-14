"""
dependencies.py
===============
FastAPI shared dependency injections for dataset context and authentication.
"""

from typing import Optional, Any, List, Set, Dict
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from modules.auth.roles import UserRole
from modules.auth.permissions import Permission, get_role_permissions
from modules.auth.models import User, UserPublic
from modules.auth.repository import UserRepository
from modules.auth.tokens import TokenStore
from modules.auth.demo_users import get_demo_user_repository
from modules.auth.citizen_access import CitizenAccessRepository, create_demo_citizen_access_repository
from modules.auth.investigation_access import (
    InvestigationAccessRepository,
    create_demo_investigation_access_repository,
)
from modules.auth.audit_repository import (
    AuditLogRepository,
    create_demo_audit_repository,
)

# Module-level singletons used as robust fallbacks
_default_user_repo = get_demo_user_repository()
_default_token_store = TokenStore()
_default_citizen_access_repo = create_demo_citizen_access_repository()
_default_investigation_access_repo = create_demo_investigation_access_repository()
_default_audit_repo = create_demo_audit_repository()

http_bearer_scheme = HTTPBearer(auto_error=False)




# --- Existing Investigation Context Dependencies ---

def _ensure_dataset_loaded(app):
    if not hasattr(app.state, "cases") or not app.state.cases:
        from modules.graph.dataset_integration import build_dataset_graph, get_case_inventory
        from modules.analytics.graph_analytics import analyze_graph
        from modules.priority.priority_scorer import calculate_priority_scores

        cases = get_case_inventory()
        G = build_dataset_graph()
        analytics = analyze_graph(G)
        priority = calculate_priority_scores(G, analytics)

        app.state.cases = cases
        app.state.graph = G
        app.state.analytics = analytics
        app.state.priority = priority

def get_graph(request: Request):
    _ensure_dataset_loaded(request.app)
    return request.app.state.graph

def get_analytics(request: Request):
    _ensure_dataset_loaded(request.app)
    return request.app.state.analytics

def get_priority(request: Request):
    _ensure_dataset_loaded(request.app)
    return request.app.state.priority

def get_cases(request: Request):
    _ensure_dataset_loaded(request.app)
    return request.app.state.cases


# --- Authentication Dependencies ---

def get_user_repo(request: Request) -> UserRepository:
    """
    Retrieves the active UserRepository from application state,
    falling back to module singleton if uninitialized.
    """
    if hasattr(request.app.state, "user_repo") and request.app.state.user_repo is not None:
        return request.app.state.user_repo
    return _default_user_repo


def get_token_store(request: Request) -> TokenStore:
    """
    Retrieves the active TokenStore from application state,
    falling back to module singleton if uninitialized.
    """
    if hasattr(request.app.state, "token_store") and request.app.state.token_store is not None:
        return request.app.state.token_store
    return _default_token_store


def extract_bearer_token(request: Request) -> Optional[str]:
    """
    Extracts the bearer token from the Authorization header.
    Handles 'Bearer <token>' or raw token formats.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        return None

    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    elif len(parts) == 1:
        # Fallback if raw token passed without 'Bearer ' prefix
        return parts[0]
    return None


def get_current_user(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repo),
    token_store: TokenStore = Depends(get_token_store)
) -> User:
    """
    Dependency that extracts, validates, and resolves the current authenticated user.
    Enforces active user account status.
    Raises HTTP 401 if missing, invalid, expired, revoked, or account inactive.
    """
    token = extract_bearer_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    session = token_store.get_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = user_repo.get_by_id(session.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user record not found.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def require_authenticated_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Explicit alias dependency to require an authenticated active user.
    """
    return current_user


def get_current_user_public(
    current_user: User = Depends(require_authenticated_user)
) -> UserPublic:
    """
    Returns public user representation safely stripped of credentials.
    """
    return current_user.to_public()


def require_role(*allowed_roles: UserRole):
    """
    Factory creating a FastAPI dependency that checks if the authenticated user
    possesses one of the specified roles.
    Raises HTTP 401 if unauthenticated, HTTP 403 if role unauthorized.
    """
    normalized_roles = set(allowed_roles)

    def role_dependency(
        current_user: User = Depends(require_authenticated_user)
    ) -> User:
        if current_user.role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Insufficient role permissions."
            )
        return current_user

    return role_dependency


def require_permission(*required_permissions: Permission):
    """
    Factory creating a FastAPI dependency that checks if the authenticated user
    possesses ANY of the specified permissions.
    Raises HTTP 401 if unauthenticated, HTTP 403 if permission missing.
    """
    perms_set = set(required_permissions)

    def permission_dependency(
        current_user: User = Depends(require_authenticated_user)
    ) -> User:
        user_perms = get_role_permissions(current_user.role)
        if not perms_set.intersection(user_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Insufficient role permissions."
            )
        return current_user

    return permission_dependency


def get_citizen_access_repo(request: Request) -> CitizenAccessRepository:
    """
    Retrieves the active CitizenAccessRepository from application state,
    falling back to module singleton if uninitialized.
    """
    if hasattr(request.app.state, "citizen_access_repo") and request.app.state.citizen_access_repo is not None:
        return request.app.state.citizen_access_repo
    return _default_citizen_access_repo


def require_citizen_case_access(
    case_id: str,
    current_user: User = Depends(require_role(UserRole.CITIZEN)),
    citizen_repo: CitizenAccessRepository = Depends(get_citizen_access_repo),
    cases: list = Depends(get_cases)
) -> dict:
    """
    Object-level authorization dependency:
    1. Enforce authenticated user has role CITIZEN.
    2. Check if case_id exists in system case inventory (if not, HTTP 404).
    3. Check if current_user.user_id is explicitly authorized for this case (if not, HTTP 403).
    4. Return the raw case record for citizen-safe serialization.
    """
    clean_case_id = case_id.strip().upper()

    # 1. Verify case exists in system inventory
    matching_case = None
    for c in cases:
        cid = c.get("case_id") or c.get("id")
        if cid and str(cid).strip().upper() == clean_case_id:
            matching_case = c
            break

    if not matching_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case record '{case_id}' not found."
        )

    # 2. Enforce object-level authorization for this specific citizen
    if not citizen_repo.has_access(current_user.user_id, clean_case_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view this case."
        )

    return matching_case
 
 
# --- Investigation-Level Authorization Dependencies (IO & IPS) ---

def get_investigation_access_repo(request: Request) -> InvestigationAccessRepository:
    """
    Retrieves the active InvestigationAccessRepository from application state,
    falling back to module singleton if uninitialized.
    """
    if hasattr(request.app.state, "investigation_access_repo") and request.app.state.investigation_access_repo is not None:
        return request.app.state.investigation_access_repo
    return _default_investigation_access_repo


def get_audit_repo(request: Request) -> AuditLogRepository:
    """
    Retrieves the active AuditLogRepository from application state,
    falling back to module singleton if uninitialized.
    """
    if hasattr(request.app.state, "audit_repo") and request.app.state.audit_repo is not None:
        return request.app.state.audit_repo
    return _default_audit_repo


def get_officer_authorized_case_ids(
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    cases: list = Depends(get_cases)
) -> set:
    """
    Resolves the precise set of Case IDs for which the authenticated officer has
    full operational investigation authority:
    - IPS_OFFICER: All cases in their supervisory state jurisdiction.
    - INVESTIGATING_OFFICER: Active case assignments within their territorial jurisdiction.
    """
    return inv_repo.get_authorized_case_ids_for_officer(
        user_id=current_user.user_id,
        user_role=current_user.role.value,
        all_cases=cases
    )


def require_investigation_case_access(
    case_id: str,
    current_user: User = Depends(require_permission(Permission.VIEW_ASSIGNED_CASES, Permission.VIEW_AUTHORIZED_CASES)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    cases: list = Depends(get_cases)
) -> dict:
    """
    Object-level authorization dependency for Case dossiers:
    1. Verifies case exists in system inventory (404 if not found).
    2. Validates territorial jurisdiction (403 if outside jurisdiction).
    3. For IO: Enforces active case assignment (Need-to-Know) (403 if unassigned).
    4. For IPS: Validates supervisory state jurisdiction (403 if outside state).
    5. Returns case record if authorized.
    """
    clean_case_id = case_id.strip().upper()

    # 1. Verify case exists in system inventory
    matching_case = None
    for c in cases:
        cid = c.get("case_id") or c.get("id")
        if cid and str(cid).strip().upper() == clean_case_id:
            matching_case = c
            break

    if not matching_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case record '{case_id}' not found."
        )

    # 2. Enforce territorial jurisdiction
    in_jurisdiction = inv_repo.is_case_in_jurisdiction(current_user.user_id, matching_case)
    if not in_jurisdiction:
        scope = inv_repo.get_jurisdiction(current_user.user_id)
        level_label = scope.level.value if scope else "assigned"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Case '{clean_case_id}' is outside your {level_label.lower()} jurisdiction."
        )

    # 3. For IO: Enforce active case assignment (Need-to-Know)
    if current_user.role == UserRole.INVESTIGATING_OFFICER:
        if not inv_repo.is_case_assigned(current_user.user_id, clean_case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted: Need-to-know authorization required. Case '{clean_case_id}' is not assigned to you."
            )

    return matching_case


def is_entity_in_authorized_scope(
    entity_id: str,
    authorized_case_ids: set,
    G: Any,
    persons_by_id: dict = None,
    scope: Any = None
) -> bool:
    """
    Determines if an entity (PERSON, PHONE, VEHICLE, BANK_ACCOUNT, etc.) is
    accessible to an officer:
    1. If entity has relationships with an authorized case -> True.
    2. If entity is a PERSON residing in the officer's jurisdiction -> True.
    3. Otherwise -> False.
    """
    if not entity_id:
        return False

    clean_id = entity_id.strip()

    # Check graph edge case connections
    if G is not None and clean_id in G:
        for _, _, _, d in G.in_edges(clean_id, data=True, keys=True):
            cid = (d.get("case_id") or "").strip().upper()
            if cid in authorized_case_ids:
                return True
        for _, _, _, d in G.out_edges(clean_id, data=True, keys=True):
            cid = (d.get("case_id") or "").strip().upper()
            if cid in authorized_case_ids:
                return True

    # Check person location within jurisdiction
    if persons_by_id and clean_id in persons_by_id and scope:
        p = persons_by_id[clean_id]
        if scope.covers_person(p):
            return True

    return False



