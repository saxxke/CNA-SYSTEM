import pytest
from fastapi.testclient import TestClient
from main import app
from typing import Generator

# We can reuse the test client which initializes lifespan implicitly.
# The lifespan will trigger `build_dataset_graph` and load into `app.state`.
# Since this uses the actual synthetic dataset and models, this acts as 
# a full integration test.

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_summary(client):
    response = client.get("/api/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "total_entities" in data
    assert "total_relationships" in data
    
    # Regression test: total_cases must match inventory (250)
    assert data["total_cases"] == 250
    # Graph semantics should be preserved (graph nodes are just those with relationships)
    # The total nodes in graph = total_entities + (cases with relationships)

def test_cases_list(client):
    response = client.get("/api/cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list)
    assert len(cases) > 0
    # Regression test: must return all 250 cases
    assert len(cases) == 250
    # verify safety terminology is implicitly handled by not injecting guilt
    for c in cases:
        assert c["type"] in ("CASE", "CASE_ID")
        
def test_known_case(client):
    response = client.get("/api/cases/CASE-001")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CASE-001"
    assert "details" in data
    assert "connected_entities" in data

def test_unknown_case(client):
    response = client.get("/api/cases/CASE-999999")
    assert response.status_code == 404

def test_case_graph(client):
    response = client.get("/api/cases/CASE-001/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    
    # Edges should preserve provenance
    if len(data["edges"]) > 0:
        edge = data["edges"][0]
        assert "confidence" in edge
        assert "evidence" in edge

def test_case_without_graph_evidence(client):
    # Regression test: A case that exists in cases.csv but has NO relationships in transactions/communications
    # For example, CASE-040 might be one of them (since only 20 cases are in the graph)
    # Let's test the endpoint behavior for a case that is not in the graph
    cases_response = client.get("/api/cases")
    all_cases = cases_response.json()
    
    # Find a case that has no connected_entities to verify
    for case in all_cases:
        case_id = case["id"]
        case_detail = client.get(f"/api/cases/{case_id}").json()
        if len(case_detail.get("connected_entities", [])) == 0:
            graph_resp = client.get(f"/api/cases/{case_id}/graph")
            assert graph_resp.status_code == 200
            graph_data = graph_resp.json()
            # Must not fabricate relationships
            assert len(graph_data["edges"]) == 0
            break

def test_related_cases(client):
    response = client.get("/api/cases/CASE-001/related")
    assert response.status_code == 200
    data = response.json()
    assert "related_cases" in data
    assert isinstance(data["related_cases"], list)
    assert "related_cases_details" in data
    assert isinstance(data["related_cases_details"], list)

def test_case_details_step17_enrichment(client):
    response = client.get("/api/cases/CASE-001")
    assert response.status_code == 200
    data = response.json()
    assert "associated_persons" in data
    assert isinstance(data["associated_persons"], list)
    assert len(data["associated_persons"]) > 0
    person = data["associated_persons"][0]
    assert "person_id" in person
    assert "full_name" in person
    assert "role" in person
    assert "linked_cases_count" in person

    assert "related_entities" in data
    entities = data["related_entities"]
    assert "locations" in entities
    assert "phones" in entities
    assert "bank_accounts" in entities
    assert "vehicles" in entities
    assert "organizations" in entities

    assert "relationships" in data
    assert isinstance(data["relationships"], list)
    if len(data["relationships"]) > 0:
        rel = data["relationships"][0]
        assert "confidence" in rel
        assert "evidence" in rel
        assert "detection_method" in rel

    assert "related_cases" in data
    assert isinstance(data["related_cases"], list)


def test_entities_list(client):
    response = client.get("/api/entities")
    assert response.status_code == 200
    entities = response.json()
    assert isinstance(entities, list)
    assert len(entities) > 0

def test_entity_details(client):
    # Get the first entity to dynamically test
    res = client.get("/api/entities?limit=1")
    ent_id = res.json()[0]["id"]
    
    response = client.get(f"/api/entities/{ent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["entity_id"] == ent_id
    assert "graph_metrics" in data
    assert "priority_information" in data

def test_unknown_entity(client):
    response = client.get("/api/entities/UNKNOWN-123456")
    assert response.status_code == 404

def test_person_investigation_profile_step18(client):
    # 1. Test rich person dossier
    response = client.get("/api/entities/PERSON-001")
    assert response.status_code == 200
    data = response.json()
    assert data["entity_id"] == "PERSON-001"
    assert data["entity_type"] == "PERSON"
    assert "demographics" in data
    assert data["demographics"]["full_name"] == "Arjun Mehta"
    assert "aliases" in data
    assert "contact" in data
    assert "associated_cases" in data
    assert len(data["associated_cases"]) > 0
    assert "assets" in data
    assert "phones" in data["assets"]
    assert "family_relationships" in data
    assert len(data["family_relationships"]) > 0
    assert "safety_disclaimer" in data["family_relationships"][0]
    assert "network_summary" in data
    assert "evidence_relationships" in data
    assert "graph_metrics" in data
    assert "priority_information" in data

    # 2. Test persons summary registry endpoint
    persons_resp = client.get("/api/persons")
    assert persons_resp.status_code == 200
    persons = persons_resp.json()
    assert len(persons) == 200
    assert persons[0]["type"] == "PERSON"

    # 3. Test global search for person
    search_resp = client.get("/api/search?q=Arjun")
    assert search_resp.status_code == 200
    search_results = search_resp.json()["results"]
    assert any(r["id"] == "PERSON-001" for r in search_results)


def test_entity_relationships(client):
    res = client.get("/api/entities?limit=1")
    ent_id = res.json()[0]["id"]
    
    response = client.get(f"/api/entities/{ent_id}/relationships")
    assert response.status_code == 200
    edges = response.json()
    assert isinstance(edges, list)

def test_relationships_list(client):
    response = client.get("/api/relationships?limit=5")
    assert response.status_code == 200
    edges = response.json()
    assert isinstance(edges, list)
    if len(edges) > 0:
        assert "evidence" in edges[0]

def test_analytics(client):
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "degree_centrality" in data
    assert "communities" in data

def test_entity_analytics(client):
    res = client.get("/api/entities?limit=1")
    ent_id = res.json()[0]["id"]
    
    response = client.get(f"/api/analytics/entities/{ent_id}")
    assert response.status_code == 200
    data = response.json()
    # At minimum should have degree centrality or community
    assert any(k in data for k in ["degree_centrality", "community_id"])

def test_priority_list(client):
    response = client.get("/api/priority?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
def test_priority_filtering(client):
    response = client.get("/api/priority?entity_type=PERSON&limit=5")
    assert response.status_code == 200
    for p in response.json():
        assert p["entity_type"] == "PERSON"
        
def test_search(client):
    response = client.get("/api/search?q=Arjun Mehta")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_empty_search(client):
    response = client.get("/api/search?q=")
    assert response.status_code == 200
    assert response.json() == {"results": []}

def test_invalid_filters(client):
    # limit must be >= 1
    response = client.get("/api/entities?limit=0")
    assert response.status_code == 422 # FastAPI validation error

def test_cors_configuration(client):
    # Test allowed origin
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    }
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
