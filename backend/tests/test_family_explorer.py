"""
test_family_explorer.py
=======================
Unit & Integration Tests for Step 19: Family & Relationship Explorer.

Validates all 12 requirements:
1. Person with family relationships (e.g. PERSON-001)
2. Person with no family relationships
3. Father/child direction (PERSON-001 -> PERSON-005 = FATHER, PERSON-005 -> PERSON-001 = CHILD)
4. Mother/child direction
5. Spouse relationship (e.g. PERSON-002 <-> PERSON-003)
6. Sibling relationship (e.g. PERSON-006 <-> PERSON-010)
7. Reciprocal relationships (validation flag without inventing missing data)
8. Related-person navigation integrity
9. Family data does NOT enter investigative relationships / graph edges
10. Family data does NOT affect priority scoring
11. Missing optional family fields handled gracefully
12. API response structure and 404 for invalid entities
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from modules.entities.person_service import get_person_family_profile, get_person_profile
from modules.priority.priority_scorer import calculate_priority_scores
from modules.graph.dataset_integration import build_dataset_graph
from modules.analytics.graph_analytics import analyze_graph

client = TestClient(app)

def test_1_person_with_family_relationships():
    """Requirement 1: Person with family relationships returns valid structured record."""
    data = get_person_family_profile("PERSON-001")
    assert data is not None
    assert data["person_id"] == "PERSON-001"
    assert data["person_name"] == "Arjun Mehta"
    assert data["family_relationships_count"] >= 1
    assert len(data["family_relationships"]) == data["family_relationships_count"]
    assert "mandatory_safety_notice" in data
    assert "criminality" in data["mandatory_safety_notice"].lower()


def test_2_person_with_no_family_relationships():
    """Requirement 2: Person with no family relationships returns empty list gracefully."""
    # Find a person without family relationships in the 200 persons
    found_id = None
    for i in range(1, 201):
        pid = f"PERSON-{i:03d}"
        profile = get_person_family_profile(pid)
        if profile and profile["family_relationships_count"] == 0:
            found_id = pid
            break

    assert found_id is not None, "Expected at least one person with no registered family in synthetic dataset"
    data = get_person_family_profile(found_id)
    assert data["family_relationships_count"] == 0
    assert data["family_relationships"] == []
    assert data["counts_by_type"]["father"] == 0
    assert data["counts_by_type"]["spouse"] == 0


def test_3_father_child_direction():
    """
    Requirement 3: Verify exact father/child direction.
    PERSON-001 -> Father -> PERSON-005 (Suresh Mehta is the FATHER of Arjun Mehta)
    PERSON-005 -> Child -> PERSON-001 (Arjun Mehta is the CHILD of Suresh Mehta)
    """
    p1_fam = get_person_family_profile("PERSON-001")
    p5_fam = get_person_family_profile("PERSON-005")

    # In PERSON-001 profile
    p1_rel = next((r for r in p1_fam["family_relationships"] if r["related_person_id"] == "PERSON-005"), None)
    assert p1_rel is not None
    assert p1_rel["relationship_subtype"] == "FATHER"
    assert "Suresh Mehta is the FATHER of Arjun Mehta" in p1_rel["relation_to_subject"]
    assert p1_rel["reciprocal_status"]["is_verified"] is True
    assert p1_rel["reciprocal_status"]["reciprocal_subtype"] == "CHILD"

    # In PERSON-005 profile
    p5_rel = next((r for r in p5_fam["family_relationships"] if r["related_person_id"] == "PERSON-001"), None)
    assert p5_rel is not None
    assert p5_rel["relationship_subtype"] == "CHILD"
    assert "Arjun Mehta is the CHILD of Suresh Mehta" in p5_rel["relation_to_subject"]
    assert p5_rel["reciprocal_status"]["is_verified"] is True
    assert p5_rel["reciprocal_status"]["reciprocal_subtype"] == "FATHER"


def test_4_mother_child_direction():
    """Requirement 4: Verify mother/child direction."""
    # From families.csv: FAM-028: PERSON-145 -> PERSON-192, MOTHER
    p145_fam = get_person_family_profile("PERSON-145")
    assert p145_fam is not None
    m_rel = next((r for r in p145_fam["family_relationships"] if r["related_person_id"] == "PERSON-192"), None)
    assert m_rel is not None
    assert m_rel["relationship_subtype"] == "MOTHER"
    assert "MOTHER" in m_rel["relation_to_subject"]


def test_5_spouse_relationship():
    """Requirement 5: Verify spouse reciprocal relationships (PERSON-002 <-> PERSON-003)."""
    p2_fam = get_person_family_profile("PERSON-002")
    p3_fam = get_person_family_profile("PERSON-003")

    p2_rel = next((r for r in p2_fam["family_relationships"] if r["related_person_id"] == "PERSON-003"), None)
    p3_rel = next((r for r in p3_fam["family_relationships"] if r["related_person_id"] == "PERSON-002"), None)

    assert p2_rel is not None
    assert p3_rel is not None
    assert p2_rel["relationship_subtype"] == "SPOUSE"
    assert p3_rel["relationship_subtype"] == "SPOUSE"
    assert p2_rel["reciprocal_status"]["is_verified"] is True
    assert p3_rel["reciprocal_status"]["is_verified"] is True


def test_6_sibling_relationship():
    """Requirement 6: Verify sibling relationships (PERSON-006 <-> PERSON-010)."""
    p6_fam = get_person_family_profile("PERSON-006")
    p10_fam = get_person_family_profile("PERSON-010")

    p6_rel = next((r for r in p6_fam["family_relationships"] if r["related_person_id"] == "PERSON-010"), None)
    p10_rel = next((r for r in p10_fam["family_relationships"] if r["related_person_id"] == "PERSON-006"), None)

    assert p6_rel is not None
    assert p10_rel is not None
    assert p6_rel["relationship_subtype"] == "BROTHER"
    assert p10_rel["relationship_subtype"] == "BROTHER"
    assert p6_rel["reciprocal_status"]["is_verified"] is True
    assert p10_rel["reciprocal_status"]["is_verified"] is True


def test_7_reciprocal_relationships_validation_without_fabrication():
    """Requirement 7: Verify reciprocal status tracking without fabricating missing links."""
    # PERSON-145 has multiple family ties, some may be one-way source records
    p_fam = get_person_family_profile("PERSON-145")
    assert p_fam is not None
    for r in p_fam["family_relationships"]:
        assert "is_verified" in r["reciprocal_status"]
        assert "description" in r["reciprocal_status"]
        # If not verified, ensure it is clearly identified as source-recorded only
        if not r["reciprocal_status"]["is_verified"]:
            assert "source-recorded" in r["reciprocal_status"]["description"].lower()


def test_8_related_person_navigation_integrity():
    """Requirement 8: Navigating to related person's family profile returns their reciprocal view."""
    # From PERSON-001 -> PERSON-005, then inspect PERSON-005
    p1 = get_person_family_profile("PERSON-001")
    target_id = p1["family_relationships"][0]["related_person_id"]
    p_target = get_person_family_profile(target_id)
    assert p_target is not None
    # Ensure PERSON-001 is in p_target's family
    reciprocal = next((r for r in p_target["family_relationships"] if r["related_person_id"] == "PERSON-001"), None)
    assert reciprocal is not None


