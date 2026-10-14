"""
test_ai_endpoints.py
====================
Comprehensive tests for the Gemini AI Assistant endpoints:
- /ai/status
- /ai/chat
- /ai/apply-changes
- Graceful handling when GEMINI_API_KEY is missing
- Anti-hallucination validation and deterministic re-scoring verification
"""

import copy
import json
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.gemini_service import gemini_service
from app.models.ai import ProposedChange


client = TestClient(app)

SAMPLE_RESUME = {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+1-555-0199",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Git"],
    "education": "Bachelor of Science in Computer Science, 2021",
    "experience": "Software Engineer with 3 years building REST APIs and microservices.",
    "projects": "Built an ATS analytics platform with Python and FastAPI.",
    "certifications": "",
    "languages": ["English"],
    "raw_text": "Jane Doe\nPython, FastAPI, PostgreSQL, Git\nSoftware Engineer with 3 years building REST APIs.",
}

SAMPLE_JD = """
Senior Backend Developer
Requirements:
- 3+ years experience with Python and FastAPI
- Strong database knowledge with PostgreSQL
- Experience with Docker and containerization required
- Experience with Redis caching
- BS in Computer Science or equivalent
"""


def test_ai_status_endpoint():
    """Verify /ai/status reports availability without exposing secrets."""
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "message" in data
    # Ensure no secret key is in response
    assert "AQ." not in str(data)
    assert "key" not in data or data.get("key") is None


def test_ai_chat_empty_message_validation():
    """Verify empty user message raises 400 Bad Request."""
    response = client.post("/api/ai/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_ai_chat_missing_key_graceful_handling():
    """Verify missing GEMINI_API_KEY returns graceful response rather than crashing."""
    with patch.object(settings, "GEMINI_API_KEY", None):
        response = client.post(
            "/api/ai/chat",
            json={
                "message": "Why is my ATS score low?",
                "job_description": SAMPLE_JD,
                "resume_context": SAMPLE_RESUME,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "unavailable" in data["message"].lower() or "configure" in data["message"].lower()
        assert data["proposed_changes"] == []


def test_ai_chat_structured_proposal_mock():
    """Verify structured response containing proposed changes for user-claimed skills."""
    mock_gemini_json = {
        "message": "You mentioned you have Docker experience, but Docker is missing from your submitted resume. Would you like to add it?",
        "proposed_changes": [
            {
                "type": "add_skill",
                "section": "skills",
                "value": "Docker",
                "reason": "User explicitly confirmed having Docker experience.",
            }
        ],
    }

    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(mock_gemini_json)}]
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with patch.object(settings, "GEMINI_API_KEY", "test-key-12345"):
            response = client.post(
                "/api/ai/chat",
                json={
                    "message": "I actually know Docker but I forgot to list it.",
                    "job_description": SAMPLE_JD,
                    "resume_context": SAMPLE_RESUME,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Docker" in data["message"]
            assert len(data["proposed_changes"]) == 1
            prop = data["proposed_changes"][0]
            assert prop["type"] == "add_skill"
            assert prop["value"] == "Docker"
            assert prop["section"] == "skills"



def test_apply_changes_validation_and_deterministic_rescore():
    """
    Verify:
    1. Original resume is NOT mutated.
    2. Updated resume representation contains the approved skill.
    3. ATS score and breakdown are recalculated by the EXISTING ATS engine.
    4. Deterministic score changes according to existing engine rules.
    """
    original_copy = copy.deepcopy(SAMPLE_RESUME)

    request_payload = {
        "original_resume": SAMPLE_RESUME,
        "approved_changes": [
            {
                "type": "add_skill",
                "section": "skills",
                "value": "Docker",
                "reason": "User confirmed Docker experience.",
            }
        ],
        "job_description": SAMPLE_JD,
    }

    response = client.post("/api/ai/apply-changes", json=request_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    updated_resume = data["updated_resume"]
    analysis_result = data["analysis_result"]

    # 1. Original resume must NOT be modified
    assert SAMPLE_RESUME == original_copy
    assert "Docker" not in SAMPLE_RESUME["skills"]

    # 2. Updated resume contains Docker
    assert "Docker" in updated_resume["skills"]

    # 3. New score and matched skills calculated deterministically
    assert "Docker" in analysis_result["matched_skills"]
    assert "Docker" not in analysis_result["missing_skills"]

    # 4. Deterministic score breakdown is populated
    assert analysis_result["score_breakdown"] is not None
    assert "keyword_match" in analysis_result["score_breakdown"]
    assert analysis_result["score"] >= 0


def test_apply_changes_sanitizes_unsafe_input():
    """Verify malicious or invalid proposed changes are sanitized / rejected."""
    request_payload = {
        "original_resume": SAMPLE_RESUME,
        "approved_changes": [
            {
                "type": "add_skill",
                "section": "skills",
                "value": "<script>alert('xss')</script>",
                "reason": "injection test",
            },
            {
                "type": "invalid_type",
                "section": "unknown",
                "value": "Hacker",
                "reason": "invalid type",
            },
            {
                "type": "add_skill",
                "section": "skills",
                "value": "Redis",
                "reason": "User knows Redis.",
            },
        ],
        "job_description": SAMPLE_JD,
    }

    response = client.post("/api/ai/apply-changes", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    updated_skills = data["updated_resume"]["skills"]

    # XSS script must NOT be added
    assert not any("<script>" in s for s in updated_skills)
    # Valid Redis skill MUST be added
    assert "Redis" in updated_skills


def test_real_gemini_integration_if_key_available():
    """
    If a real GEMINI_API_KEY is present in the environment,
    execute an actual live query to verify end-to-end connectivity.
    """

    if not gemini_service.is_configured():
        pytest.skip("No real GEMINI_API_KEY configured; skipping live API test.")

    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Why is my ATS score low and what skills am I missing from the JD?",
            "job_description": SAMPLE_JD,
            "resume_context": SAMPLE_RESUME,
            "analysis_context": {
                "score": 65,
                "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                "missing_skills": ["Docker", "Redis"],
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    if data["success"]:
        assert len(data["message"]) > 10
        # The response should mention missing skills such as Docker or Redis based on context
        msg_lower = data["message"].lower()
        assert "docker" in msg_lower or "redis" in msg_lower
    else:
        # Graceful handling when Gemini upstream is under temporary high demand
        assert "high demand" in data["message"].lower() or "unavailable" in data["message"].lower() or "error" in data["message"].lower()
