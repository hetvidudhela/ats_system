"""
ATS Engine Package
==================
Production-ready, deterministic ATS (Applicant Tracking System) analysis engine.
Compares parsed resume data against Job Descriptions to produce objective compatibility scores,
skill gap breakdowns, experience/education analyses, and actionable recommendations.
"""

from app.services.ats.engine import ATSEngine, analyze_resume_against_jd
from app.services.ats.models import ATSReport, ScoreBreakdown, SkillMatchDetail

__all__ = [
    "ATSEngine",
    "analyze_resume_against_jd",
    "ATSReport",
    "ScoreBreakdown",
    "SkillMatchDetail",
]
