from fastapi import APIRouter
from api.models import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    return {"status": "ok"}
