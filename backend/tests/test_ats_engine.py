"""
test_ats_engine.py
==================
Comprehensive test suite for the ATS Analysis Engine.
Validates normalization, matching, false positive prevention, scoring,
edge cases, deterministic outputs, and FastAPI integration.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.services.ats.engine import ATSEngine, analyze_resume_against_jd
from app.services.ats.normalizer import (
    resolve_canonical_skill,
    get_display_name,
    normalize_token,
)
from app.services.ats.scorer import (
    WEIGHT_KEYWORD_MATCH,
    WEIGHT_EXPERIENCE,
    WEIGHT_PROJECT_RELEVANCE,
    WEIGHT_EDUCATION,
    WEIGHT_FORMATTING,
    WEIGHT_QUALITY,
    TOTAL_WEIGHT,
)


@pytest.fixture
def engine():
    return ATSEngine()


# ==========================================
# 1. NORMALIZATION & MATCHING TESTS
# ==========================================

def test_exact_skill_match(engine):
    resume = {"skills": ["Python", "FastAPI"], "raw_text": "Python FastAPI"}
    jd = "Python Developer\nRequirements:\n- Python\n- FastAPI"
    report = engine.analyze(resume, jd)
    assert "Python" in report.matched_skills
    assert "FastAPI" in report.matched_skills
    assert not report.missing_skills


def test_case_insensitive_match(engine):
    resume = {"skills": ["python", "fastapi"], "raw_text": "python fastapi"}
    jd = "Requirements:\n- PYTHON\n- FastAPI"
    report = engine.analyze(resume, jd)
    assert "Python" in report.matched_skills
    assert "FastAPI" in report.matched_skills


def test_alias_match(engine):
    # 'postgres' and 'reactjs' in resume should match 'PostgreSQL' and 'React' in JD
    resume = {"skills": ["postgres", "reactjs"], "raw_text": "postgres reactjs"}
    jd = "Requirements:\n- PostgreSQL\n- React"
    report = engine.analyze(resume, jd)
    assert "PostgreSQL" in report.matched_skills
    assert "React" in report.matched_skills


def test_fuzzy_match(engine):
    # Slight typing variations should match if >= 90%
    resume = {"skills": ["PostgreSql"], "raw_text": "PostgreSql"}
    jd = "Requirements:\n- PostgreSQL"
    report = engine.analyze(resume, jd)
    assert "PostgreSQL" in report.matched_skills


# ==========================================
# 2. FALSE POSITIVE PREVENTION
# ==========================================

def test_false_positive_java_vs_javascript(engine):
    # Candidate with only Java must NOT match JavaScript
    resume = {"skills": ["Java"], "raw_text": "Experienced Java backend developer."}
    jd = "Frontend Role\nRequirements:\n- JavaScript"
    report = engine.analyze(resume, jd)
    assert "JavaScript" in report.missing_skills
    assert "JavaScript" not in report.matched_skills


def test_false_positive_c_vs_ordinary_words(engine):
    # A resume containing words like 'cat', 'career', 'concept' must NOT match C language
    resume = {"skills": ["HTML", "CSS"], "raw_text": "Cat enthusiast with a great career and solid concepts."}
    jd = "Systems Engineer\nRequirements:\n- C\n- HTML"
    report = engine.analyze(resume, jd)
    assert "C" in report.missing_skills
    assert "HTML" in report.matched_skills


def test_false_positive_react_vs_react_native(engine):
    # React Native must not be satisfied merely by standard React
    resume = {"skills": ["React"], "raw_text": "React web developer with Redux."}
    jd = "Mobile Engineer\nRequirements:\n- React Native"
    report = engine.analyze(resume, jd)
    assert "React Native" in report.missing_skills


def test_false_positive_sql_vs_unrelated_text(engine):
    # SQL must not match substrings inside unrelated English words
    resume = {"skills": [], "raw_text": "Squealing tires and masquerade ball."}
    jd = "Database Admin\nRequirements:\n- SQL"
    report = engine.analyze(resume, jd)
    assert "SQL" in report.missing_skills


def test_negative_intent_exclusion(engine):
    # Candidate expressing interest in learning Django should not be credited with having Django
    resume = {
        "skills": ["Python"],
        "experience": "Interested in learning Django in the future.",
        "raw_text": "Interested in learning Django in the future.",
    }
    jd = "Backend Developer\nRequirements:\n- Python\n- Django"
    report = engine.analyze(resume, jd)
    assert "Python" in report.matched_skills
    assert "Django" in report.missing_skills


# ==========================================
# 3. REQUIRED VS PREFERRED SKILLS
# ==========================================

def test_required_skill_missing_vs_preferred_missing(engine):
    jd = """
    Software Engineer
    Required Skills:
    - Python
    - FastAPI
    Preferred Skills:
    - Docker
    """
    # Candidate has Python and Docker (missing required FastAPI)
    resume1 = {"skills": ["Python", "Docker"], "raw_text": "Python Docker"}
    # Candidate has Python and FastAPI (missing preferred Docker)
    resume2 = {"skills": ["Python", "FastAPI"], "raw_text": "Python FastAPI"}

    report1 = engine.analyze(resume1, jd)
    report2 = engine.analyze(resume2, jd)

    # Missing required skill should result in a lower score than missing preferred skill
    assert report2.ats_score > report1.ats_score
    assert "FastAPI" in report1.required_missing
    assert "Docker" in report2.preferred_missing


def test_all_skills_matched(engine):
    resume = {
        "skills": ["Python", "FastAPI", "Docker"],
        "experience": "3 years of Python and FastAPI development.",
        "education": "B.Tech Computer Science",
        "projects": "Built cloud backend with Docker and FastAPI.",
        "email": "test@example.com",
        "phone": "+1234567890",
        "raw_text": "Full resume text with comprehensive details...",
    }
    jd = """
    Requirements:
    - Python
    - FastAPI
    - Docker
    """
    report = engine.analyze(resume, jd)
    assert not report.missing_skills
    assert len(report.matched_skills) == 3
    assert report.ats_score >= 85


def test_no_skills_matched(engine):
    resume = {
        "skills": ["Photoshop", "Illustrator"],
        "raw_text": "Graphic designer with Adobe suite skills.",
    }
    jd = """
    Backend Engineer
    Requirements:
    - Python
    - FastAPI
    - PostgreSQL
    """
    report = engine.analyze(resume, jd)
    assert len(report.matched_skills) == 0
    assert len(report.missing_skills) == 3
    assert report.ats_score < 40


# ==========================================
# 4. EDGE CASES & INPUT VALIDATION
# ==========================================

def test_empty_jd(engine):
    resume = {"skills": ["Python"]}
    report = engine.analyze(resume, "")
    assert not report.success
    assert report.ats_score == 0
    assert "provide a comprehensive job description" in report.suggestions[0].lower()


def test_short_jd(engine):
    resume = {"skills": ["Python"]}
    report = engine.analyze(resume, "Hiring dev")
    assert not report.success
    assert report.ats_score == 0


def test_empty_resume(engine):
    jd = "Requirements:\n- Python\n- FastAPI"
    report = engine.analyze({}, jd)
    assert report.success
    assert "Python" in report.missing_skills
    assert report.ats_score < 30


def test_duplicate_skills_in_resume(engine):
    resume = {
        "skills": ["Python", "python", "Python 3"],
        "experience": "Python, Python, Python",
        "raw_text": "Python Python Python",
    }
    jd = "Requirements:\n- Python"
    report = engine.analyze(resume, jd)
    # Matched skills list should not contain duplicates
    assert report.matched_skills == ["Python"]


# ==========================================
# 5. EXPERIENCE & EDUCATION MATCHING
# ==========================================

def test_experience_requirement_meets(engine):
    resume = {
        "skills": ["Python"],
        "experience": "3 years of backend engineering experience at ABC Corp.",
        "raw_text": "3 years of backend engineering experience at ABC Corp.",
    }
    jd = "Requirements:\n- Python\n- 2+ years of experience"
    report = engine.analyze(resume, jd)
    assert report.experience_analysis["status"] == "meets"


def test_experience_requirement_does_not_meet(engine):
    resume = {
        "skills": ["Python"],
        "experience": "1 year working with Python.",
        "raw_text": "1 year working with Python.",
    }
    jd = "Senior Role\nRequirements:\n- Python\n- 5+ years of experience"
    report = engine.analyze(resume, jd)
    assert report.experience_analysis["status"] == "does_not_meet"


def test_education_requirement_meets(engine):
    resume = {
        "skills": ["Python"],
        "education": "Master of Computer Applications (MCA), Gujarat University",
        "raw_text": "Master of Computer Applications (MCA)",
    }
    jd = "Requirements:\n- Python\n- Bachelor's degree in Computer Science"
    report = engine.analyze(resume, jd)
    assert report.education_analysis["status"] == "meets"


def test_education_dates_never_counted_as_work_experience_regression(engine):
    """
    Regression Test:
    A resume with Education (BCA 2022-2025, MCA 2025-Present) and Projects (TrueHire - ongoing),
    but NO work experience section, must NEVER have education dates counted as 4.0 years of experience.
    Expected:
    - experience status == 'insufficient_evidence'
    - experience score != 20/20 (must NOT receive full 20.0 points)
    - estimated_years is None
    """
    resume = {
        "skills": ["Python", "FastAPI"],
        "education": "BCA 2022–2025\nMCA 2025–Present",
        "projects": "TrueHire – ongoing\nAI-Powered Job Hiring Platform",
        "raw_text": "Education:\nBCA 2022–2025\nMCA 2025–Present\n\nProjects:\nTrueHire – ongoing\nAI-Powered Job Hiring Platform",
    }
    jd = "Software Engineer\nRequirements:\n- Python\n- 4 years of experience"
    report = engine.analyze(resume, jd)

    assert report.experience_analysis["status"] == "insufficient_evidence"
    assert report.experience_analysis["estimated_years"] is None
    assert report.score_breakdown["experience_match"]["score"] < 20.0
    assert report.score_breakdown["experience_match"]["score"] == 10.0
    assert "approximately 4.0 years" not in report.experience_analysis["details"]


def test_genuine_work_experience_with_explicit_dates(engine):
    """
    Verify that genuine work experience with explicit dates is calculated accurately,
    and that education dates in the same resume do not bleed into work experience tenure.
    """
    resume = {
        "skills": ["Python", "FastAPI"],
        "education": "Bachelor of Computer Applications (BCA) 2018 - 2021",
        "experience": "Software Engineer at TechCorp\n2020 - 2024\nDeveloped scalable backend microservices.",
        "projects": "TrueHire – ongoing\nAI-Powered Job Hiring Platform",
        "raw_text": "Full resume text...",
    }
    jd = "Backend Developer\nRequirements:\n- Python\n- 4 years of experience"
    report = engine.analyze(resume, jd)

    assert report.experience_analysis["status"] == "meets"
    assert report.experience_analysis["estimated_years"] == 4.0
    assert report.score_breakdown["experience_match"]["score"] == 20.0
    assert "approximately 4.0 years of experience, meeting the required 4.0 years" in report.experience_analysis["details"]


def test_project_duration_and_technologies_never_create_work_experience(engine):
    """
    Verify that project duration and technologies in project descriptions
    never automatically create years of professional experience.
    """
    resume = {
        "skills": ["Python", "Docker"],
        "projects": "Major Project TrueHire (2021 - 2025)\nBuilt full-stack AI platform using Python, FastAPI, and Docker.",
        "raw_text": "Projects:\nMajor Project TrueHire (2021 - 2025)\nBuilt full-stack AI platform using Python, FastAPI, and Docker.",
    }
    jd = "Senior Developer\nRequirements:\n- Python\n- 4 years of experience"
    report = engine.analyze(resume, jd)

    assert report.experience_analysis["status"] == "insufficient_evidence"
    assert report.experience_analysis["estimated_years"] is None
    assert report.score_breakdown["experience_match"]["score"] < 20.0


def test_real_kirtan_and_milan_pdf_resumes_experience_isolation(engine):
    """
    Test the actual real PDF files:
    - kirtan resume.pdf has BCA 2022-2025 and MCA 2025-Present in Education and TrueHire in Projects,
      with NO work experience section.
    - Milankumar_Rawal_Resume.pdf has Education and no work experience.
    Both must evaluate to 'insufficient_evidence' and must NOT receive 20/20 experience points.
    """
    from parser.main import parse_resume

    kirtan_pdf = os.path.join(BACKEND_DIR, "parser", "sample_resumes", "kirtan resume.pdf")
    milan_pdf = os.path.join(BACKEND_DIR, "parser", "sample_resumes", "Milankumar_Rawal_Resume.pdf")
    jd = "Senior Software Engineer\nRequirements:\n- Python\n- 4 years of experience"

    if os.path.exists(kirtan_pdf):
        kirtan_data = parse_resume(kirtan_pdf)["data"]
        kirtan_report = engine.analyze(kirtan_data, jd)
        assert kirtan_report.experience_analysis["status"] == "insufficient_evidence"
        assert kirtan_report.experience_analysis["estimated_years"] is None
        assert kirtan_report.score_breakdown["experience_match"]["score"] == 10.0
        assert "approximately 4.0 years" not in kirtan_report.experience_analysis["details"]

    if os.path.exists(milan_pdf):
        milan_data = parse_resume(milan_pdf)["data"]
        milan_report = engine.analyze(milan_data, jd)
        assert milan_report.experience_analysis["status"] == "insufficient_evidence"
        assert milan_report.experience_analysis["estimated_years"] is None
        assert milan_report.score_breakdown["experience_match"]["score"] == 10.0


# ==========================================
# 6. PROJECT RELEVANCE & KEYWORDS
# ==========================================

def test_project_relevance_matching(engine):
    resume = {
        "skills": ["Python"],
        "projects": "Created a real-time messaging system with WebSockets and Redis.",
        "raw_text": "Created a real-time messaging system with WebSockets and Redis.",
    }
    jd = "Requirements:\n- Python\n- Redis\n- WebSockets"
    report = engine.analyze(resume, jd)
    # Redis and WebSockets were in projects, so project relevance should capture them
    assert report.project_relevance["score"] > 0
    assert "Redis" in report.project_relevance["matched_technologies"]
    assert "WebSockets" in report.project_relevance["matched_technologies"]


# ==========================================
# 7. DETERMINISTIC SCORING & WEIGHTS
# ==========================================

def test_weight_total_equals_100():
    assert TOTAL_WEIGHT == 100.0
    assert WEIGHT_KEYWORD_MATCH == 40.0
    assert WEIGHT_EXPERIENCE == 20.0
    assert WEIGHT_PROJECT_RELEVANCE == 15.0
    assert WEIGHT_EDUCATION == 10.0
    assert WEIGHT_FORMATTING == 10.0
    assert WEIGHT_QUALITY == 5.0


def test_score_always_bounded_0_to_100(engine):
    jd = "Requirements:\n- Python\n- FastAPI\n- 2+ years exp"
    # Perfectly matched
    good_resume = {
        "skills": ["Python", "FastAPI"],
        "experience": "3 years experience",
        "education": "B.Tech Computer Science",
        "projects": "Built REST API in FastAPI",
        "email": "test@example.com",
        "phone": "+1234567890",
        "raw_text": "Word " * 200,
    }
    good_report = engine.analyze(good_resume, jd)
    assert 0 <= good_report.ats_score <= 100

    # Terrible resume
    bad_report = engine.analyze({}, jd)
    assert 0 <= bad_report.ats_score <= 100


def test_deterministic_reproducibility(engine):
    resume = {
        "skills": ["Flutter", "Dart", "Firebase"],
        "experience": "2 years developing mobile apps",
        "projects": "Built chat app with Firebase and Flutter",
        "education": "BCA",
        "email": "test@example.com",
    }
    jd = "Flutter Developer\nRequirements:\n- Flutter\n- Dart\n- Firebase\n- 2+ years"

    report1 = engine.analyze(resume, jd)
    report2 = engine.analyze(resume, jd)

    assert report1.ats_score == report2.ats_score
    assert report1.score_breakdown == report2.score_breakdown
    assert report1.matched_skills == report2.matched_skills
    assert report1.missing_skills == report2.missing_skills


# ==========================================
# 8. PROMPT REALISTIC TEST CASE (Part 22)
# ==========================================

def test_prompt_realistic_flutter_test_case(engine):
    jd = """
    Flutter Developer

    Requirements:
    - Flutter
    - Dart
    - Firebase
    - REST API
    - Git
    - Provider
    - MVVM
    - 2+ years experience
    - Bachelor's degree in Computer Science or related field
    """

    resume = {
        "skills": ["Flutter", "Dart", "Firebase", "Git", "SQL"],
        "experience": "2 years developing Flutter applications.",
        "projects": "Built a Flutter application using Firebase and REST APIs.",
        "education": "B.Tech Computer Science",
        "email": "flutter.dev@example.com",
        "phone": "+1234567890",
        "linkedin": "linkedin.com/in/flutterdev",
        "raw_text": "Cleaned text...",
    }

    report = engine.analyze(resume, jd)

    # Matched verification
    assert "Flutter" in report.matched_skills
    assert "Dart" in report.matched_skills
    assert "Firebase" in report.matched_skills
    assert "Git" in report.matched_skills
    assert "REST API" in report.matched_skills

    # Missing verification
    assert "Provider" in report.missing_skills
    assert "MVVM" in report.missing_skills

    # Experience & Education
    assert report.experience_analysis["status"] == "meets"
    assert report.education_analysis["status"] == "meets"

    # Score calculation
    assert 70 <= report.ats_score <= 90


# ==========================================
# 9. FASTAPI ENDPOINT INTEGRATION
# ==========================================

def test_api_analyze_endpoint():
    client = TestClient(app)
    sample_file = os.path.join(BACKEND_DIR, "parser", "sample_resumes", "Harshit_Gandhi_Resume_v2 (3) (1).docx")
    assert os.path.exists(sample_file), f"Sample file not found at {sample_file}"

    jd = """
    Data Analyst
    Requirements:
    - Python
    - SQL
    - Power BI
    - Excel
    - 1+ years experience
    - Bachelor's degree
    """

    with open(sample_file, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"job_description": jd},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["score"] > 70
    assert "Python" in data["matched_skills"]
    assert "SQL" in data["matched_skills"]
    assert data["score_breakdown"] is not None
    assert isinstance(data["suggestions"], list)


def test_api_analyze_empty_jd_rejected():
    client = TestClient(app)
    sample_file = os.path.join(BACKEND_DIR, "parser", "sample_resumes", "Harshit_Gandhi_Resume_v2 (3) (1).docx")

    with open(sample_file, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"job_description": ""},
        )

    assert response.status_code == 400
    assert "Job description is required" in response.json()["detail"]
