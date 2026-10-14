"""
session.py
==========
Lightweight, in-memory session transfer API for seamless handoff between
the ATS Chrome Extension popup and the Flutter Web application.

Key Design Points:
- Thread-safe, memory-bounded, in-memory store.
- Cryptographically unpredictable UUIDv4 session identifiers.
- Short TTL (5 minutes) with automatic expiry cleanup.
- File bytes transported as sanitized Base64 payloads (up to 10MB).
- No permanent database or persistent file storage required.
"""

import base64
from pathlib import Path
import threading
import time
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, HTTPException, Path as FastPath, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/session",
    tags=["Session"],
)

SESSION_TTL_SECONDS = 300  # 5 minutes
MAX_SESSIONS_CAP = 100
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# In-memory session dictionary: session_id -> session_dict
_session_store: Dict[str, Dict[str, Any]] = {}
_store_lock = threading.Lock()


def _purge_expired_sessions_locked() -> None:
    """Remove expired sessions and enforce maximum capacity cap."""
    now = time.time()
    expired_keys = [
        sid for sid, data in _session_store.items()
        if now >= data.get("expires_at", 0)
    ]
    for sid in expired_keys:
        _session_store.pop(sid, None)

    # If still over capacity, evict oldest entries by creation time
    if len(_session_store) > MAX_SESSIONS_CAP:
        sorted_by_creation = sorted(
            _session_store.items(),
            key=lambda item: item[1].get("created_at", 0),
        )
        excess = len(_session_store) - MAX_SESSIONS_CAP
        for sid, _ in sorted_by_creation[:excess]:
            _session_store.pop(sid, None)


# -----------------------------------------------------------------------------
# Request & Response Models
# -----------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    version: int = Field(default=1, description="Schema version of the session transfer payload")
    filename: str = Field(..., description="Resume filename with extension")
    file_bytes: str = Field(..., description="Base64 encoded file contents")
    job_description: str = Field(default="", description="Target job description")
    analysis_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Completed ATS analysis report dictionary",
    )


class CreateSessionResponse(BaseModel):
    success: bool = True
    session_id: str
    expires_in_seconds: int


class GetSessionResponse(BaseModel):
    success: bool = True
    session_id: str
    version: int
    filename: str
    file_bytes: str
    job_description: str
    analysis_result: Optional[Dict[str, Any]] = None
    expires_in_seconds: int


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_session(payload: CreateSessionRequest) -> CreateSessionResponse:
    """
    Create a temporary in-memory session for transferring analysis data
    from the Chrome Extension to Flutter Web.
    """
    # 1. Sanitize and validate filename
    raw_filename = payload.filename.strip()
    safe_name = Path(raw_filename).name  # Prevent arbitrary directory traversal
    if not safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty.",
        )

    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported resume extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 2. Validate base64 payload size
    try:
        # Strip potential data URL prefix if provided
        b64_str = payload.file_bytes
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]

        decoded_sample = base64.b64decode(b64_str[:128], validate=True)
        # Calculate rough decoded size: len(b64) * 3 / 4
        estimated_size = (len(b64_str) * 3) // 4
        if estimated_size > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_BYTES // (1024 * 1024)}MB.",
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 encoding for file_bytes.",
        )

    # 3. Generate unpredictable session ID
    session_id = str(uuid.uuid4())
    now = time.time()
    expires_at = now + SESSION_TTL_SECONDS

    with _store_lock:
        _purge_expired_sessions_locked()
        _session_store[session_id] = {
            "version": payload.version,
            "filename": safe_name,
            "file_bytes": b64_str,
            "job_description": payload.job_description,
            "analysis_result": payload.analysis_result,
            "created_at": now,
            "expires_at": expires_at,
        }

    return CreateSessionResponse(
        success=True,
        session_id=session_id,
        expires_in_seconds=SESSION_TTL_SECONDS,
    )


@router.get("/{session_id}", response_model=GetSessionResponse)
@router.get("/{session_id}/", response_model=GetSessionResponse, include_in_schema=False)
def get_session(
    session_id: str = FastPath(..., description="Unique UUID session identifier")
) -> GetSessionResponse:
    """
    Retrieve and validate an active analysis session for Flutter Web restoration.
    """
    # Validate UUID syntax
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format. Must be a valid UUID.",
        )

    now = time.time()
    with _store_lock:
        _purge_expired_sessions_locked()
        session_data = _session_store.get(session_id)

        if not session_data or now >= session_data.get("expires_at", 0):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or has expired.",
            )

        remaining_ttl = max(0, int(session_data["expires_at"] - now))

        return GetSessionResponse(
            success=True,
            session_id=session_id,
            version=session_data["version"],
            filename=session_data["filename"],
            file_bytes=session_data["file_bytes"],
            job_description=session_data["job_description"],
            analysis_result=session_data["analysis_result"],
            expires_in_seconds=remaining_ttl,
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{session_id}/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_session(session_id: str):
    """Explicitly clean up a session after consumption."""
    with _store_lock:
        _session_store.pop(session_id, None)
    return None
