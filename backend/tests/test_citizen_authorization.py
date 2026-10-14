"""
test_citizen_authorization.py
==============================
Comprehensive integration test suite for Phase 4: Backend Object-Level Authorization for CITIZEN Users.

Coverage:
1. Citizen login still works
2. Citizen can retrieve their authorized case list
3. Authorized CASE-001 succeeds
4. Another explicitly authorized case (CASE-014) succeeds
5. Unauthorized existing case returns 403
6. Non-existent case returns appropriate 404
7. Citizen cannot access investigator case API
8. Citizen cannot access network
9. Citizen cannot access priority
10. Citizen cannot access investigation search
11. Citizen cannot access AI assistant
12. Citizen cannot access internal person/entity data
13. Case ID substitution is rejected
14. Query manipulation cannot bypass authorization
15. user_id spoofing fails
16. X-User-Id spoofing fails
17. role spoofing fails
18. X-Role spoofing fails
19. Missing token returns 401
20. Invalid token returns 401
21. Inactive citizen returns 401
22. Citizen with zero authorized cases gets empty list
23. One citizen cannot access another citizen's authorized case
24. Existing IO behavior remains valid (and denied citizen-only portal)
25. Existing IPS behavior remains valid (and denied citizen-only portal)
26. Existing Home Ministry behavior remains valid (and denied citizen-only portal)
27. Citizen-safe response does not expose forbidden internal fields
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from modules.auth.demo_users import DEMO_CREDENTIALS, get_demo_user_repository
from modules.auth.tokens import TokenStore
from modules.auth.citizen_access import (
    create_demo_citizen_access_repository,
    CitizenAccessRepository
)
from modules.auth.models import User
from modules.auth.roles import UserRole
from modules.auth.security import hash_password


@pytest.fixture(scope="module")
def client():
    """
    TestClient with fresh demo auth repositories and token store.
    Exercises the real unmocked authentication and authorization stack.
    """
    with TestClient(app) as c:
        c.app.state.user_repo = get_demo_user_repository()
        c.app.state.token_store = TokenStore()
        c.app.state.citizen_access_repo = create_demo_citizen_access_repository()
        yield c


@pytest.fixture(scope="module")
def tokens(client):
    """Obtains authentic session tokens for demo accounts."""
    toks = {}
    for username, password in DEMO_CREDENTIALS.items():
        resp = client.post("/api/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200
        toks[username] = resp.json()["token"]
    return toks


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1-4. Citizen Login & Authorized Case Access
# =====================================================================

def test_1_citizen_login_still_works(client):
    """1. Citizen login succeeds and returns valid bearer token with CITIZEN role."""
    resp = client.post("/api/auth/login", json={
        "username": "citizen.demo",
        "password": DEMO_CREDENTIALS["citizen.demo"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["role"] == UserRole.CITIZEN.value


def test_2_citizen_retrieves_authorized_case_list(client, tokens):
    """2. Citizen retrieves their explicit authorized case list (CASE-001, CASE-014)."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/citizen/cases", headers=auth_header(cit_token))
    assert resp.status_code == 200
    cases = resp.json()
    assert isinstance(cases, list)
    case_ids = [c["case_id"] for c in cases]
    assert "CASE-001" in case_ids
    assert "CASE-014" in case_ids
    assert len(case_ids) == 2


