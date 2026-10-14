"""
test_auth_api.py
================
Comprehensive integration test suite for Phase 2: Backend Authentication API.

Endpoints under test:
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout

Coverage:
1. Successful citizen login
2. Successful IO login
3. Successful IPS login
4. Successful Home Ministry login
5. Incorrect password
6. Unknown username
7. Inactive account
8. Missing username
9. Missing password
10. Malformed authentication
11. Valid /api/auth/me
12. /api/auth/me without authentication
13. Invalid authentication
14. Logout
15. Authentication after logout where applicable
16. Password hash never appears in API response
17. Plaintext password never appears in API response
18. Role comes from backend user record
19. Client cannot change role during login
20. Client cannot impersonate another user by modifying user_id
21. Preservation: Existing APIs (e.g. /api/health) continue functioning without regression
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from modules.auth.roles import UserRole
from modules.auth.demo_users import DEMO_CREDENTIALS, get_demo_user_repository
from modules.auth.tokens import TokenStore
from modules.auth.models import User
from modules.auth.security import hash_password


@pytest.fixture
def auth_client():
    """
    TestClient fixture with fresh in-memory UserRepository and TokenStore.
    """
    with TestClient(app) as client:
        # Reset to pristine demo user repo and token store for every test
        client.app.state.user_repo = get_demo_user_repository()
        client.app.state.token_store = TokenStore()
        yield client


# =====================================================================
# 1-4. Successful Login for all 4 Roles
# =====================================================================

def test_successful_citizen_login(auth_client):
    """1. Successful citizen login returns token and CITIZEN role."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "citizen.demo",
        "password": DEMO_CREDENTIALS["citizen.demo"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data and len(data["token"]) > 20
    assert data["token_type"] == "bearer"
    user = data["user"]
    assert user["username"] == "citizen.demo"
    assert user["role"] == UserRole.CITIZEN.value
    assert user["active"] is True
    assert user["jurisdiction"] is None


def test_successful_io_login(auth_client):
    """2. Successful IO login returns token and INVESTIGATING_OFFICER role."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "io.demo",
        "password": DEMO_CREDENTIALS["io.demo"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    user = data["user"]
    assert user["username"] == "io.demo"
    assert user["role"] == UserRole.INVESTIGATING_OFFICER.value
    assert user["jurisdiction"] == "Raipur District"


def test_successful_ips_login(auth_client):
    """3. Successful IPS login returns token and IPS_OFFICER role."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "ips.demo",
        "password": DEMO_CREDENTIALS["ips.demo"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    user = data["user"]
    assert user["username"] == "ips.demo"
    assert user["role"] == UserRole.IPS_OFFICER.value
    assert user["jurisdiction"] == "Chhattisgarh State"


def test_successful_home_ministry_login(auth_client):
    """4. Successful Home Ministry login returns token and HOME_MINISTRY role."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "hm.demo",
        "password": DEMO_CREDENTIALS["hm.demo"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    user = data["user"]
    assert user["username"] == "hm.demo"
    assert user["role"] == UserRole.HOME_MINISTRY.value
    assert user["jurisdiction"] == "National / Central"


# =====================================================================
# 5-10. Failed Login & Edge Cases
# =====================================================================

def test_incorrect_password(auth_client):
    """5. Incorrect password returns 401 Unauthorized."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "citizen.demo",
        "password": "WrongPassword@123"
    })
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]


def test_unknown_username(auth_client):
    """6. Nonexistent username returns uniform 401 Unauthorized without leaking info."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "nonexistent.user",
        "password": "SomePassword#123"
    })
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]


def test_inactive_account(auth_client):
    """7. Inactive account returns 401 Unauthorized."""
    # Add an inactive user
    repo = auth_client.app.state.user_repo
    inactive_user = User(
        user_id="usr_test_inactive",
        username="inactive.demo",
        password_hash=hash_password("InactivePass@2026"),
        role=UserRole.CITIZEN,
        display_name="Inactive User",
        active=False
    )
    repo.add_user(inactive_user)

    resp = auth_client.post("/api/auth/login", json={
        "username": "inactive.demo",
        "password": "InactivePass@2026"
    })
    assert resp.status_code == 401
    assert "inactive" in resp.json()["detail"].lower()


def test_missing_username(auth_client):
    """8. Missing or empty username returns error (400 or 422)."""
    # Empty string in payload
    resp = auth_client.post("/api/auth/login", json={
        "username": "",
        "password": "ValidPassword@123"
    })
    assert resp.status_code in [400, 422]

    # Field omitted completely
    resp2 = auth_client.post("/api/auth/login", json={
        "password": "ValidPassword@123"
    })
    assert resp2.status_code in [400, 422]


def test_missing_password(auth_client):
    """9. Missing or empty password returns error (400 or 422)."""
    resp = auth_client.post("/api/auth/login", json={
        "username": "citizen.demo",
        "password": ""
    })
    assert resp.status_code in [400, 422]

    resp2 = auth_client.post("/api/auth/login", json={
        "username": "citizen.demo"
    })
    assert resp2.status_code in [400, 422]


def test_malformed_authentication(auth_client):
    """10. Malformed Authorization header returns 401 Unauthorized."""
    # Header with invalid format (more than 2 parts or not Bearer)
    headers = {"Authorization": "Basic randomstring123"}
    resp = auth_client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 401


# =====================================================================
# 11-15. /api/auth/me and /api/auth/logout
# =====================================================================

def test_valid_auth_me(auth_client):
    """11. Valid /api/auth/me returns authenticated user's public info."""
    # Login as IO
    login_resp = auth_client.post("/api/auth/login", json={
        "username": "io.demo",
        "password": DEMO_CREDENTIALS["io.demo"]
    })
    token = login_resp.json()["token"]

    # Call /api/auth/me with Bearer token
    me_resp = auth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    user = me_resp.json()
    assert user["username"] == "io.demo"
    assert user["role"] == UserRole.INVESTIGATING_OFFICER.value
    assert user["jurisdiction"] == "Raipur District"
    assert user["active"] is True
    assert "password_hash" not in user


