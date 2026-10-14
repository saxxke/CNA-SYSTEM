"""
permissions.py
==============
Centralized Role-Based Access Control (RBAC) permissions definitions and role-permission mappings.

Supported Roles:
- CITIZEN
- INVESTIGATING_OFFICER
- IPS_OFFICER
- HOME_MINISTRY
"""

from enum import Enum
from typing import Set, Dict, Iterable, Union
from .roles import UserRole


class Permission(str, Enum):
    # Citizen permissions
    VIEW_OWN_CASES = "VIEW_OWN_CASES"
    VIEW_OWN_CASE_STATUS = "VIEW_OWN_CASE_STATUS"
    VIEW_AUTHORIZED_UPDATES = "VIEW_AUTHORIZED_UPDATES"

    # Investigating Officer permissions
    VIEW_ASSIGNED_CASES = "VIEW_ASSIGNED_CASES"
    CREATE_CASE = "CREATE_CASE"
    UPDATE_CASE = "UPDATE_CASE"
    VIEW_PEOPLE = "VIEW_PEOPLE"
    VIEW_NETWORK = "VIEW_NETWORK"
    SEARCH_INVESTIGATION_DATA = "SEARCH_INVESTIGATION_DATA"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"
    VIEW_PRIORITY_LEADS = "VIEW_PRIORITY_LEADS"
    USE_AI_ASSISTANT = "USE_AI_ASSISTANT"

    # IPS Officer permissions
    VIEW_AUTHORIZED_CASES = "VIEW_AUTHORIZED_CASES"
    VIEW_CROSS_CASE_ANALYTICS = "VIEW_CROSS_CASE_ANALYTICS"
    GENERATE_REPORTS = "GENERATE_REPORTS"

    # Audit logging permissions (Supervisory and Oversight)
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"

    # Home Ministry permissions
    VIEW_AGGREGATED_ANALYTICS = "VIEW_AGGREGATED_ANALYTICS"
    VIEW_TRENDS = "VIEW_TRENDS"
    VIEW_REGIONAL_STATISTICS = "VIEW_REGIONAL_STATISTICS"
    GENERATE_STRATEGIC_REPORTS = "GENERATE_STRATEGIC_REPORTS"


ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.CITIZEN: {
        Permission.VIEW_OWN_CASES,
        Permission.VIEW_OWN_CASE_STATUS,
        Permission.VIEW_AUTHORIZED_UPDATES,
    },
    UserRole.INVESTIGATING_OFFICER: {
        Permission.VIEW_ASSIGNED_CASES,
        Permission.CREATE_CASE,
        Permission.UPDATE_CASE,
        Permission.VIEW_PEOPLE,
        Permission.VIEW_NETWORK,
        Permission.SEARCH_INVESTIGATION_DATA,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_PRIORITY_LEADS,
        Permission.USE_AI_ASSISTANT,
    },
    UserRole.IPS_OFFICER: {
        Permission.VIEW_AUTHORIZED_CASES,
        Permission.CREATE_CASE,
        Permission.UPDATE_CASE,
        Permission.VIEW_PEOPLE,
        Permission.VIEW_NETWORK,
        Permission.SEARCH_INVESTIGATION_DATA,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_CROSS_CASE_ANALYTICS,
        Permission.VIEW_PRIORITY_LEADS,
        Permission.USE_AI_ASSISTANT,
        Permission.GENERATE_REPORTS,
        Permission.VIEW_AUDIT_LOGS,
    },
    UserRole.HOME_MINISTRY: {
        Permission.VIEW_AGGREGATED_ANALYTICS,
        Permission.VIEW_TRENDS,
        Permission.VIEW_REGIONAL_STATISTICS,
        Permission.GENERATE_STRATEGIC_REPORTS,
        Permission.VIEW_AUDIT_LOGS,
    },
}


def get_role_permissions(role: Union[UserRole, str]) -> Set[Permission]:
    """
    Returns the set of permissions assigned to the given role.
    """
    if isinstance(role, str):
        try:
            role = UserRole(role.strip().upper())
        except ValueError:
            return set()
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Union[UserRole, str], permission: Permission) -> bool:
    """
    Checks whether a role possesses a specific permission.
    """
    return permission in get_role_permissions(role)


def check_role_has_any_permission(role: Union[UserRole, str], permissions: Iterable[Permission]) -> bool:
    """
    Checks whether a role possesses at least one of the specified permissions.
    """
    user_perms = get_role_permissions(role)
    return any(p in user_perms for p in permissions)
