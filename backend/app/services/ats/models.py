"""
models.py
=========
Data models for the ATS Analysis Engine.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SkillMatchDetail(BaseModel):
    """Details regarding an individual skill match comparison."""
    skill: str
    status: str = Field(..., description="'matched' or 'missing'")
    match_type: str = Field("none", description="'exact', 'normalized', 'alias', 'fuzzy', or 'none'")
    is_required: bool = False
    evidence: str = ""


class ScoreComponent(BaseModel):
    """Component of the score breakdown."""
    score: float
    max_score: float


class ScoreBreakdown(BaseModel):
    """Complete score breakdown totaling 100 points."""
    keyword_match: ScoreComponent
    experience_match: ScoreComponent
    education_match: ScoreComponent
    project_relevance: ScoreComponent
    formatting: ScoreComponent
    quality: ScoreComponent

    def to_dict(self) -> dict[str, dict[str, float]]:
        return {
            "keyword_match": {"score": round(self.keyword_match.score, 1), "max_score": self.keyword_match.max_score},
            "experience_match": {"score": round(self.experience_match.score, 1), "max_score": self.experience_match.max_score},
            "education_match": {"score": round(self.education_match.score, 1), "max_score": self.education_match.max_score},
            "project_relevance": {"score": round(self.project_relevance.score, 1), "max_score": self.project_relevance.max_score},
            "formatting": {"score": round(self.formatting.score, 1), "max_score": self.formatting.max_score},
            "quality": {"score": round(self.quality.score, 1), "max_score": self.quality.max_score},
        }


class ExperienceAnalysis(BaseModel):
    """Evaluation of experience requirements."""
    status: str = Field(..., description="'meets', 'partially_meets', 'does_not_meet', 'insufficient_evidence', or 'not_specified'")
    required_years: Optional[float] = None
    estimated_years: Optional[float] = None
    details: str = ""


class EducationAnalysis(BaseModel):
    """Evaluation of education requirements."""
    status: str = Field(..., description="'meets', 'partially_meets', 'does_not_meet', or 'not_specified'")
    required_level: str = ""
    detected_education: str = ""
    details: str = ""


class ProjectRelevanceAnalysis(BaseModel):
    """Evaluation of project relevance to JD tech stack."""
    score: float
    max_score: float
    matched_technologies: List[str] = Field(default_factory=list)
    details: str = ""


class ATSReport(BaseModel):
    """
    Complete ATS compatibility report returned by the engine.
    Compatible with frontend and backend API expectations.
    """
    success: bool = True
    ats_score: int = Field(..., ge=0, le=100, description="Overall ATS score between 0 and 100")
    score: int = Field(..., ge=0, le=100, description="Alias for ats_score for backward compatibility")
    score_breakdown: dict[str, dict[str, float]]
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    required_matched: List[str] = Field(default_factory=list)
    required_missing: List[str] = Field(default_factory=list)
    preferred_matched: List[str] = Field(default_factory=list)
    preferred_missing: List[str] = Field(default_factory=list)
    experience_analysis: dict[str, Any]
    education_analysis: dict[str, Any]
    project_relevance: dict[str, Any]
    match_details: List[dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    eligibility: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
