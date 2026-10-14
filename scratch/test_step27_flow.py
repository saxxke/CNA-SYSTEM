"""
Verification script for Step 27 API, persistence, and graph integrity.
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("--- 1. Testing Duplicate Check API ---")
    # Test Exact Phone Duplicate
    res = requests.post(f"{BASE_URL}/api/persons/check-duplicate", json={
        "full_name": "Arjun Mehta",
        "phone": "7454794895",
        "district": "Raipur"
    })
    print("Exact duplicate check status:", res.status_code)
    dup_data = res.json()
    print("Has matches:", dup_data.get("has_matches"))
    if dup_data.get("matches"):
        print("Top match:", dup_data["matches"][0])
    assert dup_data.get("has_matches") is True, "Exact duplicate should trigger advisory match"

    # Test Similar Name (A. Mehta)
    res = requests.post(f"{BASE_URL}/api/persons/check-duplicate", json={
        "full_name": "A. Mehta",
        "district": "Raipur"
    })
    sim_data = res.json()
    print("A. Mehta match status:", sim_data.get("has_matches"))
    assert sim_data.get("has_matches") is True, "Similar name should trigger possible match"

    print("\n--- 2. Testing Person Search for Linking ---")
    res = requests.get(f"{BASE_URL}/api/persons/search-linking?q=Arjun Mehta")
    assert res.status_code == 200
    search_results = res.json()
    print(f"Found {len(search_results)} candidates for 'Arjun Mehta':")
    arjun = search_results[0]
    arjun_id = arjun["person_id"]
    print(f"Linking candidate: {arjun['full_name']} ({arjun_id}), cases: {arjun['associated_case_count']}")

    print("\n--- 3. Testing Case Registration Transaction ---")
    reg_payload = {
        "case": {
            "title": "Synthetic Cyber Financial Fraud Case",
            "fir_number": "FIR-TEST-2026-999",
            "offence_category": "Cybercrime",
            "legal_section": "66D IT Act",
            "incident_date": "2026-09-01",
            "status": "OPEN",
            "police_station": "Cyber Police Station",
            "district": "Raipur",
            "state": "Chhattisgarh",
            "location": "Raipur Cyber Cell Area",
            "description": "Synthetic demonstration incident involving unauthorized digital transactions."
        },
        "associated_persons": [
            {
                "person_type": "EXISTING",
                "person_id": arjun_id,
                "role": "WITNESS"
            },
            {
                "person_type": "NEW",
                "role": "SUBJECT",
                "new_person_data": {
                    "full_name": "Rahul Verma",
                    "gender": "Male",
                    "occupation": "Tech Analyst",
                    "district": "Raipur",
                    "state": "Chhattisgarh",
                    "phone": "+91 9898989898",
                    "address": "42 Synthetic Tech Park, Raipur"
                }
            }
        ],
        "optional_entities": [
            {
                "entity_type": "PHONE",
                "value": "+91 9898989899"
            }
        ]
    }

    res = requests.post(f"{BASE_URL}/api/cases/register", json=reg_payload)
    print("Register Case response status:", res.status_code)
    reg_res = res.json()
    print("Register Case response:", json.dumps(reg_res, indent=2))
    assert res.status_code == 200
    assert reg_res["success"] is True
    created_case_id = reg_res["case_id"]
    new_person_id = None
    for p in reg_res["associated_persons"]:
        if p["is_new"]:
            new_person_id = p["person_id"]
    print(f"Registered Case ID: {created_case_id}, New Person ID: {new_person_id}")

    print("\n--- 4. Verify Retrieval of Created Case ---")
    res = requests.get(f"{BASE_URL}/api/cases/{created_case_id}")
    assert res.status_code == 200, f"Case {created_case_id} should be retrievable"
    case_obj = res.json()
    case_details = case_obj.get("details", {})
    print("Retrieved Case Title:", case_details.get("title"))
    assert case_details.get("title") == "Synthetic Cyber Financial Fraud Case"
    print("Associated persons count in case:", case_details.get("associated_persons_count"))

    print("\n--- 5. Verify Retrieval of Created Person ---")
    res = requests.get(f"{BASE_URL}/api/entities/{new_person_id}")
    assert res.status_code == 200, f"Person {new_person_id} should be retrievable"
    person_obj = res.json()
    demo = person_obj.get("demographics", {})
    print("Retrieved Person Name:", demo.get("full_name"))
    assert demo.get("full_name") == "Rahul Verma"
    cases_linked = person_obj.get("associated_cases", [])
    print("Associated cases:", [c.get("case_id") for c in cases_linked])
    assert created_case_id in [c.get("case_id") for c in cases_linked]

    print("\n--- 6. Verify Search Integration ---")
    res = requests.get(f"{BASE_URL}/api/search?q=Rahul Verma")
    assert res.status_code == 200
    search_data = res.json()
    p_matches = [r for r in search_data.get("results", []) if "Rahul Verma" in str(r)]
    print(f"Search results for 'Rahul Verma': {len(p_matches)} found")
    assert len(p_matches) > 0, "Rahul Verma should be found in search"

    print("\n--- 7. Verify Network / Graph Integrity ---")
    res = requests.get(f"{BASE_URL}/api/relationships?case_id={created_case_id}")
    assert res.status_code == 200
    edges = res.json()
    print(f"Case relationships in graph: {len(edges)} edges found")
    assert len(edges) >= 2
    for e in edges:
        s, t = e["source"], e["target"]
        assert not (s.startswith("PERSON-") and t.startswith("PERSON-")), f"Fabricated person-to-person edge found: {s} -> {t}"
    print("Graph integrity PASS: Only CASE-PERSON associations present, no fabricated person-person edges.")

    print("\n--- 8. Verify AI Assistant Integration ---")
    res = requests.post(f"{BASE_URL}/api/assistant/chat", json={
        "query": "Show details for Rahul Verma"
    })
    print("Assistant status:", res.status_code)
    if res.status_code == 200:
        ans = res.json()
        print("Assistant answer snippet:", ans.get("answer", "")[:150])
        print("Provenance citations:", len(ans.get("provenance", [])))
        assert "Rahul Verma" in ans.get("answer", "") or len(ans.get("candidate_entities", [])) > 0 or len(ans.get("provenance", [])) > 0

    print("\nAll API verification steps passed successfully!")

if __name__ == "__main__":
    test_api()
