"""
test_audit_logging.py
=====================
Comprehensive test suite for Phase 7: Lightweight Audit Logging.

Coverage:
1. Login success & failure audit events (single event, correct status)
2. Logout audit events
3. Case dossier & case graph view events
4. Case registration audit events
5. Person & family view audit events
6. Search query audit events with strict sanitization (no raw query strings)
7. AI Assistant query audit events with strict sanitization (no raw questions/answers)
8. Priority leads & cross-case analytics view events
9. Citizen case status inquiry audit events
10. Unauthorized access denial (Need-to-Know 403) produces exactly ONE denial event
11. Outside-jurisdiction denial (403) produces exactly ONE denial event
12. Single-denial-event guarantee (no duplicate denial events)
13. Audit log RBAC:
    - IPS_OFFICER: Allowed (200)
    - HOME_MINISTRY: Allowed (200)
    - INVESTIGATING_OFFICER: Denied (403)
    - CITIZEN: Denied (403)
    - Unauthenticated: Denied (401)
14. Read-only API guarantees: POST/PUT/DELETE /api/audit/logs return 405 Method Not Allowed
15. AuditEvent model immutability (frozen Pydantic model)
16. Bounded sliding-window retention (5,000 events max)
17. Zero credential or sensitive investigation narrative leakage
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from modules.auth.demo_users import DEMO_CREDENTIALS, get_demo_user_repository
from modules.auth.tokens import TokenStore
from modules.auth.citizen_access import create_demo_citizen_access_repository
from modules.auth.investigation_access import create_demo_investigation_access_repository
from modules.auth.audit_repository import AuditLogRepository, create_demo_audit_repository
from modules.auth.audit_models import AuditEvent, AuditEventType, AuditStatus
from pydantic import ValidationError


@pytest.fixture(scope="module")
def client():
    """
    Module-scoped TestClient configured with isolated in-memory stores.
    """
    with TestClient(app) as test_client:
        test_client.app.state.user_repo = get_demo_user_repository()
        test_client.app.state.token_store = TokenStore()
        test_client.app.state.citizen_access_repo = create_demo_citizen_access_repository()
        test_client.app.state.investigation_access_repo = create_demo_investigation_access_repository()
        test_client.app.state.audit_repo = create_demo_audit_repository()
        yield test_client


@pytest.fixture(scope="module")
def tokens(client):
    """
    Retrieves bearer authentication tokens for all demo accounts.
    """
    auth_tokens = {}
    for username, password in DEMO_CREDENTIALS.items():
        resp = client.post("/api/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
        auth_tokens[username] = resp.json()["token"]
    return auth_tokens


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. Authentication Lifecycle Events
# =====================================================================

def test_audit_login_success_recorded(client):
    """Successful authentication logs AUTH_LOGIN_SUCCESS with user identity."""
    audit_repo = client.app.state.audit_repo
    initial_count = audit_repo.get_total_count()

    resp = client.post("/api/auth/login", json={"username": "io.demo", "password": DEMO_CREDENTIALS["io.demo"]})
    assert resp.status_code == 200

    events = audit_repo.query_logs(user_id="io.demo", event_type="AUTH_LOGIN_SUCCESS", limit=10)
    assert len(events) > 0
    latest = events[0]
    assert latest.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
    assert latest.actor_username == "io.demo"
    assert latest.actor_role == "INVESTIGATING_OFFICER"
    assert latest.status == AuditStatus.SUCCESS
    assert latest.status_code == 200


def test_audit_login_failure_recorded_single_event(client):
    """Failed authentication logs AUTH_LOGIN_FAILURE exactly once."""
    audit_repo = client.app.state.audit_repo
    initial_events = len(audit_repo.query_logs(event_type="AUTH_LOGIN_FAILURE"))

    resp = client.post("/api/auth/login", json={"username": "io.demo", "password": "WrongPassword999!"})
    assert resp.status_code == 401

    failure_events = audit_repo.query_logs(event_type="AUTH_LOGIN_FAILURE")
    # Exactly one new failure event must have been recorded
    assert len(failure_events) == initial_events + 1
    latest = failure_events[0]
    assert latest.event_type == AuditEventType.AUTH_LOGIN_FAILURE
    assert latest.target_id == "io.demo"
    assert latest.status == AuditStatus.DENIED
    assert latest.status_code == 401


def test_audit_logout_recorded(client):
    """Logout invalidates session and logs AUTH_LOGOUT event."""
    audit_repo = client.app.state.audit_repo
    # Login temporarily
    resp_login = client.post("/api/auth/login", json={"username": "io.demo", "password": DEMO_CREDENTIALS["io.demo"]})
    token = resp_login.json()["token"]

    resp_logout = client.post("/api/auth/logout", headers=auth_header(token))
    assert resp_logout.status_code == 200

    logout_events = audit_repo.query_logs(user_id="io.demo", event_type="AUTH_LOGOUT", limit=5)
    assert len(logout_events) > 0
    latest = logout_events[0]
    assert latest.event_type == AuditEventType.AUTH_LOGOUT
    assert latest.actor_username == "io.demo"
    assert latest.status == AuditStatus.SUCCESS


# =====================================================================
# 2. Case Operations (Dossier View, Graph View, Registration)
# =====================================================================

def test_audit_case_dossier_view_recorded(client, tokens):
    """Viewing an authorized case dossier logs CASE_VIEW_DOSSIER."""
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]

    resp = client.get("/api/cases/CASE-001", headers=auth_header(token))
    assert resp.status_code == 200

    events = audit_repo.query_logs(event_type="CASE_VIEW_DOSSIER", target_id="CASE-001", limit=5)
    assert len(events) > 0
    latest = events[0]
    assert latest.actor_username == "io.demo"
    assert latest.target_id == "CASE-001"
    assert latest.status == AuditStatus.SUCCESS


def test_audit_case_graph_view_recorded(client, tokens):
    """Viewing a case graph logs CASE_VIEW_GRAPH."""
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]

    resp = client.get("/api/cases/CASE-001/graph", headers=auth_header(token))
    assert resp.status_code == 200

    events = audit_repo.query_logs(event_type="CASE_VIEW_GRAPH", target_id="CASE-001", limit=5)
    assert len(events) > 0
    assert events[0].event_type == AuditEventType.CASE_VIEW_GRAPH


def test_audit_case_registration_recorded(client, tokens):
    """Case registration logs CASE_REGISTER with newly generated Case ID."""
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]

    payload = {
        "case": {
            "title": "Audit Test Incident",
            "description": "Synthesized incident for audit verification",
            "offence_category": "Extortion",
            "incident_date": "2026-09-02",
            "location": "Raipur South",
            "district": "Raipur",
            "state": "Chhattisgarh",
            "police_station": "Civil Lines PS",
            "priority": "LOW"
        },
        "associated_persons": [
            {
                "person_type": "NEW",
                "role": "SUBJECT",
                "new_person_data": {
                    "full_name": "Audit Test Subject",
                    "gender": "Male",
                    "district": "Raipur"
                }
            }
        ]
    }
    resp = client.post("/api/cases/register", json=payload, headers=auth_header(token))
    assert resp.status_code in (200, 201)
    new_cid = resp.json()["case_id"]

    events = audit_repo.query_logs(event_type="CASE_REGISTER", target_id=new_cid, limit=5)
    assert len(events) > 0
    latest = events[0]
    assert latest.target_id == new_cid
    assert latest.actor_username == "io.demo"
    assert latest.status == AuditStatus.SUCCESS


# =====================================================================
# 3. Entity and Family Operations
# =====================================================================

def test_audit_person_and_family_view_recorded(client, tokens):
    """Viewing person profile and family profile logs respective audit events."""
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]

    # Person dossier
    resp_person = client.get("/api/entities/PERSON-001", headers=auth_header(token))
    assert resp_person.status_code == 200
    p_events = audit_repo.query_logs(event_type="PERSON_VIEW_DOSSIER", target_id="PERSON-001", limit=5)
    assert len(p_events) > 0

    # Family profile
    resp_family = client.get("/api/entities/PERSON-001/family", headers=auth_header(token))
    assert resp_family.status_code == 200
    f_events = audit_repo.query_logs(event_type="FAMILY_VIEW_PROFILE", target_id="PERSON-001", limit=5)
    assert len(f_events) > 0
    assert f_events[0].actor_username == "io.demo"


# =====================================================================
# 4. Search & AI Sanitization (Strict Privacy Checks)
# =====================================================================

def test_audit_search_query_sanitization(client, tokens):
    """
    Search queries must be logged with metadata only.
    Raw search text must NEVER be stored in audit records.
    """
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]
    secret_search_term = "ExtremelyConfidentialKeyword987"

    resp = client.get(f"/api/search?q={secret_search_term}", headers=auth_header(token))
    assert resp.status_code == 200

    events = audit_repo.query_logs(event_type="SEARCH_EXECUTE", limit=10)
    assert len(events) > 0
    latest = events[0]

    # Check that the raw confidential search term was NOT stored anywhere in the event
    event_json = latest.model_dump_json()
    assert secret_search_term not in event_json
    assert "query_length" in latest.details
    assert latest.details["query_length"] == len(secret_search_term)


def test_audit_assistant_query_sanitization(client, tokens):
    """
    AI Assistant questions must be logged with intent & state only.
    Raw investigator question and response markdown must NEVER be stored.
    """
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]
    secret_ai_question = "Summarize CASE-001 confidential suspect details"

    resp = client.post("/api/assistant/query", json={"question": secret_ai_question}, headers=auth_header(token))
    assert resp.status_code == 200

    events = audit_repo.query_logs(event_type="ASSISTANT_QUERY", limit=5)
    assert len(events) > 0
    latest = events[0]

    event_json = latest.model_dump_json()
    assert secret_ai_question not in event_json
    assert "intent" in latest.details
    assert "response_state" in latest.details
    assert latest.details["question_length"] == len(secret_ai_question)


# =====================================================================
# 5. Priority, Cross-Case Analytics & Citizen Portals
# =====================================================================

def test_audit_priority_and_cross_case_recorded(client, tokens):
    """Priority and cross-case views are properly recorded."""
    audit_repo = client.app.state.audit_repo

    # Priority view by IO
    resp_p = client.get("/api/priority", headers=auth_header(tokens["io.demo"]))
    assert resp_p.status_code == 200
    p_evts = audit_repo.query_logs(event_type="PRIORITY_LEADS_VIEW", limit=5)
    assert len(p_evts) > 0

    # Cross-case analytics view by IPS
    resp_cc = client.get("/api/analytics/cross-case", headers=auth_header(tokens["ips.demo"]))
    assert resp_cc.status_code == 200
    cc_evts = audit_repo.query_logs(event_type="CROSS_CASE_ANALYTICS_VIEW", limit=5)
    assert len(cc_evts) > 0


def test_audit_citizen_case_view_recorded(client, tokens):
    """Citizen viewing their authorized case status is audited."""
    audit_repo = client.app.state.audit_repo
    token = tokens["citizen.demo"]

    resp = client.get("/api/citizen/cases/CASE-001", headers=auth_header(token))
    assert resp.status_code == 200

    evts = audit_repo.query_logs(event_type="CITIZEN_CASE_VIEW", target_id="CASE-001", limit=5)
    assert len(evts) > 0
    assert evts[0].actor_role == "CITIZEN"


# =====================================================================
# 6. Single Denial Event Guarantee (Need-to-Know & Jurisdiction 403s)
# =====================================================================

def test_unauthorized_access_denial_single_event_need_to_know(client, tokens):
    """
    Accessing an unassigned in-district case (CASE-084) returns 403 and generates
    EXACTLY ONE UNAUTHORIZED_ACCESS_DENIED audit record.
    """
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]
    prev_denials = len(audit_repo.query_logs(event_type="UNAUTHORIZED_ACCESS_DENIED", target_id="CASE-084"))

    resp = client.get("/api/cases/CASE-084", headers=auth_header(token))
    assert resp.status_code == 403

    current_denials = audit_repo.query_logs(event_type="UNAUTHORIZED_ACCESS_DENIED", target_id="CASE-084")
    # Single denial event rule: exactly one new event added
    assert len(current_denials) == prev_denials + 1
    denial_event = current_denials[0]
    assert denial_event.actor_username == "io.demo"
    assert denial_event.status == AuditStatus.DENIED
    assert denial_event.status_code == 403
    assert "Need-to-know" in denial_event.details.get("reason", "")


def test_unauthorized_access_denial_single_event_outside_jurisdiction(client, tokens):
    """
    Accessing outside jurisdiction case (CASE-007) returns 403 and generates
    EXACTLY ONE UNAUTHORIZED_ACCESS_DENIED audit record.
    """
    audit_repo = client.app.state.audit_repo
    token = tokens["io.demo"]
    prev_denials = len(audit_repo.query_logs(event_type="UNAUTHORIZED_ACCESS_DENIED", target_id="CASE-007"))

    resp = client.get("/api/cases/CASE-007", headers=auth_header(token))
    assert resp.status_code == 403

    current_denials = audit_repo.query_logs(event_type="UNAUTHORIZED_ACCESS_DENIED", target_id="CASE-007")
    assert len(current_denials) == prev_denials + 1
    assert current_denials[0].status_code == 403


# =====================================================================
# 7. Audit Log Viewer RBAC & Read-Only Constraints
# =====================================================================

def test_audit_log_access_rbac(client, tokens):
    """
    /api/audit/logs RBAC rules:
    - IPS_OFFICER: 200 OK
    - HOME_MINISTRY: 200 OK
    - INVESTIGATING_OFFICER: 403 Forbidden
    - CITIZEN: 403 Forbidden
    - Unauthenticated: 401 Unauthorized
    """
    # 1. IPS Officer -> 200
    resp_ips = client.get("/api/audit/logs", headers=auth_header(tokens["ips.demo"]))
    assert resp_ips.status_code == 200
    data = resp_ips.json()
    assert "events" in data
    assert "total_count" in data

    # 2. Home Ministry -> 200
    resp_hm = client.get("/api/audit/logs", headers=auth_header(tokens["hm.demo"]))
    assert resp_hm.status_code == 200

    # 3. Investigating Officer -> 403
    resp_io = client.get("/api/audit/logs", headers=auth_header(tokens["io.demo"]))
    assert resp_io.status_code == 403

    # 4. Citizen -> 403
    resp_cit = client.get("/api/audit/logs", headers=auth_header(tokens["citizen.demo"]))
    assert resp_cit.status_code == 403

    # 5. Unauthenticated -> 401
    resp_unauth = client.get("/api/audit/logs")
    assert resp_unauth.status_code == 401


def test_audit_log_no_mutation_apis(client, tokens):
    """
    Audit logging endpoint is strictly read-only.
    POST, PUT, DELETE methods on /api/audit/logs must return 405 Method Not Allowed.
    """
    token = tokens["ips.demo"]

    resp_post = client.post("/api/audit/logs", json={}, headers=auth_header(token))
    assert resp_post.status_code == 405

    resp_put = client.put("/api/audit/logs", json={}, headers=auth_header(token))
    assert resp_put.status_code == 405

    resp_delete = client.delete("/api/audit/logs", headers=auth_header(token))
    assert resp_delete.status_code == 405


def test_audit_event_model_immutability():
    """AuditEvent Pydantic model is frozen and cannot be modified."""
    event = AuditEvent(
        event_id="test_evt_001",
        timestamp="2026-09-20T20:00:00Z",
        actor_user_id="usr_001",
        actor_username="test_user",
        actor_role="INVESTIGATING_OFFICER",
        event_type=AuditEventType.CASE_VIEW_DOSSIER,
        action="VIEW",
        target_type="CASE",
        target_id="CASE-001",
        status=AuditStatus.SUCCESS,
        status_code=200,
        request_path="/api/cases/CASE-001"
    )

    with pytest.raises(ValidationError):
        event.status = AuditStatus.FAILED  # Mutating frozen model must raise error


def test_audit_bounded_retention_window():
    """AuditLogRepository strictly respects its maximum sliding-window capacity."""
    small_repo = AuditLogRepository(max_capacity=5)

    for i in range(10):
        evt = AuditEvent(
            event_id=f"evt_{i}",
            timestamp="2026-09-20T20:00:00Z",
            actor_user_id="usr_001",
            actor_username="test",
            actor_role="INVESTIGATING_OFFICER",
            event_type=AuditEventType.CASE_VIEW_DOSSIER,
            action="VIEW",
            target_type="CASE",
            target_id=f"CASE-{i}",
            status=AuditStatus.SUCCESS,
            status_code=200,
            request_path="/api/cases"
        )
        small_repo.record_event(evt)

    assert small_repo.get_total_count() == 5
    # The oldest events 0..4 should have rolled off; remaining must be 5..9
    events = small_repo.query_logs(limit=10)
    event_ids = {e.event_id for e in events}
    assert event_ids == {"evt_5", "evt_6", "evt_7", "evt_8", "evt_9"}


def test_zero_credential_leakage(client, tokens):
    """
    Inspects all events recorded in the repository and verifies that no
    passwords, password hashes, or bearer tokens appear anywhere.
    """
    audit_repo = client.app.state.audit_repo
    all_events = audit_repo.query_logs(limit=500)

    for ev in all_events:
        json_repr = ev.model_dump_json()
        assert "password_hash" not in json_repr
        assert "pbkdf2" not in json_repr.lower()
        # Verify actual bearer session tokens are never stored
        for secret_token in tokens.values():
            assert secret_token not in json_repr
        # Verify plaintext passwords are never stored
        for secret_pwd in DEMO_CREDENTIALS.values():
            assert secret_pwd not in json_repr
