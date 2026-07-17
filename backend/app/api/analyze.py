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

router = APIRouter(
    prefix="/analyze",
    tags=["ATS"],
)


@router.post("/")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    # -------------------------
    # Validate uploaded file
    # -------------------------
    validate_file(resume)

    # -------------------------
    # Save uploaded file
    # -------------------------
    file_path = save_uploaded_file(resume)

    # -------------------------
    # Parse Resume
    # -------------------------
    parsed_resume = parser_service.parse(file_path)

    # -------------------------
    # Parser failed
    # -------------------------
    if not parsed_resume["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=parsed_resume["error"],
        )

    

    # -------------------------
    # NEXT STEP
    # Integrate Member 2's ATS
    # -------------------------

    # report = ats_service.analyze(
    #     parsed_data,
    #     job_description,
    # )
    #
    # return AnalyzeResponse(
    #     success=report["success"],
    #     score=report["score"],
    #     matched_skills=report["matched_skills"],
    #     missing_skills=report["missing_skills"],
    #     suggestions=report["suggestions"],
    # )

    # Temporary return for testing parser integration
    return parsed_resume