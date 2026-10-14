import os
from pathlib import Path
from fastapi import (
    APIRouter,
    File,
    Form,
    UploadFile,
    HTTPException,
    status,
)

from app.utils.file_utils import (
    validate_file,
    save_uploaded_file,
)
from app.services.parser_service import parser_service
from app.services.ats_service import ats_service
from app.models.response import AnalyzeResponse

router = APIRouter(
    prefix="/analyze",
    tags=["ATS"],
)


@router.post("/", response_model=AnalyzeResponse)
@router.post("", response_model=AnalyzeResponse, include_in_schema=False)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(default=""),
):
    """
    Analyze an uploaded resume (PDF or DOCX) against a Job Description.

    1. Validates uploaded file and Job Description.
    2. Saves file temporarily and extracts structured data via Resume Parser.
    3. Runs the deterministic ATS Engine to compute compatibility score.
    4. Cleans up temporary file and returns comprehensive ATS report.
    """
    # -------------------------
    # Validate Job Description
    # -------------------------
    if not job_description or not job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is required and cannot be empty.",
        )

    if len(job_description.strip()) < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is too short. Please provide a detailed job description.",
        )

    # -------------------------
    # Validate uploaded file
    # -------------------------
    validate_file(resume)

    # -------------------------
    # Save uploaded file
    # -------------------------
    file_path = save_uploaded_file(resume)

    try:
        # -------------------------
        # Parse Resume
        # -------------------------
        parsed_resume = parser_service.parse(file_path)

        if not parsed_resume["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=parsed_resume["error"],
            )

        parsed_data = parsed_resume.get("data") or {}

        # -------------------------
        # Run ATS Engine Analysis
        # -------------------------
        report = ats_service.analyze(
            parsed_resume=parsed_data,
            job_description=job_description,
        )

        return AnalyzeResponse(
            success=report.get("success", True),
            score=report.get("score", 0),
            ats_score=report.get("ats_score", 0),
            matched_skills=report.get("matched_skills", []),
            missing_skills=report.get("missing_skills", []),
            matched_keywords=report.get("matched_keywords", []),
            missing_keywords=report.get("missing_keywords", []),
            required_matched=report.get("required_matched", []),
            required_missing=report.get("required_missing", []),
            preferred_matched=report.get("preferred_matched", []),
            preferred_missing=report.get("preferred_missing", []),
            score_breakdown=report.get("score_breakdown"),
            experience_analysis=report.get("experience_analysis"),
            education_analysis=report.get("education_analysis"),
            project_relevance=report.get("project_relevance"),
            match_details=report.get("match_details", []),
            suggestions=report.get("suggestions", []),
            parsed_resume=parsed_data,
            eligibility=report.get("eligibility"),
        )

    finally:
        # Clean up temporary uploaded file
        if isinstance(file_path, Path) and file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass