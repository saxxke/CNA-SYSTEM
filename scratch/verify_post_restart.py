"""
Verify Step 27 runtime data after backend restart.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# Wait for server ready
for _ in range(15):
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if r.status_code == 200:
            break
    except Exception:
        time.sleep(1)

print("Backend is alive. Testing post-restart persistence...")

# 1. GET /api/cases/CASE-251
r = requests.get(f"{BASE_URL}/api/cases/CASE-251")
print("1. GET /api/cases/CASE-251 status:", r.status_code)
assert r.status_code == 200, "CASE-251 should persist after restart"
case_data = r.json()
print("   Title:", case_data.get("details", {}).get("title"))
print("   FIR:", case_data.get("details", {}).get("fir_number"))

# 2. GET /api/entities/PERSON-201
r = requests.get(f"{BASE_URL}/api/entities/PERSON-201")
print("2. GET /api/entities/PERSON-201 status:", r.status_code)
assert r.status_code == 200, "PERSON-201 should persist after restart"
person_data = r.json()
print("   Name:", person_data.get("demographics", {}).get("full_name"))
print("   Occupation:", person_data.get("demographics", {}).get("occupation"))

# 3. GET /api/cases list contains CASE-251
r = requests.get(f"{BASE_URL}/api/cases")
print("3. GET /api/cases status:", r.status_code)
assert r.status_code == 200
cases = r.json()
c_ids = [c.get("id") or c.get("case_id") or c.get("details", {}).get("case_id") for c in cases]
print(f"   Total cases: {len(cases)}, CASE-251 in list: {'CASE-251' in c_ids}")
assert "CASE-251" in c_ids, "CASE-251 must appear in cases list"

# 4. GET /api/persons list contains PERSON-201
r = requests.get(f"{BASE_URL}/api/persons")
print("4. GET /api/persons status:", r.status_code)
assert r.status_code == 200
persons_list = r.json()
p_ids = [p.get("person_id") for p in persons_list]
print(f"   Total persons: {len(persons_list)}, PERSON-201 in list: {'PERSON-201' in p_ids}")
assert "PERSON-201" in p_ids, "PERSON-201 must appear in persons list"

# 5. Search Integration
r = requests.get(f"{BASE_URL}/api/search?q=Rahul%20Verma")
print("5. Search status:", r.status_code)
assert r.status_code == 200
s_res = r.json()
p_matches = [res for res in s_res.get("results", []) if "Rahul Verma" in str(res)]
print(f"   Matches for 'Rahul Verma': {len(p_matches)}")
assert len(p_matches) > 0, "Rahul Verma must be searchable"

# 6. Graph Relationships
r = requests.get(f"{BASE_URL}/api/relationships?case_id=CASE-251")
print("6. Relationships status:", r.status_code)
assert r.status_code == 200
edges = r.json()
print(f"   Edges for CASE-251: {len(edges)}")
assert len(edges) >= 2, "Graph must have CASE-251 associations"

# 7. Analytics & Priority
r = requests.get(f"{BASE_URL}/api/analytics")
print("7. Analytics status:", r.status_code)
assert r.status_code == 200

r = requests.get(f"{BASE_URL}/api/priority?limit=10")
print("8. Priority status:", r.status_code)
assert r.status_code == 200

# 8. AI Assistant
r = requests.post(f"{BASE_URL}/api/assistant/query", json={"question": "Show details for Rahul Verma"})
print("9. AI Assistant status:", r.status_code)
assert r.status_code == 200
ans_data = r.json()
print("   Answer snippet:", ans_data.get("answer", "")[:120])
print("   Provenance items:", len(ans_data.get("provenance", [])))
print("   Entity cards:", len(ans_data.get("entity_cards", [])))

print("\n>>> ALL POST-RESTART PERSISTENCE CHECKS PASSED PERFECTLY! <<<")
