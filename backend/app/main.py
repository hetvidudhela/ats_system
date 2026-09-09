from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Enable CORS for frontend and Chrome extension integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(version_router)
app.include_router(analyze_router)

# Also mount under /api prefix for full backward/forward compatibility
app.include_router(health_router, prefix="/api")
app.include_router(version_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")



@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to ATS Backend API",
        "docs": "/docs",
        "version": settings.API_VERSION,
    }


logger.info(f"{settings.APP_NAME} started successfully.")