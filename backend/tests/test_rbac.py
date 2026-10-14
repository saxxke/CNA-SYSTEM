"""
test_rbac.py
============
Comprehensive test suite for Phase 3: Backend Role-Based Access Control (RBAC).

Coverage:
AUTHENTICATION
1. Unauthenticated protected API -> 401
2. Valid authenticated user -> accepted where permitted

CITIZEN
3. Citizen -> investigator-only endpoint -> 403
4. Citizen -> network -> 403
5. Citizen -> priority -> 403
6. Citizen -> investigator analytics -> 403

IO
7. IO -> investigation API -> allowed (200)
8. IO -> network -> allowed (200)
9. IO -> analytics -> allowed (200)
10. IO -> priority -> allowed (200)
11. IO -> AI assistant -> allowed (200)

IPS
12. IPS -> investigation APIs -> allowed (200)
13. IPS -> network -> allowed (200)
14. IPS -> analytics -> allowed (200)
15. IPS -> cross-case analytics -> allowed (200)
16. IPS -> priority -> allowed (200)
17. IPS -> reports -> allowed (200)

HOME MINISTRY
18. Home Ministry -> aggregated analytics -> allowed (200)
19. Home Ministry -> strategic trends -> allowed (200)
20. Home Ministry -> regional statistics -> allowed (200)
21. Home Ministry -> investigator-only person data -> denied (403)
22. Home Ministry -> unrestricted investigation network -> denied (403)

PRIVILEGE ESCALATION & SECURITY
23. Client sends role=CITIZEN while authenticated as IO -> backend authoritative role used
24. Client sends role=IPS while authenticated as Citizen -> denied 403
25. Client sends another user_id -> backend ignores client user_id
26. Client attempts to manipulate authorization headers -> 401
27. Client attempts direct access to restricted endpoint -> 403
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from modules.auth.demo_users import DEMO_CREDENTIALS, get_demo_user_repository
from modules.auth.tokens import TokenStore


@pytest.fixture(scope="module")
def rbac_client():
    """
    TestClient configured with fresh in-memory UserRepository and TokenStore.
    Runs with strict unmocked RBAC enforcement.
    """
    with TestClient(app) as client:
        client.app.state.user_repo = get_demo_user_repository()
        client.app.state.token_store = TokenStore()
        yield client


@pytest.fixture(scope="module")
def auth_tokens(rbac_client):
    """
    Helper fixture obtaining valid session bearer tokens for all 4 demo users.
    """
    tokens = {}
    for username, password in DEMO_CREDENTIALS.items():
        resp = rbac_client.post("/api/auth/login", json={
            "username": username,
            "password": password
        })
        assert resp.status_code == 200, f"Login failed for {username}"
        tokens[username] = resp.json()["token"]
    return tokens


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1-2. Authentication Baseline
# =====================================================================

def test_unauthenticated_protected_api_returns_401(rbac_client):
    """1. Accessing a protected endpoint without authentication returns 401."""
    resp = rbac_client.get("/api/cases")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_valid_authenticated_user_accepted_where_permitted(rbac_client, auth_tokens):
    """2. Valid authenticated user is accepted on permitted endpoints."""
    io_token = auth_tokens["io.demo"]
    resp = rbac_client.get("/api/cases", headers=auth_header(io_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# =====================================================================
# 3-6. Citizen Access Restrictions
# =====================================================================

def test_citizen_investigator_cases_denied(rbac_client, auth_tokens):
    """3. Citizen attempting to access investigator cases returns 403."""
    cit_token = auth_tokens["citizen.demo"]
    resp = rbac_client.get("/api/cases", headers=auth_header(cit_token))
    assert resp.status_code == 403


def test_citizen_network_denied(rbac_client, auth_tokens):
    """4. Citizen attempting to access investigation network returns 403."""
    cit_token = auth_tokens["citizen.demo"]
    resp = rbac_client.get("/api/network", headers=auth_header(cit_token))
    assert resp.status_code == 403


def test_citizen_priority_denied(rbac_client, auth_tokens):
    """5. Citizen attempting to access priority scores returns 403."""
    cit_token = auth_tokens["citizen.demo"]
    resp = rbac_client.get("/api/priority", headers=auth_header(cit_token))
    assert resp.status_code == 403


def test_citizen_investigator_analytics_denied(rbac_client, auth_tokens):
    """6. Citizen attempting to access investigator analytics returns 403."""
    cit_token = auth_tokens["citizen.demo"]
    resp = rbac_client.get("/api/analytics", headers=auth_header(cit_token))
    assert resp.status_code == 403


# =====================================================================
# 7-11. Investigating Officer (IO) Permissions
# =====================================================================

def test_io_investigation_cases_allowed(rbac_client, auth_tokens):
    """7. IO accessing investigation cases is allowed."""
    io_token = auth_tokens["io.demo"]
    resp = rbac_client.get("/api/cases", headers=auth_header(io_token))
    assert resp.status_code == 200


def test_io_network_allowed(rbac_client, auth_tokens):
    """8. IO accessing network graph is allowed."""
    io_token = auth_tokens["io.demo"]
    resp = rbac_client.get("/api/network", headers=auth_header(io_token))
    assert resp.status_code == 200


def test_io_analytics_allowed(rbac_client, auth_tokens):
    """9. IO accessing analytics is allowed."""
    io_token = auth_tokens["io.demo"]
    resp = rbac_client.get("/api/analytics", headers=auth_header(io_token))
    assert resp.status_code == 200


def test_io_priority_allowed(rbac_client, auth_tokens):
    """10. IO accessing priority leads is allowed."""
    io_token = auth_tokens["io.demo"]
    resp = rbac_client.get("/api/priority", headers=auth_header(io_token))
    assert resp.status_code == 200


def test_io_assistant_allowed(rbac_client, auth_tokens):
    """11. IO accessing AI assistant is allowed."""
    io_token = auth_tokens["io.demo"]
    resp = rbac_client.post(
        "/api/assistant/query",
        json={"question": "What cases are connected to PERSON-001?"},
        headers=auth_header(io_token)
    )
    assert resp.status_code == 200


# =====================================================================
# 12-17. IPS Officer Permissions
# =====================================================================

def test_ips_investigation_cases_allowed(rbac_client, auth_tokens):
    """12. IPS accessing investigation cases is allowed."""
    ips_token = auth_tokens["ips.demo"]
    resp = rbac_client.get("/api/cases", headers=auth_header(ips_token))
    assert resp.status_code == 200


def test_ips_network_allowed(rbac_client, auth_tokens):
    """13. IPS accessing investigation network is allowed."""
    ips_token = auth_tokens["ips.demo"]
    resp = rbac_client.get("/api/network", headers=auth_header(ips_token))
    assert resp.status_code == 200


def test_ips_analytics_allowed(rbac_client, auth_tokens):
    """14. IPS accessing analytics is allowed."""
    ips_token = auth_tokens["ips.demo"]
    resp = rbac_client.get("/api/analytics", headers=auth_header(ips_token))
    assert resp.status_code == 200


def test_ips_cross_case_analytics_allowed(rbac_client, auth_tokens):
    """15. IPS accessing cross-case analytics is allowed."""
    ips_token = auth_tokens["ips.demo"]
    resp = rbac_client.get("/api/analytics/cross-case", headers=auth_header(ips_token))
    assert resp.status_code == 200
    assert "cross_case_connectivity" in resp.json()


def test_ips_priority_allowed(rbac_client, auth_tokens):
    """16. IPS accessing priority leads is allowed."""
    ips_token = auth_tokens["ips.demo"]
    resp = rbac_client.get("/api/priority", headers=auth_header(ips_token))
    assert resp.status_code == 200


def test_ips_reports_allowed(rbac_client, auth_tokens):
    """17. IPS generating reports is allowed."""
    ips_token = auth_tokens["ips.demo"]
    resp = rbac_client.get("/api/analytics/reports", headers=auth_header(ips_token))
    assert resp.status_code == 200
    assert "report_type" in resp.json()


# =====================================================================
# 18-22. Home Ministry Permissions & Restrictions
# =====================================================================

def test_home_ministry_aggregated_analytics_allowed(rbac_client, auth_tokens):
    """18. Home Ministry accessing aggregated analytics is allowed."""
    hm_token = auth_tokens["hm.demo"]
    resp = rbac_client.get("/api/analytics", headers=auth_header(hm_token))
    assert resp.status_code == 200

    resp_summary = rbac_client.get("/api/summary", headers=auth_header(hm_token))
    assert resp_summary.status_code == 200


def test_home_ministry_strategic_trends_allowed(rbac_client, auth_tokens):
    """19. Home Ministry accessing strategic trends is allowed."""
    hm_token = auth_tokens["hm.demo"]
    resp = rbac_client.get("/api/analytics/strategic-trends", headers=auth_header(hm_token))
    assert resp.status_code == 200


def test_home_ministry_regional_statistics_allowed(rbac_client, auth_tokens):
    """20. Home Ministry accessing regional statistics is allowed."""
    hm_token = auth_tokens["hm.demo"]
    resp = rbac_client.get("/api/analytics/regional-statistics", headers=auth_header(hm_token))
    assert resp.status_code == 200


def test_home_ministry_person_data_denied(rbac_client, auth_tokens):
    """21. Home Ministry attempting to access investigator person data is denied 403."""
    hm_token = auth_tokens["hm.demo"]
    resp = rbac_client.get("/api/persons", headers=auth_header(hm_token))
    assert resp.status_code == 403

    resp_entity = rbac_client.get("/api/entities", headers=auth_header(hm_token))
    assert resp_entity.status_code == 403


def test_home_ministry_network_denied(rbac_client, auth_tokens):
    """22. Home Ministry attempting to access unrestricted network graph is denied 403."""
    hm_token = auth_tokens["hm.demo"]
    resp = rbac_client.get("/api/network", headers=auth_header(hm_token))
    assert resp.status_code == 403


# =====================================================================
# 23-27. Privilege Escalation & Security
# =====================================================================

def test_client_cannot_downgrade_or_alter_role_via_body(rbac_client, auth_tokens):
    """23. Client sending role=CITIZEN in payload while authenticated as IO retains IO rights."""
    io_token = auth_tokens["io.demo"]
    # Send a request with a malicious or tampered role in query/body
    resp = rbac_client.get(
        "/api/cases?role=CITIZEN",
        headers=auth_header(io_token)
    )
    # Backend identity remains IO, permitted
    assert resp.status_code == 200


def test_client_cannot_escalate_role_via_payload(rbac_client, auth_tokens):
    """24. Citizen attempting role escalation to IPS via payload is rejected 403."""
    cit_token = auth_tokens["citizen.demo"]
    resp = rbac_client.get(
        "/api/cases?role=IPS_OFFICER&role_override=1",
        headers=auth_header(cit_token)
    )
    assert resp.status_code == 403


def test_client_cannot_impersonate_another_user_id(rbac_client, auth_tokens):
    """25. Citizen sending another user_id header/param cannot access protected resources."""
    cit_token = auth_tokens["citizen.demo"]
    headers = {
        "Authorization": f"Bearer {cit_token}",
        "X-User-Id": "usr_demo_io",
        "X-Role": "INVESTIGATING_OFFICER"
    }
    resp = rbac_client.get("/api/cases", headers=headers)
    # Backend ignores spoofed headers, evaluates citizen identity -> 403
    assert resp.status_code == 403


def test_malformed_authorization_header_rejected_401(rbac_client):
    """26. Malformed Authorization headers rejected with 401."""
    resp = rbac_client.get("/api/cases", headers={"Authorization": "InvalidScheme token"})
    assert resp.status_code == 401

    resp2 = rbac_client.get("/api/cases", headers={"Authorization": "Bearer "})
    assert resp2.status_code == 401


def test_direct_access_to_restricted_endpoints_denied(rbac_client, auth_tokens):
    """27. Citizen attempting direct access to case graph, priority, or assistant is denied 403."""
    cit_token = auth_tokens["citizen.demo"]

    # Direct case detail
    r1 = rbac_client.get("/api/cases/CASE-001", headers=auth_header(cit_token))
    assert r1.status_code == 403

    # Direct case graph
    r2 = rbac_client.get("/api/cases/CASE-001/graph", headers=auth_header(cit_token))
    assert r2.status_code == 403

    # Direct assistant query
    r3 = rbac_client.post(
        "/api/assistant/query",
        json={"question": "Test question"},
        headers=auth_header(cit_token)
    )
    assert r3.status_code == 403
