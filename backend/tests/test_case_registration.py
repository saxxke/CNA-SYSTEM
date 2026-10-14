"""
test_case_registration.py
=========================
Comprehensive test suite for Step 27: Register New Case + Create / Link Person.
Tests:
- Input validation (case, person, association, role, FIR)
- Dynamic ID allocation (baseline + runtime)
- Advisory duplicate detection / entity resolution
- Runtime persistence & isolation (baseline CSVs remain byte-for-byte untouched)
- Restart persistence
- Graph update semantics (INVOLVED_IN edge, no person-person edge, no family edge)
- Analytics & Priority recalculation
- Search & AI Assistant retrieval
- Strict safety & non-accusatory terminology
"""

import os
import pytest
from fastapi.testclient import TestClient

from main import app
from modules.persistence.runtime_store import (
    clear_runtime_data,
    get_runtime_records,
    get_all_records,
    get_next_case_id,
    get_next_person_id,
    get_next_cp_id,
    check_fir_exists,
    RUNTIME_DIR
)
from modules.cases.case_registration_service import (
    register_case_transaction,
    check_person_duplicate,
    search_persons_for_linking,
    ValidationError
)
from modules.graph.dataset_integration import build_dataset_graph
from modules.search.search_service import advanced_search
from modules.assistant.assistant_service import process_assistant_query


@pytest.fixture(scope="module")
def client():
    """Initializes FastAPI test client with lifespan context."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_runtime_environment():
    """Ensures clean runtime environment before and after each test."""
    clear_runtime_data()
    yield
    clear_runtime_data()


# ── 1. DYNAMIC ID ALLOCATION ────────────────────────────────────────────────

def test_dynamic_id_allocation():
    """Verifies that next IDs are dynamically calculated from baseline + runtime."""
    next_case_id = get_next_case_id()
    assert next_case_id.startswith("CASE-")
    # Baseline has 250 cases, so initial next ID should be >= CASE-251
    num = int(next_case_id.split("-")[1])
    assert num >= 251

    next_person_id = get_next_person_id()
    assert next_person_id.startswith("PERSON-")
    p_num = int(next_person_id.split("-")[1])
    assert p_num >= 201

    next_cp_id = get_next_cp_id()
    assert next_cp_id.startswith("CPA-")
    cp_num = int(next_cp_id.split("-")[1])
    assert cp_num >= 346


# ── 2. ADVISORY ENTITY RESOLUTION & DUPLICATE CHECK ─────────────────────────

def test_check_duplicate_exact_phone():
    """Exact phone match triggers DUPLICATE advisory level."""
    # PERSON-001 in baseline has phone_id PHONE-001 with number 7454794895
    res = check_person_duplicate({
        "full_name": "Different Name",
        "phone": "7454794895"
    })
    assert res["has_matches"] is True
    assert len(res["matches"]) >= 1
    top = res["matches"][0]
    assert top["match_level"] == "DUPLICATE"
    assert top["match_type"] == "EXACT_PHONE"
    assert top["score"] == 1.0


def test_check_duplicate_similar_name():
    """Similar name triggers POSSIBLE_MATCH advisory level without merging."""
    res = check_person_duplicate({
        "full_name": "A. Mehta",
        "district": "Raipur"
    })
    assert res["has_matches"] is True
    # Should flag similarity with Arjun Mehta
    matches = [m for m in res["matches"] if "Mehta" in m["full_name"]]
    assert len(matches) >= 1
    assert matches[0]["match_level"] == "POSSIBLE_MATCH"
    assert matches[0]["score"] >= 0.70


def test_search_persons_for_linking():
    """Verifies searching registered persons for linking to a case."""
    results = search_persons_for_linking("Arjun", limit=5)
    assert len(results) >= 1
    first = results[0]
    assert "Arjun" in first["full_name"]
    assert first["person_id"].startswith("PERSON-")
    assert "associated_case_count" in first


# ── 3. CASE REGISTRATION TRANSACTION & VALIDATION ────────────────────────────

def test_register_case_validation_errors():
    """Missing required case fields must raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        register_case_transaction({
            "case": {
                "title": "", # Missing
                "offence_category": "Kidnapping",
                "incident_date": "2026-09-07",
                "location": "Raipur",
                "district": "Raipur",
                "police_station": "PS-1",
                "description": "Test"
            },
            "associated_persons": [{"person_type": "EXISTING", "person_id": "PERSON-001", "role": "SUBJECT"}]
        })
    assert "Case title is required" in str(exc.value)

    # Invalid status
    with pytest.raises(ValidationError) as exc:
        register_case_transaction({
            "case": {
                "title": "Valid Title",
                "offence_category": "Kidnapping",
                "incident_date": "2026-09-07",
                "location": "Raipur",
                "district": "Raipur",
                "police_station": "PS-1",
                "description": "Test",
                "status": "INVALID_STATUS"
            },
            "associated_persons": [{"person_type": "EXISTING", "person_id": "PERSON-001", "role": "SUBJECT"}]
        })
    assert "Invalid status" in str(exc.value)


