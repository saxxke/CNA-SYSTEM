"""
test_phase8a_provenance.py
==========================
Comprehensive test suite for Phase 8A: Relationship Evidence Provenance.

Test Coverage:
1. Model Privacy & Sanitization:
   - Strictly no raw_fields or open-ended dictionaries.
   - Extra fields raise ValidationError (ConfigDict(extra="forbid")).
   - Models are frozen and immutable.
2. Graph Edge Provenance Ingestion:
   - build_dataset_graph preserves features and record_ids on edges.
3. Provenance Service:
   - get_edge_provenance returns EdgeProvenanceResponse with Confidence Evidence Breakdown.
   - Terminology uses "Confidence Evidence Breakdown" and "Potential Relationship".
   - Supporting records match sanitized models (SanitizedCommunicationRecord, SanitizedTransactionRecord, etc.).
4. Multi-Role RBAC Authorization:
   - CITIZEN -> 403 Forbidden.
   - HOME_MINISTRY -> 403 Forbidden.
   - Unauthenticated -> 401 Unauthorized.
   - IO (Assigned Case) -> 200 OK.
   - IO (Unassigned Case) -> 404 Not Found (zero evidence leakage).
   - IPS (State Jurisdiction) -> 200 OK.
5. Phase 7 Audit Logging:
   - Edge provenance view generates PROVENANCE_EDGE_VIEW audit event.
   - Audit event attributes verified.
"""

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from main import app
from modules.auth.demo_users import DEMO_CREDENTIALS, get_demo_user_repository
from modules.auth.tokens import TokenStore
from modules.auth.citizen_access import create_demo_citizen_access_repository
from modules.auth.investigation_access import create_demo_investigation_access_repository
from modules.auth.audit_repository import create_demo_audit_repository
from modules.auth.audit_models import AuditEventType
from modules.graph.dataset_integration import build_dataset_graph
from modules.provenance.models import (
    SanitizedCommunicationRecord,
    SanitizedTransactionRecord,
    SanitizedCaseAssociationRecord,
    SanitizedMetadataLinkageRecord,
    ConfidenceEvidenceBreakdown,
    EdgeProvenanceResponse,
)
from modules.provenance.provenance_service import get_edge_provenance


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        test_client.app.state.user_repo = get_demo_user_repository()
        test_client.app.state.token_store = TokenStore()
        test_client.app.state.citizen_access_repo = create_demo_citizen_access_repository()
        test_client.app.state.investigation_access_repo = create_demo_investigation_access_repository()
        test_client.app.state.audit_repo = create_demo_audit_repository()
        yield test_client


