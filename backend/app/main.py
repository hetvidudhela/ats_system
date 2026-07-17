from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import logger

from app.api.health import router as health_router
from app.api.version import router as version_router
from app.api.analyze import router as analyze_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    description="Backend API for the ATS Plugin.",
)

app.include_router(health_router)

app.include_router(version_router)

app.include_router(analyze_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to ATS Backend API",
        "docs": "/docs",
        "version": settings.API_VERSION,
    }


logger.info(f"{settings.APP_NAME} started successfully.")