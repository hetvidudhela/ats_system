"""
ai.py
=====
Pydantic data models for the optional Gemini AI Assistant.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.response import AnalyzeResponse


class ProposedChange(BaseModel):
    """
    Structured proposal for a resume modification.
    Requires explicit user approval before application.
    """
    type: str = Field("add_skill", description="Type of change, e.g. 'add_skill'")
    section: str = Field("skills", description="Target resume section, e.g. 'skills'")
    value: str = Field(..., description="The value to be added or modified, e.g. 'Docker'")
    reason: str = Field(..., description="Explanation/justification for the proposed change")


class AIChatMessage(BaseModel):
    """Message item in the conversation history."""
    role: str = Field(..., description="'user' or 'assistant' or 'model'")
    content: str = Field(..., description="Message text content")


class AIChatRequest(BaseModel):
    """Request payload for POST /api/ai/chat."""
    message: str = Field(..., description="User query or input message")
    resume_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured parsed resume data"
    )
    job_description: Optional[str] = Field(
        default="",
        description="Target job description text"
    )
    analysis_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current ATS analysis report (scores, matched/missing skills)"
    )
    conversation_history: Optional[List[AIChatMessage]] = Field(
        default_factory=list,
        description="Recent conversation history messages for context"
    )


class AIChatResponse(BaseModel):
    """Structured response from the Gemini AI Assistant."""
    success: bool = True
    message: str = Field(..., description="Assistant textual response")
    proposed_changes: List[ProposedChange] = Field(
        default_factory=list,
        description="List of structured changes requiring user approval"
    )
    error: Optional[str] = None


class AIApplyChangesRequest(BaseModel):
    """Request payload for applying user-approved changes."""
    original_resume: Dict[str, Any] = Field(
        ...,
        description="Original parsed resume dictionary"
    )
    approved_changes: List[ProposedChange] = Field(
        ...,
        description="List of user-approved structured changes"
    )
    job_description: str = Field(
        ...,
        description="Target job description text"
    )


class AIApplyChangesResponse(BaseModel):
    """Response returned after applying changes and re-running deterministic ATS analysis."""
    success: bool = True
    updated_resume: Dict[str, Any] = Field(
        ...,
        description="Updated structured resume representation"
    )
    analysis_result: AnalyzeResponse = Field(
        ...,
        description="New deterministic ATS report computed by the ATS engine"
    )
    error: Optional[str] = None