def test_3_authorized_case_001_succeeds(client, tokens):
    """3. Authorized CASE-001 succeeds with 200."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/citizen/cases/CASE-001", headers=auth_header(cit_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "CASE-001"
    assert "Kidnapping" in data["offence_category"]
    assert data["authorized_for_user"] == "citizen.demo"


def test_4_authorized_case_014_succeeds(client, tokens):
    """4. Another explicitly authorized case (CASE-014) succeeds with 200."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/citizen/cases/CASE-014", headers=auth_header(cit_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "CASE-014"
    assert "Extortion" in data["offence_category"]


# =====================================================================
# 5-6. Unauthorized Existing Case & Non-Existent Case
# =====================================================================

def test_5_unauthorized_existing_case_returns_403(client, tokens):
    """5. Unauthorized existing case (e.g. CASE-002, CASE-025) returns 403 Forbidden."""
    cit_token = tokens["citizen.demo"]
    # CASE-002 exists in inventory (250 cases) but is NOT authorized for citizen.demo
    resp = client.get("/api/citizen/cases/CASE-002", headers=auth_header(cit_token))
    assert resp.status_code == 403
    assert "forbidden" in resp.json()["detail"].lower() or "authorized" in resp.json()["detail"].lower()

    # CASE-025 also exists but is unauthorized
    resp2 = client.get("/api/citizen/cases/CASE-025", headers=auth_header(cit_token))
    assert resp2.status_code == 403


def test_6_nonexistent_case_returns_404(client, tokens):
    """6. Non-existent case returns 404 Not Found."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/citizen/cases/CASE-999999", headers=auth_header(cit_token))
    assert resp.status_code == 404


# =====================================================================
# 7-12. Citizen Denied From Investigator Endpoints
# =====================================================================

def test_7_citizen_cannot_access_investigator_case_api(client, tokens):
    """7. Citizen cannot access internal /api/cases endpoints."""
    cit_token = tokens["citizen.demo"]
    r1 = client.get("/api/cases", headers=auth_header(cit_token))
    assert r1.status_code == 403

    r2 = client.get("/api/cases/CASE-001", headers=auth_header(cit_token))
    assert r2.status_code == 403


def test_8_citizen_cannot_access_network(client, tokens):
    """8. Citizen cannot access investigation network."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/network", headers=auth_header(cit_token))
    assert resp.status_code == 403

    resp2 = client.get("/api/relationships", headers=auth_header(cit_token))
    assert resp2.status_code == 403


