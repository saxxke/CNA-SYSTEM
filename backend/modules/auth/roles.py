"""
roles.py
========
Role definitions and enumeration for the 4-role authentication system:
1. CITIZEN
2. INVESTIGATING_OFFICER
3. IPS_OFFICER
4. HOME_MINISTRY

All roles represent authorized roles within the investigation intelligence platform.
"""

from enum import Enum
from typing import Set, Dict, Any, Union


class UserRole(str, Enum):
    """
    Supported authentication roles in the platform.
    String-based enum for clean JSON serialization and strict type checking.
    """
    CITIZEN = "CITIZEN"
    INVESTIGATING_OFFICER = "INVESTIGATING_OFFICER"
    IPS_OFFICER = "IPS_OFFICER"
    HOME_MINISTRY = "HOME_MINISTRY"

    @classmethod
    def all_roles(cls) -> Set[str]:
        return {r.value for r in cls}

    @classmethod
    def has_role(cls, role_name: str) -> bool:
        if not isinstance(role_name, str):
            return False
        return role_name.strip().upper() in cls.all_roles()


ROLE_METADATA: Dict[UserRole, Dict[str, Any]] = {
    UserRole.CITIZEN: {
        "title": "Citizen",
        "description": "Citizen user with case-tracking, FIR inquiry, and restricted status view.",
        "level": 1,
        "default_jurisdiction": None,
        "requires_jurisdiction": False,
    },
    UserRole.INVESTIGATING_OFFICER: {
        "title": "Investigating Officer",
        "description": "Field investigator handling case-level evidence, suspect interviews, and local graph analytics.",
        "level": 2,
        "default_jurisdiction": "Police Station / District Level",
        "requires_jurisdiction": True,
    },
    UserRole.IPS_OFFICER: {
        "title": "IPS Officer (Supervisory)",
        "description": "Senior supervisory officer overseeing district-level and state-wide syndicates, cross-case patterns, and priority alerts.",
        "level": 3,
        "default_jurisdiction": "State HQ / Range Level",
        "requires_jurisdiction": True,
    },
    UserRole.HOME_MINISTRY: {
        "title": "Home Ministry (National Oversight)",
        "description": "National policy and strategic oversight authority with high-level multi-state intelligence and macro analytics.",
        "level": 4,
        "default_jurisdiction": "National / Central",
        "requires_jurisdiction": False,
    },
}


def validate_role(role: Union[str, UserRole]) -> UserRole:
    """
    Validates and normalizes a role input into a UserRole enum instance.
    Raises ValueError if role is invalid.
    """
    if isinstance(role, UserRole):
        return role
    if isinstance(role, str):
        normalized = role.strip().upper()
        if UserRole.has_role(normalized):
            return UserRole(normalized)
    valid_roles_str = ", ".join(sorted(UserRole.all_roles()))
    raise ValueError(f"Invalid role '{role}'. Must be one of: {valid_roles_str}")
