from fastapi import APIRouter
from app.models.response import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)



@router.get("/", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        message="ATS Backend is running."
    )