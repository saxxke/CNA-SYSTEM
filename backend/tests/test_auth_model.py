"""
test_auth_model.py
==================
Focused tests for Phase 1 Authentication Data Model & Role Definitions.

Test Coverage:
1. Valid user creation (direct and via UserCreate)
2. Secure password hashing (PBKDF2-HMAC-SHA256, unique salts, never plaintext)
3. Password verification (correct matches, wrong passwords fail, timing-safe)
4. All four valid roles (CITIZEN, INVESTIGATING_OFFICER, IPS_OFFICER, HOME_MINISTRY)
5. Invalid role rejection (Pydantic ValidationError / ValueError)
6. Inactive user handling (activation/deactivation, active-only lookup)
7. Fictional demo users (citizen.demo, io.demo, ips.demo, hm.demo)
8. Uniqueness enforcement for usernames (case-insensitive) and user IDs
9. Public model projection (password_hash strictly excluded)
10. Isolation from synthetic investigation dataset
"""

import pytest
from pydantic import ValidationError

from modules.auth.roles import UserRole, validate_role, ROLE_METADATA
from modules.auth.security import (
    hash_password,
    verify_password,
    parse_hash_string,
    DEFAULT_ITERATIONS
)
from modules.auth.models import User, UserPublic, UserCreate
from modules.auth.repository import UserRepository
from modules.auth.demo_users import (
    DEMO_CREDENTIALS,
    DEMO_USER_DEFINITIONS,
    create_demo_users,
    get_demo_user_repository
)


# =====================================================================
# 1. Valid User Creation
# =====================================================================

def test_valid_user_creation_direct():
    """Verify instantiating User with valid parameters succeeds."""
    hashed = hash_password("ValidPassword123")
    user = User(
        user_id="usr_test_001",
        username="officer.sharma",
        password_hash=hashed,
        role=UserRole.INVESTIGATING_OFFICER,
        display_name="Inspector Sharma",
        active=True,
        jurisdiction="Raipur Kotwali"
    )

    assert user.user_id == "usr_test_001"
    assert user.username == "officer.sharma"
    assert user.role == UserRole.INVESTIGATING_OFFICER
    assert user.display_name == "Inspector Sharma"
    assert user.active is True
    assert user.jurisdiction == "Raipur Kotwali"
    assert user.created_at is not None
    assert user.password_hash.startswith("pbkdf2_sha256$")


def test_user_creation_via_user_create():
    """Verify creating a user through UserCreate data transfer model."""
    create_dto = UserCreate(
        username="citizen.user1",
        password="SecurePass@2026",
        role="CITIZEN",
        display_name="Citizen One",
        jurisdiction=None
    )
    user = create_dto.to_user(generated_id="usr_gen_123")

    assert user.user_id == "usr_gen_123"
    assert user.username == "citizen.user1"
    assert user.role == UserRole.CITIZEN
    assert user.check_password("SecurePass@2026") is True
    assert user.check_password("WrongPassword") is False
    # Verify raw password is never stored
    assert not hasattr(user, "password")
    assert "SecurePass@2026" not in user.password_hash


def test_public_user_projection():
    """Verify UserPublic model omits password_hash completely."""
    user = User(
        user_id="usr_pub_001",
        username="ips.verma",
        password_hash=hash_password("SecretPass@2026"),
        role=UserRole.IPS_OFFICER,
        display_name="SP Verma",
        active=True,
        jurisdiction="Bastar Range"
    )
    public_view = user.to_public()

    assert isinstance(public_view, UserPublic)
    assert public_view.user_id == "usr_pub_001"
    assert public_view.username == "ips.verma"
    assert public_view.role == UserRole.IPS_OFFICER
    assert public_view.display_name == "SP Verma"
    assert public_view.jurisdiction == "Bastar Range"
    assert not hasattr(public_view, "password_hash")
    assert "password_hash" not in public_view.model_dump()


# =====================================================================
# 2. Password Hashing
# =====================================================================

def test_password_hashing_security():
    """Verify password hashing produces salted, multi-part PBKDF2 hashes."""
    raw_pass = "ComplexSecretPassword#2026"
    hash1 = hash_password(raw_pass)
    hash2 = hash_password(raw_pass)

    # Hash should NOT equal plaintext
    assert hash1 != raw_pass
    assert raw_pass not in hash1

    # Unique salts mean identical passwords generate distinct hashes
    assert hash1 != hash2

    # Parse structure
    prefix, iters, salt, dk = parse_hash_string(hash1)
    assert prefix == "pbkdf2_sha256"
    assert iters == DEFAULT_ITERATIONS
    assert len(salt) == 32  # 16 bytes hex encoded
    assert len(dk) == 64    # SHA-256 derived key (32 bytes hex encoded)


