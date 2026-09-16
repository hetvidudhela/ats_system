"""
test_api_endpoints.py
======================
Comprehensive verification test suite for FastAPI backend endpoints:
- /health/ and /health
- /version/ and /version
- CORS configuration
- /analyze/ and /analyze (PDF, DOCX, invalid files, empty/short JD, response contract)
"""

import io
import os
import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app


BACKEND_DIR = Path(__file__).resolve().parent.parent
SAMPLE_PDF = BACKEND_DIR / "parser" / "sample_resumes" / "sample_resume.pdf"
SAMPLE_DOCX = BACKEND_DIR / "parser" / "sample_resumes" / "Harshit_Gandhi_Resume_v2 (3) (1).docx"

REALISTIC_JD = """
Senior Full Stack Engineer

About the Role:
We are seeking an experienced Senior Software Engineer to build scalable backend services
and modern web applications.

Requirements:
- Strong proficiency in Python and FastAPI
- Hands-on experience with Docker and PostgreSQL
- Solid understanding of REST API design and Git
- Familiarity with React or modern frontend frameworks
- 2+ years of software development experience
- Bachelor's degree in Computer Science or a related technical discipline

Nice to Have:
- Experience with AWS or cloud deployments
- Automated CI/CD pipelines
"""

client = TestClient(app)


# =====================================================================
# 1. Health and Version Endpoints
# =====================================================================

def test_health_endpoint_with_slash():
    response = client.get("/health/", follow_redirects=False)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "running" in data["message"].lower()


def test_health_endpoint_without_slash():
    response = client.get("/health", follow_redirects=False)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_version_endpoint_with_slash():
    response = client.get("/version/", follow_redirects=False)
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "ATS Backend"
    assert "version" in data


def test_version_endpoint_without_slash():
    response = client.get("/version", follow_redirects=False)
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "ATS Backend"


# =====================================================================
# 2. CORS Preflight and Origin Validation
# =====================================================================

