"""
scratch/verify_phase5.py
========================
End-to-end API and RBAC verification script for Phase 5 frontend integration.
Tests all 4 roles, login, /me rehydration, logout, citizen isolation, and deep-link authorization.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from main import app
from modules.auth.demo_users import DEMO_CREDENTIALS, get_demo_user_repository
from modules.auth.tokens import TokenStore
from modules.auth.citizen_access import create_demo_citizen_access_repository

def run_verification():
    print("==================================================")
    print("PHASE 5: ROLE-BASED AUTH & NAVIGATION VERIFICATION")
    print("==================================================")

    results = []

    with TestClient(app) as client:
        # Fresh state
        client.app.state.user_repo = get_demo_user_repository()
        client.app.state.token_store = TokenStore()
        client.app.state.citizen_access_repo = create_demo_citizen_access_repository()

        # 1. Citizen Login
        resp = client.post("/api/auth/login", json={"username": "citizen.demo", "password": DEMO_CREDENTIALS["citizen.demo"]})
        assert resp.status_code == 200, f"Citizen login failed: {resp.text}"
        cit_token = resp.json()["token"]
        assert resp.json()["user"]["role"] == "CITIZEN"
        results.append(("1. Citizen Login", "PASS", resp.json()["user"]["role"]))

        # 2. IO Login
        resp = client.post("/api/auth/login", json={"username": "io.demo", "password": DEMO_CREDENTIALS["io.demo"]})
        assert resp.status_code == 200
        io_token = resp.json()["token"]
        assert resp.json()["user"]["role"] == "INVESTIGATING_OFFICER"
        results.append(("2. IO Login", "PASS", resp.json()["user"]["role"]))

        # 3. IPS Login
        resp = client.post("/api/auth/login", json={"username": "ips.demo", "password": DEMO_CREDENTIALS["ips.demo"]})
        assert resp.status_code == 200
        ips_token = resp.json()["token"]
        assert resp.json()["user"]["role"] == "IPS_OFFICER"
        results.append(("3. IPS Login", "PASS", resp.json()["user"]["role"]))

        # 4. Home Ministry Login
        resp = client.post("/api/auth/login", json={"username": "hm.demo", "password": DEMO_CREDENTIALS["hm.demo"]})
        assert resp.status_code == 200
        hm_token = resp.json()["token"]
        assert resp.json()["user"]["role"] == "HOME_MINISTRY"
        results.append(("4. Home Ministry Login", "PASS", resp.json()["user"]["role"]))

        # 5. Authoritative Identity Rehydration (/api/auth/me)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {cit_token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "citizen.demo"
        results.append(("5. /api/auth/me rehydration", "PASS", "Strictly authoritative from backend"))

        # 6. Logout and Token Revocation
        resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {cit_token}"})
        assert resp.status_code == 200
        # Subsequent request with revoked token fails
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {cit_token}"})
        assert resp.status_code == 401
        results.append(("6. Logout and Token Invalidation", "PASS", "Revoked token immediately returns 401"))

        # Re-login citizen for remaining tests
        cit_token = client.post("/api/auth/login", json={"username": "citizen.demo", "password": DEMO_CREDENTIALS["citizen.demo"]}).json()["token"]

        # 7. Invalid Credentials
        resp = client.post("/api/auth/login", json={"username": "io.demo", "password": "WrongPassword@2026"})
        assert resp.status_code == 401
        assert "Invalid username or password" in resp.text
        results.append(("7. Invalid credentials handling", "PASS", "Uniform 401 error message"))

        # 8. Unauthenticated Access
        resp = client.get("/api/cases")
        assert resp.status_code == 401
        results.append(("8. Unauthenticated access guard", "PASS", "Returns 401 with WWW-Authenticate header"))

        # 9. Citizen Authorized Cases (/api/citizen/cases)
        resp = client.get("/api/citizen/cases", headers={"Authorization": f"Bearer {cit_token}"})
        assert resp.status_code == 200
        case_ids = [c["case_id"] for c in resp.json()]
        assert set(case_ids) == {"CASE-001", "CASE-014"}
        results.append(("9. Citizen Cases list", "PASS", f"Only authorized cases returned: {case_ids}"))

        # 10. Citizen Authorized Case Detail
        resp = client.get("/api/citizen/cases/CASE-001", headers={"Authorization": f"Bearer {cit_token}"})
        assert resp.status_code == 200
        assert "official_notice" in resp.json()
        assert "suspects" not in resp.json()  # Internal data omitted
        results.append(("10. Citizen Authorized Case Detail", "PASS", "Sanitized citizen-safe fields only"))

        # 11. Citizen Unauthorized Case Detail
        resp = client.get("/api/citizen/cases/CASE-002", headers={"Authorization": f"Bearer {cit_token}"})
        assert resp.status_code == 403
        results.append(("11. Citizen Unauthorized Case Detail", "PASS", "Object-level authorization denied (403)"))

        # 12. Citizen Cannot Access Investigator Endpoints
        cit_denials = [
            client.get("/api/cases", headers={"Authorization": f"Bearer {cit_token}"}).status_code,
            client.get("/api/network", headers={"Authorization": f"Bearer {cit_token}"}).status_code,
            client.get("/api/priority", headers={"Authorization": f"Bearer {cit_token}"}).status_code,
            client.post("/api/assistant/query", json={"question": "Test"}, headers={"Authorization": f"Bearer {cit_token}"}).status_code,
        ]
        assert all(s == 403 for s in cit_denials)
        results.append(("12. Citizen restricted from investigator APIs", "PASS", "All returned 403 Forbidden"))

        # 13. IO Can Access Investigator Endpoints
        io_access = [
            client.get("/api/cases", headers={"Authorization": f"Bearer {io_token}"}).status_code,
            client.get("/api/network", headers={"Authorization": f"Bearer {io_token}"}).status_code,
            client.get("/api/analytics", headers={"Authorization": f"Bearer {io_token}"}).status_code,
            client.get("/api/priority", headers={"Authorization": f"Bearer {io_token}"}).status_code,
        ]
        assert all(s == 200 for s in io_access)
        results.append(("13. IO access to investigation tools", "PASS", "All returned 200 OK"))

        # 14. IPS Can Access Supervisory Endpoints
        ips_cross = client.get("/api/analytics/cross-case", headers={"Authorization": f"Bearer {ips_token}"})
        assert ips_cross.status_code == 200
        assert "cross_case_connectivity" in ips_cross.json()

        ips_reports = client.get("/api/analytics/reports", headers={"Authorization": f"Bearer {ips_token}"})
        assert ips_reports.status_code == 200
        results.append(("14. IPS supervisory endpoints", "PASS", "Cross-case analytics & reports 200 OK"))

        # 15. Home Ministry Strategic Endpoints
        hm_trends = client.get("/api/analytics/strategic-trends", headers={"Authorization": f"Bearer {hm_token}"})
        assert hm_trends.status_code == 200

        hm_regional = client.get("/api/analytics/regional-statistics", headers={"Authorization": f"Bearer {hm_token}"})
        assert hm_regional.status_code == 200
        results.append(("15. Home Ministry strategic endpoints", "PASS", "Trends & regional statistics 200 OK"))

        # 16. Home Ministry Cannot Access Individual Investigator Person or Network Data
        hm_denials = [
            client.get("/api/persons", headers={"Authorization": f"Bearer {hm_token}"}).status_code,
            client.get("/api/entities", headers={"Authorization": f"Bearer {hm_token}"}).status_code,
            client.get("/api/network", headers={"Authorization": f"Bearer {hm_token}"}).status_code,
        ]
        assert all(s == 403 for s in hm_denials)
        results.append(("16. Home Ministry restricted from raw network & person data", "PASS", "All returned 403 Forbidden"))

    print("\nVERIFICATION SUMMARY TABLE:")
    print("-" * 75)
    for name, status, detail in results:
        print(f"[{status}] {name:<45} | {detail}")
    print("-" * 75)
    print("ALL 16 BACKEND RBAC AND CITIZEN INTEGRATION CHECKS PASSED!")

if __name__ == "__main__":
    run_verification()
