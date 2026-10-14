from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    message: str


class VersionResponse(BaseModel):
    application: str
    version: str


class AnalyzeResponse(BaseModel):
    """
    Response model for the /analyze endpoint.
    Maintains backward compatibility with original fields while exposing detailed ATS analysis.
    """
    success: bool
    score: int
    ats_score: Optional[int] = None
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    required_matched: List[str] = Field(default_factory=list)
    required_missing: List[str] = Field(default_factory=list)
    preferred_matched: List[str] = Field(default_factory=list)
    preferred_missing: List[str] = Field(default_factory=list)
    score_breakdown: Optional[Dict[str, Dict[str, float]]] = None
    experience_analysis: Optional[Dict[str, Any]] = None
    education_analysis: Optional[Dict[str, Any]] = None
    project_relevance: Optional[Dict[str, Any]] = None
    match_details: Optional[List[Dict[str, Any]]] = None
    suggestions: List[str] = Field(default_factory=list)
    parsed_resume: Optional[Dict[str, Any]] = None
    eligibility: Optional[Dict[str, Any]] = None