def test_9_citizen_cannot_access_priority(client, tokens):
    """9. Citizen cannot access priority leads."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/priority", headers=auth_header(cit_token))
    assert resp.status_code == 403


def test_10_citizen_cannot_access_investigation_search(client, tokens):
    """10. Citizen cannot access internal search endpoints."""
    cit_token = tokens["citizen.demo"]
    r1 = client.get("/api/search?q=test", headers=auth_header(cit_token))
    assert r1.status_code == 403

    r2 = client.post("/api/search/advanced", json={"query": "test"}, headers=auth_header(cit_token))
    assert r2.status_code == 403


def test_11_citizen_cannot_access_ai_assistant(client, tokens):
    """11. Citizen cannot access investigator AI assistant."""
    cit_token = tokens["citizen.demo"]
    resp = client.post("/api/assistant/query", json={"question": "Tell me about cases"}, headers=auth_header(cit_token))
    assert resp.status_code == 403


def test_12_citizen_cannot_access_person_entity_data(client, tokens):
    """12. Citizen cannot access internal person dossier or entity endpoints."""
    cit_token = tokens["citizen.demo"]
    r1 = client.get("/api/persons", headers=auth_header(cit_token))
    assert r1.status_code == 403

    r2 = client.get("/api/entities", headers=auth_header(cit_token))
    assert r2.status_code == 403


# =====================================================================
# 13-18. Parameter Manipulation & Spoofing Defense
# =====================================================================

def test_13_case_id_substitution_is_rejected(client, tokens):
    """13. Substituting CASE-001 with CASE-003 or CASE-025 is rejected with 403."""
    cit_token = tokens["citizen.demo"]
    for unauthorized_id in ["CASE-003", "CASE-025", "CASE-100"]:
        resp = client.get(f"/api/citizen/cases/{unauthorized_id}", headers=auth_header(cit_token))
        assert resp.status_code == 403


def test_14_query_manipulation_cannot_bypass_authorization(client, tokens):
    """14. Query parameters like ?case_id=CASE-001 cannot trick endpoint into serving CASE-002."""
    cit_token = tokens["citizen.demo"]
    resp = client.get(
        "/api/citizen/cases/CASE-002?case_id=CASE-001&override=true",
        headers=auth_header(cit_token)
    )
    # Path parameter CASE-002 is evaluated strictly
    assert resp.status_code == 403


def test_15_user_id_spoofing_fails(client, tokens):
    """15. Passing user_id=usr_demo_io in query/body cannot expand authorized cases."""
    cit_token = tokens["citizen.demo"]
    resp = client.get(
        "/api/citizen/cases?user_id=usr_demo_io",
        headers=auth_header(cit_token)
    )
    assert resp.status_code == 200
    cases = resp.json()
    # Still only returns citizen.demo's authorized 2 cases
    assert len(cases) == 2
    assert {c["case_id"] for c in cases} == {"CASE-001", "CASE-014"}


def test_16_x_user_id_header_spoofing_fails(client, tokens):
    """16. X-User-Id header cannot spoof another identity."""
    cit_token = tokens["citizen.demo"]
    headers = {
        "Authorization": f"Bearer {cit_token}",
        "X-User-Id": "usr_demo_io"
    }
    resp = client.get("/api/citizen/cases/CASE-002", headers=headers)
    assert resp.status_code == 403


def test_17_role_spoofing_fails(client, tokens):
    """17. Client supplying role=INVESTIGATING_OFFICER cannot bypass citizen authorization."""
    cit_token = tokens["citizen.demo"]
    resp = client.get(
        "/api/citizen/cases/CASE-002?role=INVESTIGATING_OFFICER",
        headers=auth_header(cit_token)
    )
    assert resp.status_code == 403


def test_18_x_role_header_spoofing_fails(client, tokens):
    """18. X-Role header cannot elevate privileges to investigator."""
    cit_token = tokens["citizen.demo"]
    headers = {
        "Authorization": f"Bearer {cit_token}",
        "X-Role": "INVESTIGATING_OFFICER"
    }
    resp = client.get("/api/cases", headers=headers)
    assert resp.status_code == 403


# =====================================================================
# 19-21. Authentication Enforcement on Citizen API
# =====================================================================

def test_19_missing_token_returns_401(client):
    """19. Citizen endpoints without token return 401 Unauthorized."""
    r1 = client.get("/api/citizen/cases")
    assert r1.status_code == 401

    r2 = client.get("/api/citizen/cases/CASE-001")
    assert r2.status_code == 401


def test_20_invalid_token_returns_401(client):
    """20. Citizen endpoints with forged or invalid token return 401."""
    headers = {"Authorization": "Bearer forged_invalid_token_9999"}
    resp = client.get("/api/citizen/cases", headers=headers)
    assert resp.status_code == 401


def test_21_inactive_citizen_returns_401(client):
    """21. Inactive citizen account is rejected with 401."""
    repo = client.app.state.user_repo
    inactive_citizen = User(
        user_id="usr_cit_inactive",
        username="inactive.citizen",
        password_hash=hash_password("InactivePass123"),
        role=UserRole.CITIZEN,
        display_name="Inactive Citizen",
        active=False
    )
    repo.add_user(inactive_citizen)

    # Login should fail for inactive account
    login_resp = client.post("/api/auth/login", json={
        "username": "inactive.citizen",
        "password": "InactivePass123"
    })
    assert login_resp.status_code == 401


# =====================================================================
# 22-23. Multi-Citizen Isolation & Empty Authorization
# =====================================================================

def test_22_citizen_with_zero_authorized_cases_gets_empty_list(client):
    """22. A citizen with zero authorized cases receives [] (empty list), not all cases."""
    repo = client.app.state.user_repo
    new_citizen = User(
        user_id="usr_cit_no_cases",
        username="empty.citizen",
        password_hash=hash_password("EmptyPass123"),
        role=UserRole.CITIZEN,
        display_name="Citizen with No Cases",
        active=True
    )
    repo.add_user(new_citizen)

    login_resp = client.post("/api/auth/login", json={
        "username": "empty.citizen",
        "password": "EmptyPass123"
    })
    token = login_resp.json()["token"]

    resp = client.get("/api/citizen/cases", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_23_one_citizen_cannot_access_another_citizens_case(client, tokens):
    """23. Citizen A cannot access Citizen B's authorized case, and vice versa."""
    repo = client.app.state.user_repo
    cit_access_repo = client.app.state.citizen_access_repo

    citizen_b = User(
        user_id="usr_cit_second",
        username="second.citizen",
        password_hash=hash_password("SecondPass123"),
        role=UserRole.CITIZEN,
        display_name="Second Citizen",
        active=True
    )
    repo.add_user(citizen_b)

    # Authorize CASE-003 exclusively for second.citizen
    cit_access_repo.grant_access(user_id="usr_cit_second", case_id="CASE-003", active=True)

    login_b = client.post("/api/auth/login", json={
        "username": "second.citizen",
        "password": "SecondPass123"
    })
    token_b = login_b.json()["token"]
    token_a = tokens["citizen.demo"]  # has CASE-001, CASE-014

    # Citizen B accesses own CASE-003 -> 200
    r_b_own = client.get("/api/citizen/cases/CASE-003", headers=auth_header(token_b))
    assert r_b_own.status_code == 200
    assert r_b_own.json()["case_id"] == "CASE-003"

    # Citizen A attempts to access Citizen B's CASE-003 -> 403 Forbidden
    r_a_b = client.get("/api/citizen/cases/CASE-003", headers=auth_header(token_a))
    assert r_a_b.status_code == 403

    # Citizen B attempts to access Citizen A's CASE-001 -> 403 Forbidden
    r_b_a = client.get("/api/citizen/cases/CASE-001", headers=auth_header(token_b))
    assert r_b_a.status_code == 403


