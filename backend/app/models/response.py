from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    message: str


class VersionResponse(BaseModel):
    application: str
    version: str


class AnalyzeResponse(BaseModel):
    success: bool
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]