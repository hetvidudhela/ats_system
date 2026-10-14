"""
test_eligibility.py
===================
Comprehensive test suite for the ATS Eligibility Warning System:
1. ATS score strictly below 40%.
2. ATS score exactly 40% (does not trigger score rule alone).
3. Zero matching required skills.
4. Very low matching-skill ratio (< 25% when >= 3 required).
5. Mandatory education explicitly not fulfilled (confirmed mismatch).
6. Mandatory eligibility information missing or unverifiable.
7. Strong match with no detected eligibility issues.
8. Job description with no extractable skills handled gracefully.
9. Multiple reasons combined and deduplicated.
10. End-to-end endpoint verification with /analyze.
"""

from pathlib import Path
import sys
from typing import Dict, Any
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.ats.eligibility import (
    evaluate_candidate_eligibility,
    EligibilityAssessment,
    MIN_ATS_SCORE_THRESHOLD,
    LOW_SKILL_RATIO_THRESHOLD,
)
from app.services.ats.engine import analyze_resume_against_jd
from app.services.ats.models import EducationAnalysis, ExperienceAnalysis
from app.services.ats.jd_analyzer import JDAnalysis

client = TestClient(app)


def test_score_strictly_below_40_triggers_warning():
    """ATS score below 40% must trigger eligibility warning."""
    assessment = evaluate_candidate_eligibility(
        overall_score=38,
        skills_summary={"required_matched": ["Python"], "required_missing": []},
        exp_analysis={"status": "meets"},
        edu_analysis={"status": "not_specified"},
        jd_analysis=None,
    )

    assert assessment.warning is True
    assert assessment.eligible is False
    assert assessment.status == "potentially_ineligible"
    assert any("ATS score is 38%" in r for r in assessment.reasons)
    assert any("strictly below the 40% minimum threshold" in r for r in assessment.reasons)


def test_score_exactly_40_does_not_trigger_score_rule_alone():
    """ATS score exactly 40% should NOT trigger the score rule alone."""
    assessment = evaluate_candidate_eligibility(
        overall_score=40,
        skills_summary={"required_matched": ["Python", "FastAPI"], "required_missing": ["Docker"]},
        exp_analysis={"status": "meets"},
        edu_analysis={"status": "meets"},
        jd_analysis=JDAnalysis(all_skills=["Python", "FastAPI", "Docker"]),
    )

    assert assessment.warning is False
    assert assessment.eligible is True
    assert assessment.status == "no_major_issues_detected"
    assert len(assessment.reasons) == 0


def test_zero_matching_required_skills_triggers_warning():
    """Zero matched required skills must trigger eligibility warning."""
    assessment = evaluate_candidate_eligibility(
        overall_score=45,
        skills_summary={
            "required_matched": [],
            "required_missing": ["Python", "FastAPI", "PostgreSQL"],
        },
        exp_analysis={"status": "meets"},
        edu_analysis={"status": "meets"},
        jd_analysis=JDAnalysis(all_skills=["Python", "FastAPI", "PostgreSQL"]),
    )

    assert assessment.warning is True
    assert assessment.eligible is False
    assert assessment.status == "potentially_ineligible"
    assert any("Zero matching required skills (0 of 3" in r for r in assessment.reasons)


def test_very_low_matching_skill_ratio_triggers_warning():
    """Matched ratio < 25% when >= 3 required skills must trigger warning."""
    # 1 of 8 skills matched = 12.5% < 25%
    required_missing = ["Docker", "Kubernetes", "AWS", "FastAPI", "PostgreSQL", "Redis", "Kafka"]
    assessment = evaluate_candidate_eligibility(
        overall_score=42,
        skills_summary={
            "required_matched": ["Python"],
            "required_missing": required_missing,
        },
        exp_analysis={"status": "meets"},
        edu_analysis={"status": "meets"},
        jd_analysis=JDAnalysis(all_skills=["Python"] + required_missing),
    )

    assert assessment.warning is True
    assert assessment.eligible is False
    assert assessment.status == "potentially_ineligible"
    assert any("Very few required skills matched: only 1 of 8" in r for r in assessment.reasons)
    assert any("12%" in r or "13%" in r for r in assessment.reasons)


def test_mandatory_education_confirmed_mismatch():
    """Explicitly not fulfilling mandatory degree level triggers confirmed mismatch."""
    assessment = evaluate_candidate_eligibility(
        overall_score=65,
        skills_summary={"required_matched": ["Python", "SQL"], "required_missing": []},
        exp_analysis={"status": "meets"},
        edu_analysis=EducationAnalysis(
            status="does_not_meet",
            required_level="Master's Degree",
            detected_education="Diploma / Associate",
            details="Candidate has Diploma, whereas Master's is required.",
        ),
        jd_analysis=None,
    )

    assert assessment.warning is True
    assert assessment.eligible is False
    assert assessment.status == "potentially_ineligible"
    assert any("Candidate holds Diploma / Associate, which does not fulfill the mandatory Master's Degree requirement" in r for r in assessment.reasons)


def test_mandatory_education_unverified_missing():
    """Missing or unverifiable education triggers requirements_not_verified without claiming confirmed failure."""
    assessment = evaluate_candidate_eligibility(
        overall_score=60,
        skills_summary={"required_matched": ["Python", "FastAPI"], "required_missing": []},
        exp_analysis={"status": "meets"},
        edu_analysis=EducationAnalysis(
            status="does_not_meet",
            required_level="Bachelor's Degree",
            detected_education="None detected",
            details="No degree detected.",
        ),
        jd_analysis=None,
    )

    assert assessment.warning is True
    assert assessment.eligible is None  # Unverified / unknown
    assert assessment.status == "requirements_not_verified"
    assert any("Required Bachelor's Degree could not be verified from the resume" in r for r in assessment.reasons)


