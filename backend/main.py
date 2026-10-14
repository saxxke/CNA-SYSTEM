import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import networkx as nx

from modules.graph.dataset_integration import build_dataset_graph, get_case_inventory
from modules.analytics.graph_analytics import analyze_graph
from modules.priority.priority_scorer import calculate_priority_scores
from modules.auth.demo_users import get_demo_user_repository
from modules.auth.tokens import TokenStore
from modules.auth.citizen_access import create_demo_citizen_access_repository
from modules.auth.investigation_access import create_demo_investigation_access_repository
from modules.auth.audit_repository import create_demo_audit_repository
from modules.auth.audit_service import log_unauthorized_access_denied
from api.dependencies import extract_bearer_token
from api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Load the complete case inventory
    print("Building application context: Loading case inventory...")
    cases = get_case_inventory()
    app.state.cases = cases
    
    # 2. Build integration graph exactly once
    print("Building application context: Loading dataset graph...")
    G = build_dataset_graph()
    app.state.graph = G
    
    # 3. Run graph analytics exactly once
    print("Building application context: Running graph analytics...")
    analytics = analyze_graph(G)
    app.state.analytics = analytics
    
    # 4. Calculate priority scores exactly once
    print("Building application context: Calculating priority scores...")
    priority = calculate_priority_scores(G, analytics)
    app.state.priority = priority
    
    # 5. Initialize authentication store, citizen access repository, investigation access repository & audit repository
    print("Building application context: Initializing authentication repository, token store, investigation access & audit repository...")
    app.state.user_repo = get_demo_user_repository()
    app.state.token_store = TokenStore()
    app.state.citizen_access_repo = create_demo_citizen_access_repository()
    app.state.investigation_access_repo = create_demo_investigation_access_repository()
    app.state.audit_repo = create_demo_audit_repository()
    
    print("Application context fully initialized. API ready.")
    yield
    # Clean up resources if necessary
    app.state.cases = []
    app.state.graph = nx.MultiDiGraph()
    app.state.analytics = {}
    app.state.priority = []
    if hasattr(app.state, "token_store") and app.state.token_store:
        app.state.token_store.clear()
    if hasattr(app.state, "citizen_access_repo") and app.state.citizen_access_repo:
        app.state.citizen_access_repo.clear()
    if hasattr(app.state, "investigation_access_repo") and app.state.investigation_access_repo:
        app.state.investigation_access_repo.clear()
    if hasattr(app.state, "audit_repo") and app.state.audit_repo:
        app.state.audit_repo.clear()

app = FastAPI(
    title="Investigation Intelligence API",
    description="SYNTHETIC DEMONSTRATION DATA. Analytical decision-support interface. Requires human verification.",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize fallback state on app immediately for test isolation
app.state.user_repo = get_demo_user_repository()
app.state.token_store = TokenStore()
app.state.citizen_access_repo = create_demo_citizen_access_repository()
app.state.investigation_access_repo = create_demo_investigation_access_repository()
app.state.audit_repo = create_demo_audit_repository()


@app.exception_handler(HTTPException)
async def http_exception_audit_handler(request: Request, exc: HTTPException):
    """
    Centralized exception handler to authoritatively capture 401 and 403 access denials.
    Enforces the single-denial-event rule: exactly one event recorded per denied request.
    """
    if exc.status_code in (401, 403):
        if not getattr(request.state, "audit_denial_recorded", False):
            request.state.audit_denial_recorded = True
            audit_repo = getattr(request.app.state, "audit_repo", None)
            if audit_repo is not None:
                # Attempt to resolve authenticated actor
                user = None
                token_store = getattr(request.app.state, "token_store", None)
                user_repo = getattr(request.app.state, "user_repo", None)
                token = extract_bearer_token(request)
                if token and token_store and user_repo:
                    session = token_store.get_session(token)
                    if session:
                        user = user_repo.get_by_id(session.user_id)

                # Classify target object from path
                path = request.url.path
                target_type = "RESOURCE"
                target_id = path
                if "/cases/" in path:
                    target_type = "CASE"
                    parts = path.split("/cases/")
                    if len(parts) > 1 and parts[1]:
                        target_id = parts[1].split("/")[0]
                elif "/entities/" in path:
                    target_type = "PERSON" if ("family" in path or "PERSON" in path) else "ENTITY"
                    parts = path.split("/entities/")
                    if len(parts) > 1 and parts[1]:
                        target_id = parts[1].split("/")[0]
                elif "/citizen/" in path:
                    target_type = "CITIZEN_PORTAL"
                elif "/audit/" in path:
                    target_type = "AUDIT_LOGS"
                    target_id = "AUDIT_QUERY"

                log_unauthorized_access_denied(
                    repo=audit_repo,
                    request=request,
                    status_code=exc.status_code,
                    reason=str(exc.detail),
                    user=user,
                    target_type=target_type,
                    target_id=target_id
                )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None)
    )



# CORS Configuration
# Retain local development origins and allow external production frontend configuration via environment variables
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

env_origins = os.getenv("ALLOWED_ORIGINS") or os.getenv("FRONTEND_URL")
if env_origins:
    for origin in env_origins.split(","):
        cleaned = origin.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