def test_cors_preflight_flutter_web():
    """Verify CORS headers respond correctly to legacy Flutter Web origin."""
    flutter_web_origin = "http://localhost:5000"
    response = client.options(
        "/analyze/",
        headers={
            "Origin": flutter_web_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == flutter_web_origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_flutter_web_port_57720():
    """Verify CORS headers respond correctly to extension-bound Flutter Web port 57720."""
    flutter_web_origin = "http://localhost:57720"
    response = client.options(
        "/analyze/",
        headers={
            "Origin": flutter_web_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == flutter_web_origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"



def test_cors_preflight_chrome_extension():
    """Verify CORS headers respond correctly to Chrome Extension origin."""
    extension_origin = "chrome-extension://abcdefghijklmnop"
    response = client.options(
        "/analyze/",
        headers={
            "Origin": extension_origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == extension_origin


# =====================================================================
# 3. POST /analyze/ with Valid Files and Realistic JD
# =====================================================================

def test_analyze_valid_pdf():
    """Verify POST /analyze/ with a valid PDF and realistic JD."""
    assert SAMPLE_PDF.exists(), f"Sample PDF missing at {SAMPLE_PDF}"

    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description": REALISTIC_JD},
        )

    assert response.status_code == 200
    data = response.json()

    # Core response status
    assert data["success"] is True

    # ATS score (0 to 100)
    assert isinstance(data["score"], int)
    assert 0 <= data["score"] <= 100
    assert data["ats_score"] == data["score"]

    # Skills analysis
    assert isinstance(data["matched_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert len(data["matched_skills"]) > 0
    assert "Python" in data["matched_skills"]
    assert "Docker" in data["matched_skills"]
    assert "PostgreSQL" in data["matched_skills"]

    # Keywords
    assert isinstance(data["matched_keywords"], list)
    assert isinstance(data["missing_keywords"], list)

    # Score breakdown
    breakdown = data.get("score_breakdown")
    assert breakdown is not None
    required_components = [
        "keyword_match",
        "experience_match",
        "education_match",
        "project_relevance",
        "formatting",
        "quality",
    ]
    for comp in required_components:
        assert comp in breakdown, f"Missing {comp} in score_breakdown"
        assert "score" in breakdown[comp]
        assert "max_score" in breakdown[comp]
        assert breakdown[comp]["score"] >= 0

    # Experience analysis
    exp = data.get("experience_analysis")
    assert exp is not None
    assert "status" in exp
    assert "details" in exp

    # Education analysis
    edu = data.get("education_analysis")
    assert edu is not None
    assert "status" in edu
    assert "details" in edu

    # Project relevance
    proj = data.get("project_relevance")
    assert proj is not None
    assert "score" in proj
    assert "max_score" in proj
    assert "matched_technologies" in proj

    # Suggestions
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0

    # Parsed resume
    parsed = data.get("parsed_resume")
    assert parsed is not None
    assert parsed.get("name") == "John Doe"
    assert "Python" in parsed.get("skills", [])
    assert parsed.get("email") == "john.doe@example.com"


def test_analyze_valid_docx():
    """Verify POST /analyze/ with a valid DOCX and realistic JD."""
    assert SAMPLE_DOCX.exists(), f"Sample DOCX missing at {SAMPLE_DOCX}"

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

    with open(SAMPLE_DOCX, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"job_description": jd},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert 0 <= data["score"] <= 100
    assert "Python" in data["matched_skills"]
    assert "SQL" in data["matched_skills"]
    assert data["score_breakdown"] is not None
    assert isinstance(data["suggestions"], list)
    assert data["parsed_resume"] is not None


# =====================================================================
# 4. Route Flexibility (No 307 Redirects)
# =====================================================================

def test_analyze_without_trailing_slash():
    """Verify POST /analyze works directly without redirect."""
    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/analyze",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description": REALISTIC_JD},
            follow_redirects=False,
        )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_api_analyze_prefix():
    """Verify POST /api/analyze/ also works seamlessly."""
    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/api/analyze/",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description": REALISTIC_JD},
            follow_redirects=False,
        )
    assert response.status_code == 200
    assert response.json()["success"] is True


# =====================================================================
# 5. Error and Edge Cases
# =====================================================================

def test_analyze_unsupported_file_extension():
    """Verify rejection of unsupported file types (.txt)."""
    response = client.post(
        "/analyze/",
        files={"resume": ("document.txt", io.BytesIO(b"Hello plain text"), "text/plain")},
        data={"job_description": REALISTIC_JD},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_empty_job_description():
    """Verify rejection when job_description is empty."""
    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description": ""},
        )
    assert response.status_code == 400
    assert "Job description is required" in response.json()["detail"]


def test_analyze_whitespace_job_description():
    """Verify rejection when job_description is only whitespace."""
    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description": "   \n\t   "},
        )
    assert response.status_code == 400
    assert "Job description is required" in response.json()["detail"]


def test_analyze_short_job_description():
    """Verify rejection when job_description is under 15 characters."""
    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/analyze/",
            files={"resume": ("sample_resume.pdf", f, "application/pdf")},
            data={"job_description": "Short JD"},
        )
    assert response.status_code == 400
    assert "too short" in response.json()["detail"].lower()


def test_analyze_missing_file():
    """Verify 422 when no file is attached."""
    response = client.post(
        "/analyze/",
        data={"job_description": REALISTIC_JD},
    )
    assert response.status_code == 422


def test_analyze_corrupt_file_cleanup():
    """Verify that a corrupted PDF returns 400 and cleans up temporary uploads."""
    response = client.post(
        "/analyze/",
        files={"resume": ("corrupt.pdf", io.BytesIO(b"garbage not pdf content"), "application/pdf")},
        data={"job_description": REALISTIC_JD},
    )
    assert response.status_code == 400

    # Verify upload directory is clean
    upload_dir = BACKEND_DIR / "uploads"
    if upload_dir.exists():
        files = list(upload_dir.iterdir())
        assert len(files) == 0, f"Temporary file leak detected: {files}"