def test_password_hashing_rejects_empty():
    """Verify hashing rejects empty strings or non-string types."""
    with pytest.raises(ValueError):
        hash_password("")
    with pytest.raises(ValueError):
        hash_password(None)  # type: ignore


# =====================================================================
# 3. Password Verification
# =====================================================================

def test_password_verification():
    """Verify correct password succeeds and incorrect fails."""
    plain = "InvestigatorSecretKey@2026"
    h = hash_password(plain)

    # Correct match
    assert verify_password(plain, h) is True

    # Case sensitivity check
    assert verify_password(plain.lower(), h) is False

    # Wrong passwords fail
    assert verify_password("IncorrectPassword", h) is False
    assert verify_password("", h) is False
    assert verify_password(None, h) is False  # type: ignore

    # Malformed hash string fails safely without unhandled crash
    assert verify_password(plain, "corrupted_hash_string") is False
    assert verify_password(plain, "") is False


# =====================================================================
# 4. All Four Valid Roles
# =====================================================================

@pytest.mark.parametrize("role_enum, role_str", [
    (UserRole.CITIZEN, "CITIZEN"),
    (UserRole.INVESTIGATING_OFFICER, "INVESTIGATING_OFFICER"),
    (UserRole.IPS_OFFICER, "IPS_OFFICER"),
    (UserRole.HOME_MINISTRY, "HOME_MINISTRY"),
])
def test_all_four_valid_roles(role_enum, role_str):
    """Verify all four supported roles can be validated and assigned."""
    assert validate_role(role_enum) == role_enum
    assert validate_role(role_str) == role_enum
    assert validate_role(role_str.lower()) == role_enum

    # Check metadata exists
    assert role_enum in ROLE_METADATA
    assert "title" in ROLE_METADATA[role_enum]

    # Check user creation with this role
    u = User(
        user_id=f"usr_{role_str.lower()}",
        username=f"user.{role_str.lower()}",
        password_hash=hash_password("Pass12345"),
        role=role_enum,
        display_name=f"Test {role_str}",
        active=True
    )
    assert u.role == role_enum


# =====================================================================
# 5. Invalid Role Rejection
# =====================================================================

@pytest.mark.parametrize("invalid_role", [
    "ADMIN",
    "SUPERUSER",
    "POLICE_OFFICER",
    "ANALYST",
    "ROOT",
    "",
    "   ",
    "UNKNOWN_ROLE",
])
def test_invalid_role_rejection(invalid_role):
    """Verify unsupported roles are rejected by validator and model."""
    with pytest.raises(ValueError):
        validate_role(invalid_role)

    with pytest.raises(ValidationError):
        User(
            user_id="usr_invalid",
            username="bad.role.user",
            password_hash=hash_password("Pass12345"),
            role=invalid_role,  # type: ignore
            display_name="Invalid Role User",
            active=True
        )


# =====================================================================
# 6. Inactive User Handling
# =====================================================================

def test_inactive_user_handling():
    """Verify inactive users are tracked, detected, and filtered."""
    repo = UserRepository()
    active_user = User(
        user_id="usr_act_01",
        username="active.officer",
        password_hash=hash_password("PassActive123"),
        role=UserRole.INVESTIGATING_OFFICER,
        display_name="Active Officer",
        active=True
    )
    inactive_user = User(
        user_id="usr_inact_01",
        username="retired.officer",
        password_hash=hash_password("PassRetired123"),
        role=UserRole.INVESTIGATING_OFFICER,
        display_name="Retired Officer",
        active=False
    )
    repo.add_user(active_user)
    repo.add_user(inactive_user)

    # Active status queries
    assert repo.is_user_active("usr_act_01") is True
    assert repo.is_user_active("active.officer") is True
    assert repo.is_user_active("usr_inact_01") is False
    assert repo.is_user_active("retired.officer") is False

    # get_active_user_by_username returns None for inactive user
    assert repo.get_active_user_by_username("active.officer") is not None
    assert repo.get_active_user_by_username("retired.officer") is None

    # Deactivate active user
    assert repo.deactivate_user("active.officer") is True
    assert repo.is_user_active("active.officer") is False
    assert repo.get_active_user_by_username("active.officer") is None

    # Reactivate
    assert repo.activate_user("active.officer") is True
    assert repo.is_user_active("active.officer") is True

    # List filtering
    assert len(repo.list_users(include_inactive=True)) == 2
    assert len(repo.list_users(include_inactive=False)) == 1


