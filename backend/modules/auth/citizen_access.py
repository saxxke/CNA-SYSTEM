"""
citizen_access.py
=================
Backend object-level authorization for Citizen users.

Key Security Principle:
- Citizen access MUST be based on explicitly authorized case IDs associated
  with that specific authenticated citizen user.
- Changing a case_id in URL/query/body must NEVER grant access to another citizen's case.
- Distinct and decoupled from synthetic investigation CSV data.
"""

from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field


class CitizenCaseAccess(BaseModel):
    """
    Explicit authorization record linking a citizen user_id to an authorized case_id.
    """
    user_id: str = Field(..., description="Authenticated citizen user ID.")
    case_id: str = Field(..., description="Explicitly authorized case ID.")
    active: bool = Field(default=True, description="Whether access grant is active.")
    granted_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of access grant."
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Access grant metadata.")


# Deterministic demo authorized cases for citizen.demo (usr_demo_citizen)
DEMO_CITIZEN_AUTHORIZED_CASES: List[str] = [
    "CASE-001",
    "CASE-014",
]


class CitizenAccessRepository:
    """
    Thread-safe in-memory repository managing explicit citizen case authorization records.
    """

    def __init__(self):
        self._lock = RLock()
        # Mapping: user_id -> Dict[case_id, CitizenCaseAccess]
        self._access_by_user: Dict[str, Dict[str, CitizenCaseAccess]] = {}

    def grant_access(
        self,
        user_id: str,
        case_id: str,
        active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CitizenCaseAccess:
        """
        Grants or updates explicit case access for a citizen user.
        Thread-safe and prevents duplicate records.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id must be a non-empty string.")
        if not case_id or not case_id.strip():
            raise ValueError("case_id must be a non-empty string.")

        uid = user_id.strip()
        cid = case_id.strip().upper()

        with self._lock:
            if uid not in self._access_by_user:
                self._access_by_user[uid] = {}

            record = CitizenCaseAccess(
                user_id=uid,
                case_id=cid,
                active=active,
                metadata=metadata or {}
            )
            self._access_by_user[uid][cid] = record
            return record

    def revoke_access(self, user_id: str, case_id: str) -> bool:
        """
        Revokes a citizen's explicit access to a case.
        """
        if not user_id or not case_id:
            return False

        uid = user_id.strip()
        cid = case_id.strip().upper()

        with self._lock:
            user_grants = self._access_by_user.get(uid)
            if not user_grants or cid not in user_grants:
                return False
            user_grants[cid].active = False
            return True

    def has_access(self, user_id: str, case_id: str) -> bool:
        """
        Checks whether the citizen user has an active, explicit authorization for case_id.
        """
        if not user_id or not case_id:
            return False

        uid = user_id.strip()
        cid = case_id.strip().upper()

        with self._lock:
            user_grants = self._access_by_user.get(uid)
            if not user_grants:
                return False
            record = user_grants.get(cid)
            return bool(record and record.active)

    def get_authorized_case_ids(self, user_id: str, active_only: bool = True) -> List[str]:
        """
        Returns list of case IDs explicitly authorized for the specified user.
        """
        if not user_id:
            return []

        uid = user_id.strip()
        with self._lock:
            user_grants = self._access_by_user.get(uid, {})
            if active_only:
                return [cid for cid, rec in user_grants.items() if rec.active]
            return list(user_grants.keys())

    def clear(self) -> None:
        """
        Resets all access records.
        """
        with self._lock:
            self._access_by_user.clear()


def create_demo_citizen_access_repository() -> CitizenAccessRepository:
    """
    Initializes a CitizenAccessRepository with explicit demo authorizations
    for citizen.demo (usr_demo_citizen): CASE-001 and CASE-014.
    """
    repo = CitizenAccessRepository()
    demo_user_id = "usr_demo_citizen"

    for case_id in DEMO_CITIZEN_AUTHORIZED_CASES:
        repo.grant_access(
            user_id=demo_user_id,
            case_id=case_id,
            active=True,
            metadata={"source": "demo_seed", "scope": "citizen_case_tracking"}
        )
    return repo
