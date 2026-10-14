"""
engine.py
=========
Main ATS Engine orchestrator.
Coordinates JD analysis, multi-tiered matching, scoring, and suggestion generation.
"""

from typing import Any, Dict
from app.services.ats.models import ATSReport
from app.services.ats.jd_analyzer import analyze_job_description
from app.services.ats.matcher import (
    match_skills,
    evaluate_experience,
    evaluate_education,
    evaluate_project_relevance,
)
from app.services.ats.scorer import compute_overall_ats_score
from app.services.ats.suggestions import generate_actionable_suggestions
from app.services.ats.eligibility import evaluate_candidate_eligibility


class ATSEngine:
    """
    Independent ATS Analysis Engine.
    Deterministic, reproducible, and decoupled from web frameworks.
    """

    def analyze(self, resume_data: dict, job_description: str) -> ATSReport:
        """
        Analyze a structured resume dictionary against a job description.

        Args:
            resume_data: Dictionary produced by parse_resume()
            job_description: Plain text of target job posting

        Returns:
            ATSReport containing score, breakdowns, matches, and suggestions.
        """
        # Defensive validation
        if not isinstance(resume_data, dict):
            resume_data = {}

        jd_text = (job_description or "").strip()

        # Handle empty or invalid Job Description safely
        if not jd_text or len(jd_text) < 15:
            return ATSReport(
                success=False,
                ats_score=0,
                score=0,
                score_breakdown={
                    "keyword_match": {"score": 0.0, "max_score": 40.0},
                    "experience_match": {"score": 0.0, "max_score": 20.0},
                    "education_match": {"score": 0.0, "max_score": 10.0},
                    "project_relevance": {"score": 0.0, "max_score": 15.0},
                    "formatting": {"score": 0.0, "max_score": 10.0},
                    "quality": {"score": 0.0, "max_score": 5.0},
                },
                matched_skills=[],
                missing_skills=[],
                matched_keywords=[],
                missing_keywords=[],
                required_matched=[],
                required_missing=[],
                preferred_matched=[],
                preferred_missing=[],
                experience_analysis={"status": "not_specified", "details": "Job description is empty or too short."},
                education_analysis={"status": "not_specified", "details": "Job description is empty or too short."},
                project_relevance={"score": 0.0, "max_score": 15.0, "details": "No job description provided."},
                match_details=[],
                suggestions=["Please provide a comprehensive job description with clear requirements and skills."],
                eligibility={
                    "eligible": False,
                    "warning": True,
                    "status": "requirements_not_verified",
                    "reasons": ["Job description is empty or too short to verify eligibility."],
                },
            )

        # 1. Analyze Job Description
        jd_analysis = analyze_job_description(jd_text)

        # 2. Match Skills and Keywords
        match_details, skills_summary = match_skills(jd_analysis, resume_data)

        # 3. Evaluate Experience Requirements
        exp_analysis = evaluate_experience(jd_analysis, resume_data)

        # 4. Evaluate Education Requirements
        edu_analysis = evaluate_education(jd_analysis, resume_data)

        # 5. Evaluate Project Relevance
        proj_analysis = evaluate_project_relevance(jd_analysis, resume_data)

        # 6. Compute Deterministic 0-100 Score
        overall_score, breakdown = compute_overall_ats_score(
            skills_summary=skills_summary,
            exp_analysis=exp_analysis,
            edu_analysis=edu_analysis,
            proj_analysis=proj_analysis,
            resume_data=resume_data,
        )

        # 7. Generate Actionable Suggestions
        suggestions = generate_actionable_suggestions(
            skills_summary=skills_summary,
            exp_analysis=exp_analysis,
            edu_analysis=edu_analysis,
            proj_analysis=proj_analysis,
            resume_data=resume_data,
        )

        # 8. Evaluate Candidate Eligibility
        eligibility = evaluate_candidate_eligibility(
            overall_score=overall_score,
            skills_summary=skills_summary,
            exp_analysis=exp_analysis,
            edu_analysis=edu_analysis,
            jd_analysis=jd_analysis,
        )

        # 9. Assemble Complete Report
        return ATSReport(
            success=True,
            ats_score=overall_score,
            score=overall_score,
            score_breakdown=breakdown.to_dict(),
            matched_skills=skills_summary["matched_skills"],
            missing_skills=skills_summary["missing_skills"],
            matched_keywords=skills_summary["matched_keywords"],
            missing_keywords=skills_summary["missing_keywords"],
            required_matched=skills_summary["required_matched"],
            required_missing=skills_summary["required_missing"],
            preferred_matched=skills_summary["preferred_matched"],
            preferred_missing=skills_summary["preferred_missing"],
            experience_analysis=exp_analysis.model_dump(),
            education_analysis=edu_analysis.model_dump(),
            project_relevance=proj_analysis.model_dump(),
            match_details=[d.model_dump() for d in match_details],
            suggestions=suggestions,
            eligibility=eligibility.model_dump(),
        )


# Global Engine Instance
_engine = ATSEngine()


def analyze_resume_against_jd(resume_data: dict, job_description: str) -> ATSReport:
    """Public helper function to analyze resume data against a Job Description."""
    return _engine.analyze(resume_data, job_description)