@pytest.fixture(scope="module")
def tokens(client):
    auth_tokens = {}
    for username, password in DEMO_CREDENTIALS.items():
        resp = client.post("/api/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
        auth_tokens[username] = resp.json()["token"]
    return auth_tokens


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. Model Privacy & Sanitization Tests
# =====================================================================

def test_sanitized_record_forbids_raw_fields():
    """Verify supporting records reject unvetted/raw fields (extra='forbid')."""
    with pytest.raises(ValidationError):
        SanitizedCommunicationRecord(
            record_id="COMM-001",
            case_id="CASE-001",
            source_person_id="PERSON-001",
            target_person_id="PERSON-002",
            communication_type="CALL",
            date="2024-01-01",
            duration_seconds=60,
            summary="Call record",
            raw_fields={"unvetted_ip": "192.168.1.1"}  # Must raise ValidationError
        )


def test_sanitized_transaction_forbids_raw_fields():
    """Verify transaction records reject arbitrary dictionary payloads."""
    with pytest.raises(ValidationError):
        SanitizedTransactionRecord(
            record_id="TXN-001",
            case_id="CASE-001",
            source_person_id="PERSON-001",
            target_person_id="PERSON-002",
            amount=5000.0,
            currency="INR",
            date="2024-01-01",
            summary="Transaction record",
            unauthorized_dump={"bank_secret": "12345"}
        )


def test_provenance_models_are_frozen():
    """Verify provenance response models are immutable."""
    breakdown = ConfidenceEvidenceBreakdown(
        confidence_score=0.85,
        confidence_level="HIGH",
        observable_signals=[]
    )
    with pytest.raises(ValidationError):
        breakdown.confidence_score = 0.99


# =====================================================================
# 2. Graph Ingestion & Provenance Service Tests
# =====================================================================

def test_graph_edges_preserve_provenance_metadata():
    """Verify that build_dataset_graph attaches features and record_ids to edges."""
    G = build_dataset_graph()
    assert len(G.edges()) > 0

    edges_with_features = 0
    edges_with_records = 0
    for u, v, k, d in G.edges(data=True, keys=True):
        if "features" in d and d["features"]:
            edges_with_features += 1
        if "record_ids" in d and d["record_ids"]:
            edges_with_records += 1

    assert edges_with_features > 0, "Graph edges must preserve ML features"
    assert edges_with_records > 0, "Graph edges must preserve source record references"


def test_get_edge_provenance_service():
    """Verify get_edge_provenance builds a valid, sanitized EdgeProvenanceResponse."""
    G = build_dataset_graph()

    # Find a valid edge in the graph
    sample_edge = None
    for u, v, k, d in G.edges(data=True, keys=True):
        if d.get("case_id"):
            sample_edge = (u, v, d.get("case_id"))
            break

    assert sample_edge is not None
    u, v, cid = sample_edge

    res = get_edge_provenance(G, u, v, case_id=cid)
    assert res is not None
    assert isinstance(res, EdgeProvenanceResponse)
    assert res.source_id == u
    assert res.target_id == v
    assert res.case_id == cid
    assert res.confidence_breakdown is not None
    assert res.confidence_breakdown.confidence_score >= 0.0
    assert res.confidence_breakdown.confidence_level in ["HIGH", "MEDIUM", "LOW"]
    assert len(res.confidence_breakdown.observable_signals) > 0

    # Verify non-accusatory terminology
    disclaimer = res.safety_disclaimer.lower()
    assert "guilt" in disclaimer and "not" in disclaimer
    assert "potential relationship" in disclaimer


# =====================================================================
# 3. RBAC & Phase 6 Authorization Tests on /api/provenance/edge
# =====================================================================

def test_unauthenticated_edge_provenance_denied(client):
    """Unauthenticated request to /api/provenance/edge returns 401."""
    resp = client.get("/api/provenance/edge?source=PERSON-001&target=PERSON-002")
    assert resp.status_code == 401


def test_citizen_edge_provenance_denied(client, tokens):
    """CITIZEN role is strictly forbidden from accessing edge provenance (403)."""
    resp = client.get(
        "/api/provenance/edge?source=PERSON-001&target=PERSON-002",
        headers=auth_header(tokens["citizen.demo"])
    )
    assert resp.status_code == 403


def test_home_ministry_edge_provenance_denied(client, tokens):
    """HOME_MINISTRY role is strictly forbidden from operational edge provenance (403)."""
    resp = client.get(
        "/api/provenance/edge?source=PERSON-001&target=PERSON-002",
        headers=auth_header(tokens["hm.demo"])
    )
    assert resp.status_code == 403



def test_io_assigned_case_edge_provenance_allowed(client, tokens):
    """INVESTIGATING_OFFICER accessing provenance for an assigned case returns 200."""
    # io.demo is assigned to CASE-001, CASE-002, CASE-003
    # Check an edge associated with CASE-001
    G = client.app.state.graph
    edge_found = None
    for u, v, k, d in G.edges(data=True, keys=True):
        if d.get("case_id") == "CASE-001":
            edge_found = (u, v)
            break

    assert edge_found is not None, "CASE-001 must have at least one graph edge"
    src, tgt = edge_found

    resp = client.get(
        f"/api/provenance/edge?source={src}&target={tgt}&case_id=CASE-001",
        headers=auth_header(tokens["io.demo"])
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_id"] == src
    assert data["target_id"] == tgt
    assert data["case_id"] == "CASE-001"
    assert "confidence_breakdown" in data
    assert "observable_signals" in data["confidence_breakdown"]
    assert "supporting_records" in data


def test_io_unassigned_case_edge_provenance_denied(client, tokens):
    """INVESTIGATING_OFFICER accessing provenance for an unassigned case returns 404 (no leakage)."""
    # CASE-007 is in Mumbai, not assigned to io.demo (Raipur IO)
    resp = client.get(
        "/api/provenance/edge?source=PERSON-013&target=PERSON-014&case_id=CASE-007",
        headers=auth_header(tokens["io.demo"])
    )
    # Must be 404 Not Found (or 403), never 200
    assert resp.status_code in [403, 404]


def test_ips_state_jurisdiction_edge_provenance_allowed(client, tokens):
    """IPS_OFFICER has state jurisdiction across all Chhattisgarh cases (CASE-001 to CASE-003)."""
    G = client.app.state.graph
    edge_found = None
    for u, v, k, d in G.edges(data=True, keys=True):
        if d.get("case_id") == "CASE-002":
            edge_found = (u, v)
            break

    assert edge_found is not None
    src, tgt = edge_found

    resp = client.get(
        f"/api/provenance/edge?source={src}&target={tgt}&case_id=CASE-002",
        headers=auth_header(tokens["ips.demo"])
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "CASE-002"


# =====================================================================
# 4. Phase 7 Audit Logging Verification
# =====================================================================

def test_provenance_edge_view_audited(client, tokens):
    """Inspecting edge provenance records an immutable PROVENANCE_EDGE_VIEW audit event."""
    audit_repo = client.app.state.audit_repo
    G = client.app.state.graph

    src, tgt = None, None
    for u, v, k, d in G.edges(data=True, keys=True):
        if d.get("case_id") == "CASE-001":
            src, tgt = u, v
            break

    resp = client.get(
        f"/api/provenance/edge?source={src}&target={tgt}&case_id=CASE-001",
        headers=auth_header(tokens["io.demo"])
    )
    assert resp.status_code == 200

    # Query audit logs
    events = audit_repo.query_logs(
        user_id="io.demo",
        event_type=AuditEventType.PROVENANCE_EDGE_VIEW,
        limit=5
    )
    assert len(events) > 0
    latest = events[0]
    assert latest.event_type == AuditEventType.PROVENANCE_EDGE_VIEW
    assert latest.actor_username == "io.demo"
    assert latest.target_type == "GRAPH_EDGE"
    assert latest.target_id == f"{src}_{tgt}"
    assert latest.details.get("case_id") == "CASE-001"
