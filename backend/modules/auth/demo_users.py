"""
demo_users.py
=============
Fictional demonstration users for development, role testing, and verification.

Rules:
- NEVER use real government identities, police badge numbers, or personal info.
- All accounts use fictional designations for hackathon demonstration.
- NEVER store plaintext passwords on the User model. All passwords are
  securely hashed via PBKDF2-HMAC-SHA256.
- Distinct from the synthetic investigation dataset CSVs.

Demo Users:
1. citizen.demo -> CITIZEN
2. io.demo      -> INVESTIGATING_OFFICER
3. ips.demo     -> IPS_OFFICER
4. hm.demo      -> HOME_MINISTRY
"""

from typing import List, Dict, Any
from .roles import UserRole
from .models import User
from .security import hash_password
from .repository import UserRepository


# Fictional reference credentials strictly for automated testing and dev login hints.
# Stored passwords on the User objects are strictly PBKDF2 cryptographic hashes.
DEMO_CREDENTIALS: Dict[str, str] = {
    "citizen.demo": "DemoCitizen@2026",
    "io.demo":      "DemoInvestigator@2026",
    "ips.demo":     "DemoSupervisory@2026",
    "hm.demo":      "DemoOversight@2026",
}


DEMO_USER_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "user_id": "usr_demo_citizen",
        "username": "citizen.demo",
        "role": UserRole.CITIZEN.value,
        "display_name": "Demo Citizen (Citizen Portal)",
        "jurisdiction": None,
        "jurisdiction_level": None,
        "assigned_cases": [],
        "raw_password": DEMO_CREDENTIALS["citizen.demo"],
    },
    {
        "user_id": "usr_demo_io",
        "username": "io.demo",
        "role": UserRole.INVESTIGATING_OFFICER.value,
        "display_name": "Demo Investigating Officer (Raipur Sub-Division)",
        "jurisdiction": "Raipur District",
        "jurisdiction_level": "DISTRICT",
        "assigned_cases": ["CASE-001", "CASE-002", "CASE-003"],
        "raw_password": DEMO_CREDENTIALS["io.demo"],
    },
    {
        "user_id": "usr_demo_ips",
        "username": "ips.demo",
        "role": UserRole.IPS_OFFICER.value,
        "display_name": "Demo IPS Officer (State Supervisory HQ)",
        "jurisdiction": "Chhattisgarh State",
        "jurisdiction_level": "STATE",
        "assigned_cases": [],
        "raw_password": DEMO_CREDENTIALS["ips.demo"],
    },
    {
        "user_id": "usr_demo_hm",
        "username": "hm.demo",
        "role": UserRole.HOME_MINISTRY.value,
        "display_name": "Demo Home Ministry Officer (National Oversight)",
        "jurisdiction": "National / Central",
        "jurisdiction_level": "NATIONAL",
        "assigned_cases": [],
        "raw_password": DEMO_CREDENTIALS["hm.demo"],
    },
]


def create_demo_users() -> List[User]:
    """
    Instantiates the 4 fictional demo users with securely hashed passwords.
    """
    users = []
    for definition in DEMO_USER_DEFINITIONS:
        user = User(
            user_id=definition["user_id"],
            username=definition["username"],
            password_hash=hash_password(definition["raw_password"]),
            role=UserRole(definition["role"]),
            display_name=definition["display_name"],
            active=True,
            jurisdiction=definition["jurisdiction"],
            jurisdiction_level=definition.get("jurisdiction_level"),
            assigned_cases=definition.get("assigned_cases") or [],
            metadata={"is_demo": True, "environment": "development"}
        )
        users.append(user)
    return users



def get_demo_user_repository() -> UserRepository:
    """
    Returns a fresh UserRepository pre-populated with the 4 demo users.
    """
    repo = UserRepository()
    for user in create_demo_users():
        repo.add_user(user)
    return repo
