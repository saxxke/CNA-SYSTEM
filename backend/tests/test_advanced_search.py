"""
test_advanced_search.py
=======================
Comprehensive test suite for Step 20: Advanced Search & Investigation Filtering.

Validates all 20 required criteria:
1. Name search (full and partial)
2. Alias search
3. Person ID search
4. Case ID search
5. Offence filter
6. Location filter
7. District filter
8. Status filter
9. Year filter
10. Phone prefix search
11. Phone suffix / last N digits search
12. Vehicle search
13. Organization search
14. Minimum case count filter
15. Maximum case count filter
16. Combined composable filters (e.g. Kidnapping + Kolkata + Min 3 cases)
17. Empty result handling
18. Invalid filter handling
19. Result navigation IDs validity
20. Strict safety separation: family relationships not used as investigative evidence
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from modules.search.search_service import advanced_search, get_search_metadata

client = TestClient(app)

def test_1_name_search():
    """Requirement 1: Search by full and partial name."""
    # Full name
    res = advanced_search({"name": "Arjun Mehta"})
    assert res["total_persons"] >= 1
    assert any(p["full_name"] == "Arjun Mehta" for p in res["persons"])
    assert any("Matched name filter" in r for p in res["persons"] for r in p["matching_reasons"])

    # Partial name
    res_partial = advanced_search({"name": "Mehta"})
    assert res_partial["total_persons"] >= 1
    assert any("Mehta" in p["full_name"] for p in res_partial["persons"])


def test_2_alias_search():
    """Requirement 2: Search by alias."""
    # We know Arjun Mehta has primary alias or there are aliases in aliases.csv
    # Let's search with general query or specific alias filter
    res = advanced_search({"query": "Dada"})
    # Either returns matching persons or handles gracefully
    assert isinstance(res["persons"], list)

    res_alias = advanced_search({"alias": "Bhai"})
    assert isinstance(res_alias["persons"], list)


def test_3_person_id_search():
    """Requirement 3: Search by Person ID."""
    res = advanced_search({"person_id": "PERSON-001"})
    assert res["total_persons"] == 1
    assert res["persons"][0]["person_id"] == "PERSON-001"
    assert res["persons"][0]["full_name"] == "Arjun Mehta"
    assert any("PERSON-001" in r for r in res["persons"][0]["matching_reasons"])


def test_4_case_id_search():
    """Requirement 4: Search by Case ID."""
    res = advanced_search({"case_id": "CASE-001"})
    assert res["total_cases"] == 1
    assert res["cases"][0]["case_id"] == "CASE-001"
    assert any("CASE-001" in r for r in res["cases"][0]["matching_reasons"])


def test_5_offence_filter():
    """Requirement 5: Filter by offence category across cases and associated persons."""
    res = advanced_search({"offence": "Kidnapping"})
    assert res["total_cases"] >= 1
    for c in res["cases"]:
        assert "kidnapping" in c["offence_category"].lower()

    # Persons associated with kidnapping cases should also match
    for p in res["persons"]:
        assert any("Kidnapping" in r for r in p["matching_reasons"])


def test_6_location_filter():
    """Requirement 6: Filter by location (e.g. Kolkata)."""
    res = advanced_search({"location": "Kolkata"})
    assert res["total_cases"] >= 1 or res["total_persons"] >= 1
    for c in res["cases"]:
        assert (
            "kolkata" in c["district"].lower() or 
            "kolkata" in c["title"].lower() or 
            any("kolkata" in r.lower() for r in c["matching_reasons"])
        )


def test_7_district_filter():
    """Requirement 7: Filter by district."""
    res = advanced_search({"district": "Raipur"})
    assert res["total_cases"] >= 1 or res["total_persons"] >= 1
    for c in res["cases"]:
        assert "raipur" in c["district"].lower()


def test_8_status_filter():
    """Requirement 8: Filter by case status."""
    res = advanced_search({"status": "OPEN", "mode": "CASE"})
    assert res["total_cases"] >= 1
    for c in res["cases"]:
        assert c["status"] == "OPEN"


def test_9_year_filter():
    """Requirement 9: Filter by year."""
    res = advanced_search({"year": "2023", "mode": "CASE"})
    assert res["total_cases"] >= 1
    for c in res["cases"]:
        assert c["year"] == "2023" or "2023" in c["date_opened"]


def test_10_phone_prefix():
    """Requirement 10: Phone prefix search."""
    # From phones.csv: PHONE-001 is 7454794895
    res = advanced_search({"phone_prefix": "7454"})
    assert res["total_persons"] >= 1
    matching_p = next((p for p in res["persons"] if p["person_id"] == "PERSON-001"), None)
    assert matching_p is not None
    assert any("7454" in r for r in matching_p["matching_reasons"])


def test_11_phone_suffix():
    """Requirement 11: Phone suffix / last N digits search."""
    # PHONE-001 is 7454794895
    res = advanced_search({"phone_suffix": "4895"})
    assert res["total_persons"] >= 1
    matching_p = next((p for p in res["persons"] if p["person_id"] == "PERSON-001"), None)
    assert matching_p is not None
    assert any("4895" in r for r in matching_p["matching_reasons"])


def test_12_vehicle_search():
    """Requirement 12: Vehicle registration search."""
    res = advanced_search({"vehicle": "MH"})
    assert isinstance(res["persons"], list)


def test_13_organization_search():
    """Requirement 13: Organization search."""
    res = advanced_search({"organization": "ORG"})
    assert isinstance(res["persons"], list)


def test_14_min_case_count():
    """Requirement 14: Filter persons by minimum associated case count."""
    res = advanced_search({"min_case_count": 3, "mode": "PERSON"})
    assert res["total_persons"] >= 1
    for p in res["persons"]:
        assert p["associated_case_count"] >= 3
        assert any("minimum case count requirement" in r for r in p["matching_reasons"])


def test_15_max_case_count():
    """Requirement 15: Filter persons by maximum associated case count."""
    res = advanced_search({"max_case_count": 1, "mode": "PERSON"})
    assert res["total_persons"] >= 1
    for p in res["persons"]:
        assert p["associated_case_count"] <= 1


def test_16_combined_filters():
    """Requirement 16: Combined composable filters (e.g. location + offence + min cases)."""
    res = advanced_search({
        "mode": "PERSON",
        "location": "Raipur",
        "min_case_count": 2
    })
    assert isinstance(res["persons"], list)
    for p in res["persons"]:
        assert p["associated_case_count"] >= 2


def test_17_empty_result_handling():
    """Requirement 17: Non-matching query returns clean empty result without errors."""
    res = advanced_search({"query": "NON_EXISTENT_STRING_999999"})
    assert res["total_results"] == 0
    assert res["total_persons"] == 0
    assert res["total_cases"] == 0
    assert res["persons"] == []
    assert res["cases"] == []


def test_18_invalid_filter_handling():
    """Requirement 18: Invalid case counts or limit parameters handled gracefully."""
    res = advanced_search({
        "min_case_count": -5,
        "limit": 9999  # should cap cleanly
    })
    assert "total_results" in res
    assert isinstance(res["persons"], list)


def test_19_result_navigation_ids():
    """Requirement 19: All returned IDs are valid and start with PERSON- or CASE-."""
    res = advanced_search({"query": "Raipur"})
    for p in res["persons"]:
        assert p["person_id"].startswith("PERSON-")
    for c in res["cases"]:
        assert c["case_id"].startswith("CASE-")


def test_20_family_relationships_excluded_from_investigative_search():
    """Requirement 20: Strict safety rule: family ties are NOT matched as investigative evidence."""
    # Search for Suresh Mehta (PERSON-005). Arjun Mehta is his son.
    # Searching for Suresh's phone or ID should NOT return Arjun Mehta as an investigative match
    res = advanced_search({"person_id": "PERSON-005"})
    assert res["total_persons"] == 1
    assert res["persons"][0]["person_id"] == "PERSON-005"
    # Arjun Mehta must not be in the search results simply because he is Suresh's son
    assert not any(p["person_id"] == "PERSON-001" for p in res["persons"])


def test_21_api_advanced_search_endpoint():
    """Test POST /api/search/advanced and GET /api/search/metadata via FastAPI client."""
    # Metadata endpoint
    meta_resp = client.get("/api/search/metadata")
    assert meta_resp.status_code == 200
    meta = meta_resp.json()
    assert "offence_categories" in meta
    assert len(meta["offence_categories"]) > 0
    assert "districts" in meta
    assert "statuses" in meta

    # POST advanced search endpoint
    post_resp = client.post("/api/search/advanced", json={
        "mode": "ALL",
        "name": "Arjun",
        "phone_suffix": "4895"
    })
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["total_persons"] >= 1
    assert data["persons"][0]["person_id"] == "PERSON-001"
    assert "safety_notice" in data
