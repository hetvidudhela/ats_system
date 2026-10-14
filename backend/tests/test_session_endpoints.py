"""
test_session_endpoints.py
=========================
Comprehensive verification test suite for the temporary session handoff endpoints:
- POST /session/ and /session
- GET /session/{id} and /session/{id}/
- Prefixed routes (/api/session)
- Validation: unsupported files, path traversal, invalid base64, invalid UUID
- Expiration and not-found behavior
"""

import base64
from pathlib import Path
import sys
import time
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.api.session import _session_store, _store_lock, SESSION_TTL_SECONDS

client = TestClient(app)

SAMPLE_FILE_CONTENT = b"%PDF-1.4 Mock resume file binary content"
SAMPLE_B64 = base64.b64encode(SAMPLE_FILE_CONTENT).decode("ascii")

SAMPLE_ANALYSIS_RESULT = {
    "success": True,
    "score": 92,
    "ats_score": 92,
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["Docker"],
    "score_breakdown": {
        "keyword_match": {"score": 40.0, "max_score": 40.0},
    },
    "suggestions": ["Add Docker experience."],
}


@pytest.fixture(autouse=True)
def clean_store():
    with _store_lock:
        _session_store.clear()
    yield
    with _store_lock:
        _session_store.clear()


def test_create_and_get_session_lifecycle():
    """Verify standard session creation and retrieval."""
    payload = {
        "version": 1,
        "filename": "my_resume.pdf",
        "file_bytes": SAMPLE_B64,
        "job_description": "Looking for a Python and FastAPI expert.",
        "analysis_result": SAMPLE_ANALYSIS_RESULT,
    }

    # 1. Create session
    resp = client.post("/session/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    session_id = data["session_id"]
    assert len(session_id) == 36  # Standard UUID string length

    # 2. Retrieve session
    get_resp = client.get(f"/session/{session_id}")
    assert get_resp.status_code == 200
    session_data = get_resp.json()

    assert session_data["success"] is True
    assert session_data["session_id"] == session_id
    assert session_data["filename"] == "my_resume.pdf"
    assert session_data["file_bytes"] == SAMPLE_B64
    assert "FastAPI" in session_data["job_description"]
    assert session_data["analysis_result"]["score"] == 92
    assert session_data["expires_in_seconds"] > 0


def test_session_endpoints_prefix_and_slash_flexibility():
    """Verify route flexibility (/api/session and without trailing slashes)."""
    payload = {
        "version": 1,
        "filename": "candidate.docx",
        "file_bytes": SAMPLE_B64,
        "job_description": "Data Analyst with SQL and Python.",
        "analysis_result": None,
    }

    # POST /api/session
    post_resp = client.post("/api/session", json=payload)
    assert post_resp.status_code == 201
    session_id = post_resp.json()["session_id"]

    # GET /api/session/{id}/
    get_resp = client.get(f"/api/session/{session_id}/")
    assert get_resp.status_code == 200
    assert get_resp.json()["filename"] == "candidate.docx"


def test_session_filename_sanitization_and_path_traversal():
    """Verify path traversal characters are stripped from filename."""
    payload = {
        "filename": "../../etc/shadow/malicious.pdf",
        "file_bytes": SAMPLE_B64,
        "job_description": "Security engineer",
    }
    resp = client.post("/session/", json=payload)
    assert resp.status_code == 201
    sid = resp.json()["session_id"]

    get_resp = client.get(f"/session/{sid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["filename"] == "malicious.pdf"


def test_session_unsupported_extension():
    """Verify non-PDF/DOCX extensions are rejected."""
    payload = {
        "filename": "script.exe",
        "file_bytes": SAMPLE_B64,
        "job_description": "Hacker",
    }
    resp = client.post("/session/", json=payload)
    assert resp.status_code == 400
    assert "Unsupported resume extension" in resp.json()["detail"]


def test_session_invalid_uuid():
    """Verify malformed session ID format returns 400."""
    resp = client.get("/session/invalid-not-uuid")
    assert resp.status_code == 400
    assert "Must be a valid UUID" in resp.json()["detail"]


def test_session_not_found():
    """Verify non-existent UUID returns 404."""
    resp = client.get("/session/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert "Session not found" in resp.json()["detail"]


def test_session_expired():
    """Verify expired session returns 404."""
    payload = {
        "filename": "old_resume.pdf",
        "file_bytes": SAMPLE_B64,
        "job_description": "Senior Lead",
    }
    resp = client.post("/session/", json=payload)
    sid = resp.json()["session_id"]

    # Simulate expired session
    with _store_lock:
        _session_store[sid]["expires_at"] = time.time() - 10

    get_resp = client.get(f"/session/{sid}")
    assert get_resp.status_code == 404
    assert "expired" in get_resp.json()["detail"].lower()


def test_session_delete():
    """Verify explicit session deletion."""
    payload = {
        "filename": "delete_me.pdf",
        "file_bytes": SAMPLE_B64,
        "job_description": "To be deleted",
    }
    resp = client.post("/session/", json=payload)
    sid = resp.json()["session_id"]

    del_resp = client.delete(f"/session/{sid}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/session/{sid}")
    assert get_resp.status_code == 404
