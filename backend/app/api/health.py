from fastapi import APIRouter
from app.models.response import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)



@router.get("/", response_model=HealthResponse)
@router.get("", response_model=HealthResponse, include_in_schema=False)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        message="ATS Backend is running."
    )