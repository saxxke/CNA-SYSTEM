from fastapi import APIRouter
from .health import router as health_router
from .summary import router as summary_router
from .cases import router as cases_router
from .entities import router as entities_router
from .relationships import router as relationships_router
from .analytics import router as analytics_router
from .priority import router as priority_router
from .search import router as search_router
from .assistant import router as assistant_router
from .auth import router as auth_router
from .citizen import router as citizen_router
from .audit import router as audit_router
from .provenance import router as provenance_router

router = APIRouter()
router.include_router(health_router, tags=["Health"])
router.include_router(auth_router, tags=["Authentication"])
router.include_router(citizen_router, tags=["Citizen Portal"])
router.include_router(audit_router, tags=["Audit Logging"])
router.include_router(summary_router, tags=["Summary"])
router.include_router(cases_router, tags=["Cases"])
router.include_router(entities_router, tags=["Entities"])
router.include_router(relationships_router, tags=["Relationships"])
router.include_router(analytics_router, tags=["Analytics"])
router.include_router(priority_router, tags=["Priority"])
router.include_router(search_router, tags=["Search"])
router.include_router(assistant_router, tags=["Assistant"])
router.include_router(provenance_router, tags=["Provenance"])