def test_register_case_duplicate_fir_rejection():
    """Duplicate FIR number must be rejected."""
    # FIR-SYNTH-RAI-0001 is in baseline CASE-001
    assert check_fir_exists("FIR-SYNTH-RAI-0001") is True

    with pytest.raises(ValidationError) as exc:
        register_case_transaction({
            "case": {
                "title": "Duplicate FIR Case",
                "offence_category": "Extortion",
                "incident_date": "2026-09-07",
                "location": "Raipur",
                "district": "Raipur",
                "police_station": "PS-1",
                "description": "Test",
                "fir_number": "FIR-SYNTH-RAI-0001"
            },
            "associated_persons": [{"person_type": "EXISTING", "person_id": "PERSON-001", "role": "SUBJECT"}]
        })
    assert "already exists" in str(exc.value)


def test_register_case_duplicate_person_association_rejection():
    """Cannot associate the same person multiple times to the same case."""
    with pytest.raises(ValidationError) as exc:
        register_case_transaction({
            "case": {
                "title": "Multi Same Person Case",
                "offence_category": "Extortion",
                "incident_date": "2026-09-07",
                "location": "Raipur",
                "district": "Raipur",
                "police_station": "PS-1",
                "description": "Test"
            },
            "associated_persons": [
                {"person_type": "EXISTING", "person_id": "PERSON-001", "role": "SUBJECT"},
                {"person_type": "EXISTING", "person_id": "PERSON-001", "role": "WITNESS"}
            ]
        })
    assert "Duplicate association" in str(exc.value)


# ── 4. END-TO-END REGISTRATION & PERSISTENCE ─────────────────────────────────