# =====================================================================
# 7. Demo Users
# =====================================================================

def test_demo_users_presence_and_credentials():
    """Verify all 4 fictional demo users exist with expected properties."""
    demo_users = create_demo_users()
    assert len(demo_users) == 4

    usernames = {u.username: u for u in demo_users}
    expected_usernames = ["citizen.demo", "io.demo", "ips.demo", "hm.demo"]

    for uname in expected_usernames:
        assert uname in usernames, f"Missing demo user: {uname}"
        u = usernames[uname]
        assert u.active is True
        assert u.password_hash.startswith("pbkdf2_sha256$")

        # Verify password check against fictional reference credentials
        raw_pw = DEMO_CREDENTIALS[uname]
        assert u.check_password(raw_pw) is True
        assert u.check_password("BadPassword") is False

    # Verify roles
    assert usernames["citizen.demo"].role == UserRole.CITIZEN
    assert usernames["io.demo"].role == UserRole.INVESTIGATING_OFFICER
    assert usernames["ips.demo"].role == UserRole.IPS_OFFICER
    assert usernames["hm.demo"].role == UserRole.HOME_MINISTRY

    # Verify jurisdictions
    assert usernames["citizen.demo"].jurisdiction is None
    assert usernames["io.demo"].jurisdiction == "Raipur District"
    assert usernames["ips.demo"].jurisdiction == "Chhattisgarh State"
    assert usernames["hm.demo"].jurisdiction == "National / Central"


def test_demo_user_repository():
    """Verify get_demo_user_repository pre-seeds the repository properly."""
    repo = get_demo_user_repository()
    assert repo.count() == 4

    # Lookup by username (case-insensitive)
    u_cit = repo.get_by_username("CITIZEN.DEMO")
    assert u_cit is not None
    assert u_cit.username == "citizen.demo"
    assert u_cit.role == UserRole.CITIZEN

    u_io = repo.get_by_username("io.demo")
    assert u_io is not None
    assert u_io.role == UserRole.INVESTIGATING_OFFICER

    u_ips = repo.get_by_username("IPS.DEMO")
    assert u_ips is not None
    assert u_ips.role == UserRole.IPS_OFFICER

    u_hm = repo.get_by_username("hm.demo")
    assert u_hm is not None
    assert u_hm.role == UserRole.HOME_MINISTRY


# =====================================================================
# 8. Uniqueness of Usernames and User IDs
# =====================================================================

def test_uniqueness_enforcement():
    """Verify repository rejects duplicate user_ids and duplicate usernames."""
    repo = UserRepository()

    u1 = User(
        user_id="usr_uniq_01",
        username="unique.user",
        password_hash=hash_password("Pass12345"),
        role=UserRole.CITIZEN,
        display_name="User One",
        active=True
    )
    repo.add_user(u1)

    # Duplicate user_id with different username
    u_dup_id = User(
        user_id="usr_uniq_01",
        username="different.user",
        password_hash=hash_password("Pass12345"),
        role=UserRole.CITIZEN,
        display_name="User Duplicate ID",
        active=True
    )
    with pytest.raises(ValueError, match="already exists"):
        repo.add_user(u_dup_id)

    # Duplicate username (exact match)
    u_dup_name = User(
        user_id="usr_uniq_02",
        username="unique.user",
        password_hash=hash_password("Pass12345"),
        role=UserRole.CITIZEN,
        display_name="User Duplicate Name",
        active=True
    )
    with pytest.raises(ValueError, match="already exists"):
        repo.add_user(u_dup_name)

    # Duplicate username (case-insensitive match)
    u_dup_name_case = User(
        user_id="usr_uniq_03",
        username="UNIQUE.USER",
        password_hash=hash_password("Pass12345"),
        role=UserRole.CITIZEN,
        display_name="User Duplicate Case",
        active=True
    )
    with pytest.raises(ValueError, match="already exists"):
        repo.add_user(u_dup_name_case)


# =====================================================================
# 9. Isolation from Dataset
# =====================================================================

def test_isolation_from_investigation_dataset():
    """Verify auth entities do not write to or pollute dataset files."""
    import os
    dataset_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    assert os.path.isdir(dataset_dir)

    # Ensure no auth user names or roles are in baseline files
    cases_csv = os.path.join(dataset_dir, "cases.csv")
    assert os.path.isfile(cases_csv)

    with open(cases_csv, "r", encoding="utf-8") as f:
        content = f.read()
        assert "citizen.demo" not in content
        assert "io.demo" not in content
        assert "usr_demo_" not in content
