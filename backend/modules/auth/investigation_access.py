"""
investigation_access.py
=======================
Backend object-level investigation authorization models and repository for:
- INVESTIGATING_OFFICER (IO): Actively assigned cases within territorial jurisdiction.
- IPS_OFFICER: Full supervisory access within state jurisdiction.

Security Principles:
- Backend is the ultimate security authority.
- Client role claims, query params, or headers (X-Role, X-Jurisdiction) are NEVER trusted.
- Fail closed: Any unassigned or indeterminate access defaults to HTTP 403 Forbidden.
- Unassigned same-jurisdiction cases do NOT expose sensitive investigation dossiers, evidence, or rosters.
- Outside-jurisdiction cases are strictly denied.
"""

from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Set, Any
from pydantic import BaseModel, Field, ConfigDict


class JurisdictionLevel(str, Enum):
    POLICE_STATION = "POLICE_STATION"
    DISTRICT = "DISTRICT"
    STATE = "STATE"
    NATIONAL = "NATIONAL"


class JurisdictionScope(BaseModel):
    """
    Territorial or operational jurisdiction scope assigned to an officer.
    """
    model_config = ConfigDict(extra="forbid")

    level: JurisdictionLevel
    district: Optional[str] = None
    state: Optional[str] = None
    police_station: Optional[str] = None

    def covers_case(self, case_record: Dict[str, Any]) -> bool:
        """
        Determines whether the given case falls within this jurisdiction scope.
        """
        if self.level == JurisdictionLevel.NATIONAL:
            return True

        details = case_record.get("details", case_record)
        c_state = str(details.get("state") or case_record.get("state") or "").strip().lower()
        c_district = str(details.get("district") or case_record.get("district") or "").strip().lower()
        c_station = str(details.get("police_station") or case_record.get("police_station") or "").strip().lower()

        if self.level == JurisdictionLevel.STATE:
            if not self.state:
                return False
            return self.state.strip().lower() in c_state or c_state in self.state.strip().lower()

        if self.level == JurisdictionLevel.DISTRICT:
            if not self.district:
                return False
            # Normalize "Raipur District" vs "Raipur"
            my_dist = self.district.strip().lower().replace(" district", "")
            c_dist = c_district.replace(" district", "")
            return my_dist == c_dist

        if self.level == JurisdictionLevel.POLICE_STATION:
            if not self.police_station:
                return False
            return self.police_station.strip().lower() in c_station

        return False

    def covers_person(self, person_record: Dict[str, Any]) -> bool:
        """
        Determines whether a person's recorded location falls within this jurisdiction.
        """
        if self.level == JurisdictionLevel.NATIONAL:
            return True

        p_state = str(person_record.get("state") or "").strip().lower()
        p_district = str(person_record.get("district") or "").strip().lower()

        if self.level == JurisdictionLevel.STATE:
            if not self.state:
                return False
            return self.state.strip().lower() in p_state or p_state in self.state.strip().lower()

        if self.level == JurisdictionLevel.DISTRICT:
            if not self.district:
                return False
            my_dist = self.district.strip().lower().replace(" district", "")
            p_dist = p_district.replace(" district", "")
            return my_dist == p_dist

        return False


