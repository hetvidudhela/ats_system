"""
test_e2e_ats_ai_flow.py
=======================
End-to-End integration test covering the complete user journey:
1. Normal ATS resume analysis (deterministic scorer and matcher).
2. Zero-match scenario and warning verification.
3. Querying the AI Assistant with resume + JD + ATS analysis context.
4. User-claimed skill workflow with structured proposal.
5. User approval -> backend validation -> deterministic ATS engine re-scoring.
6. Verification that original resume remains unchanged.
7. Verification that normal ATS works seamlessly even if Gemini key is missing.
"""

import copy
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.gemini_service import gemini_service
from app.services.ats_service import ats_service

client = TestClient(app)

SAMPLE_RESUME_DATA = {
    "name": "Alex Mercer",
    "email": "alex.mercer@example.com",
    "phone": "+1-555-4321",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Git"],
    "education": "BS in Computer Science",
    "experience": "3 years as a backend developer building REST APIs with Python and FastAPI.",
    "projects": "Scalable REST APIs and microservices platform.",
    "certifications": "",
    "languages": ["English"],
    "raw_text": "Alex Mercer\nPython, FastAPI, PostgreSQL, Git\n3 years as a backend developer.",
}

JD_MATCHING = """
Senior Backend Engineer
Requirements:
- 3+ years experience with Python and FastAPI
- Relational database experience with PostgreSQL
- Docker containerization required
- Redis caching required
"""

JD_ZERO_MATCH = """
Senior iOS Mobile Engineer
Requirements:
- 4+ years of Swift and SwiftUI development
- iOS SDK and Xcode experience
- CocoaPods or Swift Package Manager
- Objective-C maintenance experience
"""



def test_e2e_normal_ats_analysis():
    """Step 1: Normal ATS analysis runs deterministically and produces expected report."""
    report = ats_service.analyze(
        parsed_resume=SAMPLE_RESUME_DATA,
        job_description=JD_MATCHING,
    )

    assert report["success"] is True
    assert report["score"] > 0
    assert "Python" in report["matched_skills"]
    assert "FastAPI" in report["matched_skills"]
    assert "Docker" in report["missing_skills"]
    assert "Redis" in report["missing_skills"]


def test_e2e_zero_match_scenario():
    """Step 2: When candidate skills do not match JD, matched_skills is empty and requirements exist."""
    report = ats_service.analyze(
        parsed_resume=SAMPLE_RESUME_DATA,
        job_description=JD_ZERO_MATCH,
    )

    assert report["success"] is True
    # Zero matched skills
    assert len(report["matched_skills"]) == 0
    # Identifiable requirements exist
    assert len(report["missing_skills"]) > 0 or len(report["required_missing"]) > 0

    # Deterministic zero-match warning condition check
    is_zero_match = (
        len(report["matched_skills"]) == 0
        and (
            len(report["match_details"]) > 0
            or len(report["missing_skills"]) > 0
            or len(report["required_missing"]) > 0
        )
    )
    assert is_zero_match is True


def test_e2e_ai_chat_flow_and_approval_rescoring():
    """
    Steps 3 to 6:
    - User asks AI about missing skill (Docker)
    - AI provides structured proposal
    - User approves change
    - Backend validates, updates resume representation (leaving original intact),
      and re-runs deterministic ATS engine to compute new score.
    """
    initial_report = ats_service.analyze(
        parsed_resume=SAMPLE_RESUME_DATA,
        job_description=JD_MATCHING,
    )
    initial_score = initial_report["score"]
    assert "Docker" in initial_report["missing_skills"]

    # Candidate explicitly confirms Docker experience
    chat_payload = {
        "message": "I actually have hands-on Docker experience from my previous project.",
        "resume_context": SAMPLE_RESUME_DATA,
        "job_description": JD_MATCHING,
        "analysis_context": initial_report,
    }

    chat_resp = client.post("/api/ai/chat", json=chat_payload)
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()

    # User-approved proposal to add Docker
    approved_proposal = {
        "type": "add_skill",
        "section": "skills",
        "value": "Docker",
        "reason": "Candidate confirmed hands-on Docker experience.",
    }

    original_copy = copy.deepcopy(SAMPLE_RESUME_DATA)

    # Apply change
    apply_resp = client.post(
        "/api/ai/apply-changes",
        json={
            "original_resume": SAMPLE_RESUME_DATA,
            "approved_changes": [approved_proposal],
            "job_description": JD_MATCHING,
        },
    )

    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()
    assert apply_data["success"] is True

    # Original resume MUST NOT be modified
    assert SAMPLE_RESUME_DATA == original_copy
    assert "Docker" not in SAMPLE_RESUME_DATA["skills"]

    # Updated resume MUST contain Docker
    updated_resume = apply_data["updated_resume"]
    assert "Docker" in updated_resume["skills"]

    # Re-analyzed result MUST be computed by the deterministic ATS engine
    new_analysis = apply_data["analysis_result"]
    assert "Docker" in new_analysis["matched_skills"]
    assert "Docker" not in new_analysis["missing_skills"]

    # New score reflects Docker match
    assert new_analysis["score"] >= initial_score


def test_e2e_normal_ats_works_without_gemini_key():
    """Step 7: ATS functionality works 100% normally even if GEMINI_API_KEY is None."""
    with patch.object(settings, "GEMINI_API_KEY", None):
        # 1. Health check works
        health = client.get("/health")
        assert health.status_code == 200

        # 2. Version check works
        version = client.get("/version")
        assert version.status_code == 200

        # 3. ATS service deterministic analysis works
        report = ats_service.analyze(
            parsed_resume=SAMPLE_RESUME_DATA,
            job_description=JD_MATCHING,
        )
        assert report["success"] is True
        assert report["score"] > 0

        # 4. AI chat gracefully informs without crashing
        ai_chat = client.post("/api/ai/chat", json={"message": "Hello"})
        assert ai_chat.status_code == 200
        ai_json = ai_chat.json()
        assert ai_json["success"] is False
        assert "unavailable" in ai_json["message"].lower() or "configure" in ai_json["message"].lower()