def test_9_family_data_does_not_enter_investigative_graph():
    """Requirement 9: Strict Safety Separation: Family relationships MUST NOT appear as graph edges."""
    G = build_dataset_graph()
    
    # Check that no edge in G has a family relationship type
    FAMILY_TYPES = {"FATHER", "MOTHER", "SPOUSE", "CHILD", "SON", "DAUGHTER", "BROTHER", "SISTER", "FAMILY"}
    for u, v, k, data in G.edges(keys=True, data=True):
        rel_type = data.get("relationship_type", "").upper()
        assert rel_type not in FAMILY_TYPES, f"Found prohibited family relationship type in investigative graph: {rel_type}"


import re

def test_10_family_data_does_not_affect_priority_scoring():
    """Requirement 10: Strict Safety Separation: Family data must not be an input to priority scoring."""
    G = build_dataset_graph()
    analytics = analyze_graph(G)
    priorities = calculate_priority_scores(G, analytics)

    # Word boundary regex to avoid matching substrings in 'case_persons.csv'
    FORBIDDEN_TERMS = [r"\bfather\b", r"\bmother\b", r"\bspouse\b", r"\bbrother\b", r"\bsister\b", r"\bchild\b", r"\bson\b", r"\bdaughter\b"]

    for p in priorities:
        # None of the reasons or supporting evidence should refer to family ties
        reasons_text = " ".join(p.get("reasons", [])).lower()
        evidence_text = " ".join(p.get("supporting_evidence", [])).lower()
        for term in FORBIDDEN_TERMS:
            assert not re.search(term, reasons_text), f"Forbidden family reference found in priority reasons: {term}"
            assert not re.search(term, evidence_text), f"Forbidden family reference found in priority evidence: {term}"


def test_11_missing_optional_family_fields_handled_gracefully():
    """Requirement 11: Missing fields such as age, occupation, or locality are handled cleanly."""
    for i in range(1, 201):
        pid = f"PERSON-{i:03d}"
        profile = get_person_family_profile(pid)
        if profile and profile["family_relationships"]:
            for m in profile["family_relationships"]:
                assert "related_person_id" in m
                assert "related_person_name" in m
                assert "relationship_subtype" in m
                assert "relation_to_subject" in m
                # Optional fields are strings (never crash or None)
                assert isinstance(m.get("age", ""), (str, int))
                assert isinstance(m.get("occupation", ""), str)
                assert isinstance(m.get("city", ""), str)


def test_12_api_family_endpoint_and_404():
    """Requirement 12: API endpoint GET /api/entities/{entity_id}/family returns 200 or 404."""
    # Valid person
    resp = client.get("/api/entities/PERSON-001/family")
    assert resp.status_code == 200
    data = resp.json()
    assert data["person_id"] == "PERSON-001"
    assert "grouped_family" in data
    assert "counts_by_type" in data
    assert "separate_investigative_context" in data
    assert "mandatory_safety_notice" in data

    # Invalid person / non-person
    resp_404 = client.get("/api/entities/NON-EXISTENT-999/family")
    assert resp_404.status_code == 404
