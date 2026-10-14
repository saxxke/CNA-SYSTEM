"""
conftest.py
===========
Pytest fixtures and configuration for the test suite.

Ensures that legacy unit and regression tests written prior to the introduction
of Phase 2/3 authentication and RBAC can execute without modification,
while tests in test_rbac.py and test_auth_api.py run with 100% strict, real,
unmocked authentication and authorization.
"""

import pytest
from main import app
from fastapi import HTTPException, Depends
from api.dependencies import (
    require_authenticated_user,
    require_investigation_case_access,
    get_officer_authorized_case_ids,
    get_cases,
    get_investigation_access_repo
)
from modules.persistence.runtime_store import clear_runtime_data
from modules.auth.roles import UserRole
from modules.auth.models import User
from modules.auth.investigation_access import JurisdictionScope, JurisdictionLevel
from modules.auth.demo_users import get_demo_user_repository


LEGACY_TEST_MODULES = {
    "test_api",
    "test_case_registration",
    "test_assistant",
    "test_family_explorer",
    "test_advanced_search",
}


@pytest.fixture(autouse=True)
def handle_legacy_auth(request):
    """
    For legacy integration test modules, provide an authenticated supervisory session
    with national jurisdiction scope so baseline assertions continue to pass
    without altering the existing test files.
    """
    module_name = request.module.__name__.split(".")[-1]
    if module_name in LEGACY_TEST_MODULES:
        clear_runtime_data()
        ips_user = get_demo_user_repository().get_by_username("ips.demo")
        legacy_officer = ips_user.model_copy(update={
            "jurisdiction": "All India",
            "jurisdiction_level": "NATIONAL"
        })
        if hasattr(app.state, "investigation_access_repo") and app.state.investigation_access_repo:
            app.state.investigation_access_repo.set_jurisdiction(
                legacy_officer.user_id,
                JurisdictionScope(level=JurisdictionLevel.NATIONAL, state="All India")
            )
        
        app.dependency_overrides[require_authenticated_user] = lambda: legacy_officer

        # In legacy tests, grant full investigation scope so pre-Phase-6 baseline assertions pass
        def legacy_case_access(case_id: str, cases: list = Depends(get_cases)):
            clean_case_id = case_id.strip().upper()
            for c in cases:
                cid = c.get("case_id") or c.get("id")
                if cid and str(cid).strip().upper() == clean_case_id:
                    return c
            raise HTTPException(status_code=404, detail=f"Case record '{case_id}' not found.")

        app.dependency_overrides[require_investigation_case_access] = legacy_case_access
        app.dependency_overrides[get_officer_authorized_case_ids] = (
            lambda request, current_user=None, inv_repo=None, inventory=[]: {
                c.get("case_id") or c.get("id") for c in (inventory or getattr(request.app.state, "cases", []))
            }
        )

        try:
            yield
        finally:
            app.dependency_overrides.pop(require_authenticated_user, None)
            app.dependency_overrides.pop(require_investigation_case_access, None)
            app.dependency_overrides.pop(get_officer_authorized_case_ids, None)
            clear_runtime_data()
    else:
        yield