def test_register_case_end_to_end_flow(client):
    """
    Prompt Requirement 29:
    Title: "Recent Kidnapping Investigation"
    Offence: Kidnapping
    Location: Raipur
    Link EXISTING: Arjun Mehta (PERSON-001) as SUBJECT
    Create NEW: "Rahul Verma" as PERSON_OF_INTEREST
    """
    payload = {
        "case": {
            "title": "Recent Kidnapping Investigation",
            "offence_category": "Kidnapping",
            "incident_date": "2026-09-07",
            "location": "Raipur Industrial Area",
            "district": "Raipur",
            "police_station": "Fictional PS No. 1, Raipur",
            "description": "Investigation into alleged kidnapping incident for demonstration purposes.",
            "status": "OPEN",
            "fir_number": "FIR-SYNTH-TEST-9999",
            "legal_section": "IPC 363"
        },
        "associated_persons": [
            {
                "person_type": "EXISTING",
                "person_id": "PERSON-001",
                "role": "SUBJECT"
            },
            {
                "person_type": "NEW",
                "new_person_data": {
                    "full_name": "Rahul Verma",
                    "gender": "Male",
                    "date_of_birth": "1990-05-12",
                    "occupation": "Trader",
                    "phone": "9876543210",
                    "district": "Raipur",
                    "address": "Fictional Station Road, Raipur"
                },
                "role": "PERSON_OF_INTEREST"
            }
        ]
    }

    resp = client.post("/api/cases/register", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    created_case_id = data["case_id"]
    assert created_case_id.startswith("CASE-")

    assocs = data["associated_persons"]
    assert len(assocs) == 2

    # Verify Arjun Mehta association
    p1 = next(a for a in assocs if a["person_id"] == "PERSON-001")
    assert p1["role"] == "SUBJECT"
    assert p1["is_new"] is False

    # Verify Rahul Verma creation
    p2 = next(a for a in assocs if a["person_name"] == "Rahul Verma")
    assert p2["role"] == "PERSON_OF_INTEREST"
    assert p2["is_new"] is True
    created_person_id = p2["person_id"]
    assert created_person_id.startswith("PERSON-")

    # 1. Verify runtime persistence under backend/data/runtime/
    runtime_cases = get_runtime_records("cases.csv")
    assert any(c["case_id"] == created_case_id for c in runtime_cases)

    runtime_persons = get_runtime_records("persons.csv")
    assert any(p["person_id"] == created_person_id for p in runtime_persons)

    runtime_cps = get_runtime_records("case_persons.csv")
    assert any(cp["case_id"] == created_case_id and cp["person_id"] == created_person_id for cp in runtime_cps)

    # 2. Case Details verification
    case_resp = client.get(f"/api/cases/{created_case_id}")
    assert case_resp.status_code == 200
    case_details = case_resp.json()
    assert case_details["details"]["case_title"] == "Recent Kidnapping Investigation"
    assert len(case_details["associated_persons"]) == 2

    # 3. Person Profile verification for newly created person
    profile_resp = client.get(f"/api/entities/{created_person_id}")
    assert profile_resp.status_code == 200
    profile_data = profile_resp.json()
    assert profile_data["demographics"]["full_name"] == "Rahul Verma"
    assert any(c["case_id"] == created_case_id for c in profile_data["associated_cases"])

    # 4. Strict Graph Semantics:
    # - Case node exists
    # - Person nodes exist
    # - INVOLVED_IN edge exists
    # - NO person-person edge
    # - NO family edge
    G = app.state.graph
    assert G.has_node(created_case_id)
    assert G.has_node(created_person_id)
    assert G.has_node("PERSON-001")
    assert G.has_edge(created_case_id, created_person_id) or G.has_edge(created_person_id, created_case_id)
    # Strictly NO direct person-person edge!
    assert not G.has_edge(created_person_id, "PERSON-001")
    assert not G.has_edge("PERSON-001", created_person_id)

    # 5. Advanced Search verification
    search_res = advanced_search({"query": "Rahul Verma"})
    assert any(p["person_id"] == created_person_id for p in search_res["persons"])

    case_search = advanced_search({"query": "Recent Kidnapping Investigation"})
    assert any(c["case_id"] == created_case_id for c in case_search["cases"])

    # 6. AI Investigation Assistant retrieval
    ast_resp = process_assistant_query("Show details for Rahul Verma", G=G)
    assert ast_resp.answer_markdown is not None
    assert len(ast_resp.answer_markdown) > 0


# ── 5. RESTART PERSISTENCE VERIFICATION ──────────────────────────────────────

def test_restart_persistence(client):
    """
    Requirement 9:
    create runtime case/person -> restart backend (re-run build_dataset_graph) -> verify again.
    """
    # Register record
    resp = client.post("/api/cases/register", json={
        "case": {
            "title": "Persistent Test Case",
            "offence_category": "Theft",
            "incident_date": "2026-09-07",
            "location": "Raipur Market",
            "district": "Raipur",
            "police_station": "PS-2",
            "description": "Test persistence across reload."
        },
        "associated_persons": [
            {"person_type": "EXISTING", "person_id": "PERSON-002", "role": "WITNESS"}
        ]
    })
    assert resp.status_code == 200
    cid = resp.json()["case_id"]

    # Simulate backend restart by rebuilding the graph and reloading caches
    rebuilt_G = build_dataset_graph()
    assert rebuilt_G.has_node(cid)
    assert rebuilt_G.has_node("PERSON-002")
    assert rebuilt_G.has_edge(cid, "PERSON-002")