# =====================================================================
# 24-26. Other Roles Isolation
# =====================================================================

def test_24_io_denied_from_citizen_portal(client, tokens):
    """24. IO retains investigation access, but is denied citizen portal (role separation)."""
    io_token = tokens["io.demo"]
    # IO can access investigator cases
    r_inv = client.get("/api/cases", headers=auth_header(io_token))
    assert r_inv.status_code == 200

    # IO cannot access citizen portal endpoint
    r_cit = client.get("/api/citizen/cases", headers=auth_header(io_token))
    assert r_cit.status_code == 403


def test_25_ips_denied_from_citizen_portal(client, tokens):
    """25. IPS retains supervisory access, but is denied citizen portal."""
    ips_token = tokens["ips.demo"]
    r_inv = client.get("/api/cases", headers=auth_header(ips_token))
    assert r_inv.status_code == 200

    r_cit = client.get("/api/citizen/cases", headers=auth_header(ips_token))
    assert r_cit.status_code == 403


def test_26_home_ministry_denied_from_citizen_portal(client, tokens):
    """26. Home Ministry retains strategic analytics, but is denied citizen portal."""
    hm_token = tokens["hm.demo"]
    r_strat = client.get("/api/analytics/strategic-trends", headers=auth_header(hm_token))
    assert r_strat.status_code == 200

    r_cit = client.get("/api/citizen/cases", headers=auth_header(hm_token))
    assert r_cit.status_code == 403


# =====================================================================
# 27. Citizen-Safe Data Scrubbing Verification
# =====================================================================

def test_27_citizen_safe_response_does_not_expose_forbidden_fields(client, tokens):
    """27. Citizen response contains ONLY safe fields; internal investigator fields omitted."""
    cit_token = tokens["citizen.demo"]
    resp = client.get("/api/citizen/cases/CASE-001", headers=auth_header(cit_token))
    assert resp.status_code == 200
    data = resp.json()

    # Allowed safe fields
    assert "case_id" in data
    assert "case_title" in data
    assert "offence_category" in data
    assert "status" in data
    assert "police_station" in data
    assert "district" in data
    assert "state"
    assert "official_notice" in data

    # Forbidden internal fields MUST NOT exist
    forbidden_fields = [
        "connected_entities",
        "priority_score",
        "priority_information",
        "graph_metrics",
        "evidence",
        "ground_truth",
        "internal_notes",
        "suspects",
        "persons_of_interest",
        "cdr_records",
        "bank_accounts",
        "vehicles",
        "nodes",
        "edges",
        "degree_centrality",
        "betweenness_centrality",
    ]
    for forbidden in forbidden_fields:
        assert forbidden not in data, f"Forbidden internal field '{forbidden}' leaked to citizen!"
