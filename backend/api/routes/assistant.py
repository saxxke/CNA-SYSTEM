"""
assistant.py
============
API endpoints for the Step 21 AI Investigation Assistant.

Exposes:
- POST /api/assistant/query: Accepts natural language investigator questions and returns
  grounded structured answers, deterministic provenance items, and entity cards.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
import networkx as nx

from api.dependencies import (
    get_graph,
    get_cases,
    get_analytics,
    get_priority,
    require_permission,
    get_investigation_access_repo,
    get_audit_repo,
)
from modules.auth.models import User
from modules.auth.permissions import Permission
from modules.auth.investigation_access import InvestigationAccessRepository
from modules.auth.audit_repository import AuditLogRepository
from modules.auth.audit_service import log_assistant_query
from modules.assistant.models import AssistantQueryRequest, AssistantQueryResponse
from modules.assistant.assistant_service import process_assistant_query

router = APIRouter(
    dependencies=[Depends(require_permission(Permission.USE_AI_ASSISTANT))]
)


@router.post("/assistant/query", response_model=AssistantQueryResponse)
def query_assistant(
    payload: AssistantQueryRequest,
    request: Request,
    current_user: User = Depends(require_permission(Permission.USE_AI_ASSISTANT)),
    inv_repo: InvestigationAccessRepository = Depends(get_investigation_access_repo),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
    inventory: list = Depends(get_cases),
    G: nx.MultiDiGraph = Depends(get_graph),
    analytics: dict = Depends(get_analytics),
    priority: list = Depends(get_priority)
):
    """
    Step 21: Grounded AI Investigation Assistant query endpoint.
    Retrieval is strictly gated server-side by officer authorized investigation scope.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Inquiry question cannot be empty.")

    authorized_case_ids = inv_repo.get_authorized_case_ids_for_officer(
        current_user.user_id,
        current_user.role.value,
        inventory
    )
    scope = inv_repo.get_jurisdiction(current_user.user_id)

    context = {
        "active_case_id": payload.active_case_id,
        "active_person_id": payload.active_person_id,
        "conversation_context": payload.conversation_context,
        "user_id": current_user.user_id,
        "user_role": current_user.role.value,
        "authorized_case_ids": list(authorized_case_ids),
        "jurisdiction": scope.model_dump() if scope else None,
    }

    try:
        response = process_assistant_query(
            question=payload.question,
            context=context,
            G=G,
            analytics=analytics,
            priority=priority
        )

        # Audit log sanitized AI query (never stores raw query string or answer markdown)
        log_assistant_query(
            audit_repo,
            current_user,
            request,
            intent=str(response.intent),
            response_state=str(response.response_state),
            question_length=len(payload.question)
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant query processing failed: {str(e)}")

