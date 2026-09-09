from fastapi import APIRouter

from app.core.config import settings
from app.models.response import VersionResponse

router = APIRouter(
    prefix="/version",
    tags=["Version"],
)



@router.get("/", response_model=VersionResponse)
@router.get("", response_model=VersionResponse, include_in_schema=False)
def get_version() -> VersionResponse:
    return VersionResponse(
        application=settings.APP_NAME,
        version=settings.API_VERSION,
    )