class OfficerCaseAssignment(BaseModel):
    """
    Active assignment linking an Investigating Officer to a specific case.
    """
    model_config = ConfigDict(extra="forbid")

    assignment_id: str
    user_id: str
    case_id: str
    role_in_case: str = Field(default="LEAD_INVESTIGATOR", description="LEAD_INVESTIGATOR, ASSISTING_OFFICER, SUPERVISOR")
    assigned_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of assignment."
    )
    active: bool = Field(default=True, description="Whether the assignment is currently active.")
    assigned_by: str = Field(default="SYSTEM_DISPATCH", description="Officer/authority who made the assignment.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Default synthetic assignments for demo users
# io.demo (usr_demo_io) is assigned to CASE-001, CASE-002, CASE-003 in Raipur
DEMO_IO_ASSIGNED_CASES: List[str] = [
    "CASE-001",
    "CASE-002",
    "CASE-003",
]


class InvestigationAccessRepository:
    """
    Thread-safe in-memory repository managing officer jurisdictions and case assignments.
    """

    def __init__(self):
        self._lock = RLock()
        # Mapping: user_id -> JurisdictionScope
        self._jurisdictions: Dict[str, JurisdictionScope] = {}
        # Mapping: user_id -> Dict[case_id, OfficerCaseAssignment]
        self._assignments: Dict[str, Dict[str, OfficerCaseAssignment]] = {}

    def set_jurisdiction(self, user_id: str, scope: JurisdictionScope) -> None:
        if not user_id or not user_id.strip():
            raise ValueError("user_id must be non-empty.")
        with self._lock:
            self._jurisdictions[user_id.strip()] = scope

    def get_jurisdiction(self, user_id: str) -> Optional[JurisdictionScope]:
        if not user_id:
            return None
        with self._lock:
            return self._jurisdictions.get(user_id.strip())

    def assign_case(
        self,
        user_id: str,
        case_id: str,
        role_in_case: str = "LEAD_INVESTIGATOR",
        assigned_by: str = "SYSTEM_DISPATCH",
        active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OfficerCaseAssignment:
        if not user_id or not user_id.strip():
            raise ValueError("user_id must be non-empty.")
        if not case_id or not case_id.strip():
            raise ValueError("case_id must be non-empty.")

        uid = user_id.strip()
        cid = case_id.strip().upper()
        asgn_id = f"asgn_{uid}_{cid}"

        with self._lock:
            if uid not in self._assignments:
                self._assignments[uid] = {}

            record = OfficerCaseAssignment(
                assignment_id=asgn_id,
                user_id=uid,
                case_id=cid,
                role_in_case=role_in_case,
                active=active,
                assigned_by=assigned_by,
                metadata=metadata or {}
            )
            self._assignments[uid][cid] = record
            return record

    def revoke_assignment(self, user_id: str, case_id: str) -> bool:
        if not user_id or not case_id:
            return False
        uid = user_id.strip()
        cid = case_id.strip().upper()
        with self._lock:
            user_asgns = self._assignments.get(uid)
            if not user_asgns or cid not in user_asgns:
                return False
            user_asgns[cid].active = False
            return True

    def get_assigned_case_ids(self, user_id: str, active_only: bool = True) -> Set[str]:
        if not user_id:
            return set()
        uid = user_id.strip()
        with self._lock:
            user_asgns = self._assignments.get(uid, {})
            if active_only:
                return {cid for cid, rec in user_asgns.items() if rec.active}
            return set(user_asgns.keys())

    def is_case_assigned(self, user_id: str, case_id: str) -> bool:
        if not user_id or not case_id:
            return False
        return case_id.strip().upper() in self.get_assigned_case_ids(user_id, active_only=True)

    def is_case_in_jurisdiction(self, user_id: str, case_record: Dict[str, Any]) -> bool:
        """
        Checks whether the case falls within the officer's territorial jurisdiction.
        """
        scope = self.get_jurisdiction(user_id)
        if not scope:
            return False
        return scope.covers_case(case_record)

    def is_case_authorized(
        self,
        user_id: str,
        user_role: str,
        case_id: str,
        case_record: Dict[str, Any]
    ) -> bool:
        """
        Enforces complete object-level investigation authorization:
        - IPS_OFFICER: Authorized if case falls within configured state jurisdiction.
        - INVESTIGATING_OFFICER: Authorized ONLY IF actively assigned AND within jurisdiction.
        """
        cid = case_id.strip().upper()
        scope = self.get_jurisdiction(user_id)
        if not scope:
            return False

        # Verify jurisdiction first
        if not scope.covers_case(case_record):
            return False

        if user_role == "IPS_OFFICER":
            # Supervisory state jurisdiction confers case access without individual assignment
            return True

        if user_role == "INVESTIGATING_OFFICER":
            # Must be actively assigned AND within jurisdiction
            return self.is_case_assigned(user_id, cid)

        return False

    def get_authorized_case_ids_for_officer(
        self,
        user_id: str,
        user_role: str,
        all_cases: List[Dict[str, Any]]
    ) -> Set[str]:
        """
        Returns set of case IDs for which the officer has full operational investigation access.
        """
        scope = self.get_jurisdiction(user_id)
        if not scope:
            return set()

        if user_role == "IPS_OFFICER":
            # All cases covered by state jurisdiction
            return {
                (c.get("case_id") or c.get("id") or "").strip().upper()
                for c in all_cases
                if scope.covers_case(c) and (c.get("case_id") or c.get("id"))
            }

        if user_role == "INVESTIGATING_OFFICER":
            # Active assignments that ALSO fall within officer's jurisdiction
            assigned = self.get_assigned_case_ids(user_id, active_only=True)
            return {
                (c.get("case_id") or c.get("id") or "").strip().upper()
                for c in all_cases
                if (c.get("case_id") or c.get("id") or "").strip().upper() in assigned
                and scope.covers_case(c)
            }

        return set()

    def get_jurisdiction_case_ids(
        self,
        user_id: str,
        all_cases: List[Dict[str, Any]]
    ) -> Set[str]:
        """
        Returns all case IDs within the officer's territorial jurisdiction (assigned + unassigned).
        """
        scope = self.get_jurisdiction(user_id)
        if not scope:
            return set()
        return {
            (c.get("case_id") or c.get("id") or "").strip().upper()
            for c in all_cases
            if scope.covers_case(c) and (c.get("case_id") or c.get("id"))
        }

    def clear(self) -> None:
        with self._lock:
            self._jurisdictions.clear()
            self._assignments.clear()


def create_demo_investigation_access_repository() -> InvestigationAccessRepository:
    """
    Initializes and seeds the InvestigationAccessRepository with realistic demo configurations:
    - io.demo (usr_demo_io): Raipur District jurisdiction + active assignment to CASE-001, CASE-002, CASE-003.
    - ips.demo (usr_demo_ips): Chhattisgarh State supervisory jurisdiction (covers all Raipur cases).
    - hm.demo (usr_demo_hm): National oversight.
    """
    repo = InvestigationAccessRepository()

    # 1. IO Demo Configuration
    io_user_id = "usr_demo_io"
    repo.set_jurisdiction(
        io_user_id,
        JurisdictionScope(
            level=JurisdictionLevel.DISTRICT,
            district="Raipur",
            state="Chhattisgarh",
            police_station="Fictional PS No.1, Raipur"
        )
    )
    for cid in DEMO_IO_ASSIGNED_CASES:
        repo.assign_case(
            user_id=io_user_id,
            case_id=cid,
            role_in_case="LEAD_INVESTIGATOR",
            assigned_by="SP_RAIPUR",
            active=True,
            metadata={"priority": "HIGH", "dispatch_unit": "Raipur CID Unit 1"}
        )

    # 2. IPS Demo Configuration
    ips_user_id = "usr_demo_ips"
    repo.set_jurisdiction(
        ips_user_id,
        JurisdictionScope(
            level=JurisdictionLevel.STATE,
            state="Chhattisgarh"
        )
    )

    # 3. Home Ministry Demo Configuration
    hm_user_id = "usr_demo_hm"
    repo.set_jurisdiction(
        hm_user_id,
        JurisdictionScope(
            level=JurisdictionLevel.NATIONAL
        )
    )

    return repo