def test_mandatory_experience_confirmed_mismatch():
    """Detected experience confirmed below mandatory years triggers potentially_ineligible."""
    assessment = evaluate_candidate_eligibility(
        overall_score=50,
        skills_summary={"required_matched": ["Python"], "required_missing": []},
        exp_analysis=ExperienceAnalysis(
            status="does_not_meet",
            required_years=5.0,
            estimated_years=1.5,
            details="Candidate has 1.5 yrs, below required 5.0 yrs.",
        ),
        edu_analysis={"status": "meets"},
        jd_analysis=None,
    )

    assert assessment.warning is True
    assert assessment.eligible is False
    assert assessment.status == "potentially_ineligible"
    assert any("Candidate has approximately 1.5 years of experience, below the required 5.0 years" in r for r in assessment.reasons)


def test_mandatory_experience_unverified():
    """Unverifiable experience triggers requirements_not_verified."""
    assessment = evaluate_candidate_eligibility(
        overall_score=55,
        skills_summary={"required_matched": ["Python", "SQL"], "required_missing": []},
        exp_analysis=ExperienceAnalysis(
            status="insufficient_evidence",
            required_years=3.0,
            estimated_years=None,
            details="Could not calculate experience.",
        ),
        edu_analysis={"status": "meets"},
        jd_analysis=None,
    )

    assert assessment.warning is True
    assert assessment.eligible is None
    assert assessment.status == "requirements_not_verified"
    assert any("Required minimum experience (3.0 years) could not be verified from the resume" in r for r in assessment.reasons)


def test_strong_match_no_major_issues():
    """Strong candidate meeting all criteria should have no warnings."""
    assessment = evaluate_candidate_eligibility(
        overall_score=88,
        skills_summary={
            "required_matched": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "required_missing": [],
        },
        exp_analysis=ExperienceAnalysis(
            status="meets",
            required_years=3.0,
            estimated_years=4.5,
            details="Meets experience.",
        ),
        edu_analysis=EducationAnalysis(
            status="meets",
            required_level="Bachelor's Degree",
            detected_education="Bachelor's Degree",
            details="Meets education.",
        ),
        jd_analysis=JDAnalysis(all_skills=["Python", "FastAPI", "Docker", "PostgreSQL"]),
    )

    assert assessment.warning is False
    assert assessment.eligible is True
    assert assessment.status == "no_major_issues_detected"
    assert len(assessment.reasons) == 0


def test_jd_with_no_extractable_skills_handled_gracefully():
    """If JD contains no skills, candidate is not falsely flagged as having 0 matched skills."""
    assessment = evaluate_candidate_eligibility(
        overall_score=50,
        skills_summary={"required_matched": [], "required_missing": []},
        exp_analysis={"status": "not_specified"},
        edu_analysis={"status": "not_specified"},
        jd_analysis=JDAnalysis(all_skills=[]),
    )

    assert not any("0 of 0" in r for r in assessment.reasons)
    assert not any("Zero matching required skills" in r for r in assessment.reasons)


def test_multiple_reasons_combined_without_duplication():
    """Multiple failing criteria are all included cleanly without duplicate messages."""
    assessment = evaluate_candidate_eligibility(
        overall_score=25,  # Rule 1 (<40)
        skills_summary={
            "required_matched": [],
            "required_missing": ["React", "TypeScript", "Node.js"],
        },  # Rule 2 (0 matched)
        exp_analysis=ExperienceAnalysis(
            status="does_not_meet",
            required_years=5.0,
            estimated_years=1.0,
        ),  # Rule 3B (exp mismatch)
        edu_analysis=EducationAnalysis(
            status="does_not_meet",
            required_level="Master's Degree",
            detected_education="Bachelor's Degree",
        ),  # Rule 3A (edu mismatch)
        jd_analysis=JDAnalysis(all_skills=["React", "TypeScript", "Node.js"]),
    )

    assert assessment.warning is True
    assert assessment.eligible is False
    assert assessment.status == "potentially_ineligible"
    assert len(assessment.reasons) == 4
    # All unique
    assert len(assessment.reasons) == len(set(assessment.reasons))


def test_analyze_resume_against_jd_end_to_end_has_eligibility():
    """End-to-end engine report includes structured eligibility dictionary."""
    resume_data = {
        "raw_text": "Experienced Senior Python Engineer with 6 years experience in FastAPI, Docker, and PostgreSQL. Bachelor's in CS.",
        "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "education": "Bachelor of Science in Computer Science",
        "experience": "Senior Software Engineer (2018 - 2024)",
    }
    jd_text = """
    Senior Python Developer
    Requirements:
    - 5+ years of experience
    - Python, FastAPI, Docker, PostgreSQL
    - Bachelor's Degree in Computer Science
    """

    report = analyze_resume_against_jd(resume_data, jd_text)
    rep_dict = report.to_dict()

    assert "eligibility" in rep_dict
    elig = rep_dict["eligibility"]
    assert elig["warning"] is False
    assert elig["eligible"] is True
    assert elig["status"] == "no_major_issues_detected"
    assert isinstance(elig["reasons"], list)
