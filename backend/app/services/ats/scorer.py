"""
scorer.py
=========
Deterministic 0-100 scoring model for the ATS Engine.
Calculates objective compatibility scores using configurable weighted components.
"""

from typing import Any, Dict
from app.services.ats.models import (
    ScoreBreakdown,
    ScoreComponent,
    ExperienceAnalysis,
    EducationAnalysis,
    ProjectRelevanceAnalysis,
)

# Configurable Weights (Must sum to exactly 100)
WEIGHT_KEYWORD_MATCH = 40.0
WEIGHT_EXPERIENCE = 20.0
WEIGHT_PROJECT_RELEVANCE = 15.0
WEIGHT_EDUCATION = 10.0
WEIGHT_FORMATTING = 10.0
WEIGHT_QUALITY = 5.0

TOTAL_WEIGHT = (
    WEIGHT_KEYWORD_MATCH
    + WEIGHT_EXPERIENCE
    + WEIGHT_PROJECT_RELEVANCE
    + WEIGHT_EDUCATION
    + WEIGHT_FORMATTING
    + WEIGHT_QUALITY
)
assert TOTAL_WEIGHT == 100.0, f"Weights must sum to 100.0, got {TOTAL_WEIGHT}"


def calculate_keyword_score(skills_summary: Dict[str, Any]) -> float:
    """
    Calculate keyword & skill match score out of 40 points:
    - Required skills: 25 points
    - Preferred skills: 10 points
    - Domain keywords: 5 points
    """
    req_matched = len(skills_summary.get("required_matched", []))
    req_missing = len(skills_summary.get("required_missing", []))
    req_total = req_matched + req_missing

    pref_matched = len(skills_summary.get("preferred_matched", []))
    pref_missing = len(skills_summary.get("preferred_missing", []))
    pref_total = pref_matched + pref_missing

    kw_matched = len(skills_summary.get("matched_keywords", []))
    kw_missing = len(skills_summary.get("missing_keywords", []))
    kw_total = kw_matched + kw_missing

    if req_total > 0:
        req_score = (req_matched / req_total) * 25.0
    else:
        req_score = 0.0 if not req_matched and not pref_matched else 25.0

    if pref_total > 0:
        pref_score = (pref_matched / pref_total) * 10.0
    else:
        pref_score = (req_matched / max(1, req_total)) * 10.0 if req_total > 0 else 0.0

    if kw_total > 0:
        kw_score = (kw_matched / kw_total) * 5.0
    else:
        kw_score = (req_matched / max(1, req_total)) * 5.0 if req_total > 0 else 0.0

    total_kw_score = min(WEIGHT_KEYWORD_MATCH, req_score + pref_score + kw_score)
    return round(total_kw_score, 1)


def calculate_experience_score(exp_analysis: ExperienceAnalysis, resume_is_empty: bool) -> float:
    """
    Calculate experience match score out of 20 points:
    - meets: 20.0
    - not_specified (JD didn't ask): 20.0 (if resume has content)
    - partially_meets: 12.0
    - insufficient_evidence: 10.0
    - does_not_meet / empty resume: 0.0 - 4.0
    """
    if resume_is_empty:
        return 0.0

    mapping = {
        "meets": 20.0,
        "not_specified": 20.0,
        "partially_meets": 12.0,
        "insufficient_evidence": 10.0,
        "does_not_meet": 4.0,
    }
    return mapping.get(exp_analysis.status, 10.0)


def calculate_education_score(edu_analysis: EducationAnalysis, resume_is_empty: bool) -> float:
    """
    Calculate education match score out of 10 points:
    - meets: 10.0
    - not_specified: 10.0 (if resume has content)
    - partially_meets: 6.0
    - does_not_meet / empty resume: 0.0 - 2.0
    """
    if resume_is_empty:
        return 0.0

    mapping = {
        "meets": 10.0,
        "not_specified": 10.0,
        "partially_meets": 6.0,
        "does_not_meet": 2.0,
    }
    return mapping.get(edu_analysis.status, 6.0)


def calculate_formatting_score(resume_data: dict) -> float:
    """
    Evaluate structural ATS completeness out of 10 points:
    - Skills section present: 3.0 pts
    - Experience section present: 3.0 pts
    - Education section present: 2.0 pts
    - Projects section present: 2.0 pts
    """
    score = 0.0
    if resume_data.get("skills"):
        score += 3.0
    if resume_data.get("experience"):
        score += 3.0
    if resume_data.get("education"):
        score += 2.0
    if resume_data.get("projects"):
        score += 2.0
    return min(WEIGHT_FORMATTING, score)


def calculate_quality_score(resume_data: dict) -> float:
    """
    Evaluate basic quality and contact details out of 5 points:
    - Valid Email: 2.0 pts
    - Valid Phone: 1.0 pt
    - Professional links (LinkedIn / GitHub): 1.0 pt
    - Sufficient text length (> 150 words): 1.0 pt
    """
    score = 0.0
    if resume_data.get("email"):
        score += 2.0
    if resume_data.get("phone"):
        score += 1.0
    if resume_data.get("linkedin") or resume_data.get("github"):
        score += 1.0
    raw = resume_data.get("raw_text") or ""
    if len(raw.split()) >= 150:
        score += 1.0
    return min(WEIGHT_QUALITY, score)


def compute_overall_ats_score(
    skills_summary: Dict[str, Any],
    exp_analysis: ExperienceAnalysis,
    edu_analysis: EducationAnalysis,
    proj_analysis: ProjectRelevanceAnalysis,
    resume_data: dict,
) -> tuple[int, ScoreBreakdown]:
    """
    Assemble the complete score breakdown and compute the final 0-100 ATS score.
    """
    resume_is_empty = not any([
        resume_data.get("skills"),
        resume_data.get("experience"),
        resume_data.get("education"),
        resume_data.get("projects"),
        resume_data.get("raw_text"),
    ])

    kw_score = calculate_keyword_score(skills_summary)
    exp_score = calculate_experience_score(exp_analysis, resume_is_empty)
    edu_score = calculate_education_score(edu_analysis, resume_is_empty)
    proj_score = min(WEIGHT_PROJECT_RELEVANCE, max(0.0, proj_analysis.score))
    format_score = calculate_formatting_score(resume_data)
    qual_score = calculate_quality_score(resume_data)

    breakdown = ScoreBreakdown(
        keyword_match=ScoreComponent(score=kw_score, max_score=WEIGHT_KEYWORD_MATCH),
        experience_match=ScoreComponent(score=exp_score, max_score=WEIGHT_EXPERIENCE),
        education_match=ScoreComponent(score=edu_score, max_score=WEIGHT_EDUCATION),
        project_relevance=ScoreComponent(score=proj_score, max_score=WEIGHT_PROJECT_RELEVANCE),
        formatting=ScoreComponent(score=format_score, max_score=WEIGHT_FORMATTING),
        quality=ScoreComponent(score=qual_score, max_score=WEIGHT_QUALITY),
    )

    total_float = kw_score + exp_score + edu_score + proj_score + format_score + qual_score
    final_int = int(round(max(0.0, min(100.0, total_float))))

    return final_int, breakdown
