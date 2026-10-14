"""
ai.py
=====
API router for the optional Gemini AI Assistant.
Mounted under /ai and /api/ai.
"""

from fastapi import APIRouter, HTTPException, status

from app.models.ai import (
    AIChatRequest,
    AIChatResponse,
    AIApplyChangesRequest,
    AIApplyChangesResponse,
)
from app.services.gemini_service import gemini_service
from app.core.logger import logger

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"],
)


@router.get("/status")
async def get_ai_status():
    """
    Check if the Gemini AI Assistant is configured and ready.
    Does NOT leak the actual API key.
    """
    configured = gemini_service.is_configured()
    return {
        "available": configured,
        "model": gemini_service._model if configured else None,
        "message": "AI Assistant is ready." if configured else "Gemini API key is not configured.",
    }


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_assistant(request: AIChatRequest):
    """
    Interact with the Gemini AI Assistant.
    Provides resume and ATS analysis context.
    Returns structured assistant response with optional proposals.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    # gemini_service.chat handles missing keys, timeouts, and errors gracefully
    response = await gemini_service.chat(request)
    return response


@router.post("/apply-changes", response_model=AIApplyChangesResponse)
async def apply_approved_changes(request: AIApplyChangesRequest):
    """
    Validates user-approved resume modifications, constructs an updated
    resume representation, and recalculates the ATS score using the
    EXISTING deterministic ATS engine.
    Original resume data is NOT altered.
    """
    if not request.original_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Original resume context is required.",
        )

    if not request.job_description or len(request.job_description.strip()) < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid job description is required for re-scoring.",
        )

    try:
        updated_resume, analysis_response = gemini_service.apply_approved_changes(
            original_resume=request.original_resume,
            approved_changes=request.approved_changes,
            job_description=request.job_description,
        )

        return AIApplyChangesResponse(
            success=True,
            updated_resume=updated_resume,
            analysis_result=analysis_response,
        )
    except Exception as e:
        logger.exception(f"Error applying approved changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply changes: {str(e)}",
        )