def test_auth_me_without_authentication(auth_client):
    """12. /api/auth/me without authentication returns 401 Unauthorized."""
    resp = auth_client.get("/api/auth/me")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_invalid_authentication(auth_client):
    """13. /api/auth/me with invalid or forged token returns 401 Unauthorized."""
    resp = auth_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer forged_invalid_token_99999"}
    )
    assert resp.status_code == 401


def test_logout(auth_client):
    """14. POST /api/auth/logout invalidates session and returns success."""
    login_resp = auth_client.post("/api/auth/login", json={
        "username": "ips.demo",
        "password": DEMO_CREDENTIALS["ips.demo"]
    })
    token = login_resp.json()["token"]

    # Logout
    logout_resp = auth_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True


def test_authentication_after_logout(auth_client):
    """15. Accessing protected /api/auth/me after logout is rejected with 401."""
    login_resp = auth_client.post("/api/auth/login", json={
        "username": "hm.demo",
        "password": DEMO_CREDENTIALS["hm.demo"]
    })
    token = login_resp.json()["token"]

    # First verify /me works
    me_before = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_before.status_code == 200

    # Perform logout
    auth_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})

    # Accessing /me with same token must now fail
    me_after = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.status_code == 401
    assert "revoked" in me_after.json()["detail"].lower() or "invalid" in me_after.json()["detail"].lower()


# =====================================================================
# 16-20. Security Assurances
# =====================================================================

def test_password_hash_never_appears_in_api_response(auth_client):
    """16. Password hash never appears in login or /me response."""
    login_resp = auth_client.post("/api/auth/login", json={
        "username": "citizen.demo",
        "password": DEMO_CREDENTIALS["citizen.demo"]
    })
    token = login_resp.json()["token"]
    login_body = login_resp.text
    assert "password_hash" not in login_body
    assert "pbkdf2_sha256" not in login_body

    me_resp = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    me_body = me_resp.text
    assert "password_hash" not in me_body
    assert "pbkdf2_sha256" not in me_body


def test_plaintext_password_never_appears_in_api_response(auth_client):
    """17. Plaintext password never appears in login or /me response."""
    password = DEMO_CREDENTIALS["io.demo"]
    login_resp = auth_client.post("/api/auth/login", json={
        "username": "io.demo",
        "password": password
    })
    token = login_resp.json()["token"]
    assert password not in login_resp.text

    me_resp = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert password not in me_resp.text


def test_role_comes_from_backend_user_record(auth_client):
    """18. Role is authoritative from backend user repository, not client."""
    login_resp = auth_client.post("/api/auth/login", json={
        "username": "citizen.demo",
        "password": DEMO_CREDENTIALS["citizen.demo"]
    })
    assert login_resp.json()["user"]["role"] == UserRole.CITIZEN.value


def test_client_cannot_change_role_during_login(auth_client):
    """19. Client supplying role='HOME_MINISTRY' when logging into citizen cannot elevate role."""
    malicious_payload = {
        "username": "citizen.demo",
        "password": DEMO_CREDENTIALS["citizen.demo"],
        "role": "HOME_MINISTRY",
        "role_level": 4,
        "is_admin": True
    }
    resp = auth_client.post("/api/auth/login", json=malicious_payload)
    assert resp.status_code == 200
    user = resp.json()["user"]
    # Role MUST remain CITIZEN
    assert user["role"] == UserRole.CITIZEN.value
    assert user["role"] != "HOME_MINISTRY"

    # Verify /me confirms role is CITIZEN
    token = resp.json()["token"]
    me_resp = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.json()["role"] == UserRole.CITIZEN.value


def test_client_cannot_impersonate_by_modifying_user_id(auth_client):
    """20. Client supplying user_id during login or /me cannot impersonate another user."""
    malicious_payload = {
        "username": "citizen.demo",
        "password": DEMO_CREDENTIALS["citizen.demo"],
        "user_id": "usr_demo_hm"  # Attemping to claim Home Ministry ID
    }
    resp = auth_client.post("/api/auth/login", json=malicious_payload)
    assert resp.status_code == 200
    user = resp.json()["user"]
    # user_id must be citizen.demo's real ID (usr_demo_citizen), NOT usr_demo_hm
    assert user["user_id"] == "usr_demo_citizen"
    assert user["user_id"] != "usr_demo_hm"

    # Also check /me query parameter tampering
    token = resp.json()["token"]
    me_resp = auth_client.get(
        "/api/auth/me?user_id=usr_demo_hm",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.json()["user_id"] == "usr_demo_citizen"


# =====================================================================
# 21. Preservation of Existing Endpoints
# =====================================================================

def test_existing_health_endpoint_remains_public(auth_client):
    """21. GET /api/health remains publicly accessible and unchanged."""
    resp = auth_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
