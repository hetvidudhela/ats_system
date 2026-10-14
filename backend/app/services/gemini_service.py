"""
gemini_service.py
=================
Service handling Gemini AI Assistant interactions and resume change validation.
Operates strictly as an advisory assistant; the deterministic ATS Engine remains
the sole source of truth for scoring and matching.
"""

import copy
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logger import logger
from app.models.ai import (
    AIChatMessage,
    AIChatRequest,
    AIChatResponse,
    ProposedChange,
)
from app.services.ats_service import ats_service
from app.models.response import AnalyzeResponse


GEMINI_SYSTEM_INSTRUCTION = """
You are the ATS Resume Intelligence AI Assistant.
Your job is to assist the candidate in understanding their ATS analysis results and improving their resume.

CRITICAL RULES & CONSTRAINTS:
1. THE EXISTING DETERMINISTIC ATS ENGINE IS THE SOLE SOURCE OF TRUTH.
   - Never invent, calculate, or estimate ATS scores.
   - Never override the ATS engine's matched skills, missing skills, or requirement status.
   - The actual score is always calculated by the backend ATS engine.

2. GROUNDING & ANTI-HALLUCINATION:
   - Answer ONLY using the supplied Resume Context, Job Description, and ATS Analysis Context.
   - Do NOT invent or fabricate: skills, experience, education, projects, certifications, employers, or dates.
   - If the resume does not provide evidence, explicitly state that there is insufficient evidence.
   - NEVER encourage false resume claims. If a user asks to add a skill they do not actually possess (e.g., "I don't know AWS but add it because JD requires it"), you MUST refuse:
     "I can't add a skill you don't actually possess. I can instead help you identify legitimate experience or learning steps that could strengthen your profile."

3. USER-CLAIMED SKILLS WORKFLOW:
   - If the user explicitly states they possess a skill/qualification that is missing from the submitted resume (e.g., "I actually know Docker but I forgot to mention it"), do NOT pretend the resume is already modified.
   - Respond politely stating that they indicated they have the experience, but it is currently absent from the submitted resume.
   - Ask if they would like to add the skill to the Skills section.
   - Emit a structured proposal in `proposed_changes`.
   - The user must explicitly approve before any change takes effect.

4. RESPONSE FORMAT:
   You MUST return a valid JSON object matching this exact schema:
   {
     "message": "Your clear, professional, markdown-formatted assistant response to the user.",
     "proposed_changes": [
       {
         "type": "add_skill",
         "section": "skills",
         "value": "ExactSkillName",
         "reason": "Brief explanation of why this change is proposed."
       }
     ]
   }
   If no change is proposed, `proposed_changes` must be an empty list [].
"""


class GeminiService:
    """
    Manages communication with Google's Gemini API and validates structured resume changes.
    """

    def __init__(self):
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL or "gemini-3.8-flash"

    def is_configured(self) -> bool:
        """Checks if a valid Gemini API key is configured."""
        api_key = settings.GEMINI_API_KEY
        return bool(api_key and api_key.strip())

    async def chat(self, request: AIChatRequest) -> AIChatResponse:
        """
        Sends user message and ATS context to Gemini and returns structured response.
        Fails gracefully if API key is missing or service is unavailable.
        """
        if not self.is_configured():
            logger.warning("Gemini AI Assistant requested but GEMINI_API_KEY is not configured.")
            return AIChatResponse(
                success=False,
                message="AI Assistant is currently unavailable. Please configure the Gemini API key in the backend environment.",
                proposed_changes=[],
                error="GEMINI_API_KEY not configured",
            )

        # Construct prompt containing context and recent conversation history
        context_prompt = self._build_context_prompt(request)

        # Model preference order: primary configured model, then available fallback
        models_to_try = [self._model]
        for fallback in ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.8-flash"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": context_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": GEMINI_SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }

        try:
            import asyncio
            response = None
            async with httpx.AsyncClient(timeout=30.0) as client:
                for model_candidate in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={settings.GEMINI_API_KEY}"
                    for attempt in range(2):
                        response = await client.post(url, json=payload)
                        if response.status_code in (503, 429):
                            if attempt == 0:
                                await asyncio.sleep(1.0)
                                continue
                            logger.warning(f"Model {model_candidate} unavailable ({response.status_code}), checking fallback...")
                            break
                        break
                    if response is not None and response.status_code == 200:
                        break

            if response is None or response.status_code != 200:
                status_code = response.status_code if response else "Unknown"
                err_text = response.text[:300] if response else ""
                logger.error(f"Gemini API returned status {status_code}: {err_text}")
                return AIChatResponse(
                    success=False,
                    message="The AI Assistant is currently experiencing high demand or is temporarily unavailable. Please try again shortly.",
                    proposed_changes=[],
                    error=f"Gemini API error ({status_code})",
                )


            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return AIChatResponse(
                    success=False,
                    message="The AI Assistant did not return a response.",
                    proposed_changes=[],
                    error="No candidates returned",
                )

            raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return self._parse_gemini_json_response(raw_text)

        except httpx.TimeoutException:
            logger.error("Gemini API request timed out.")
            return AIChatResponse(
                success=False,
                message="The AI Assistant request timed out. Please try asking again.",
                proposed_changes=[],
                error="Request timed out",
            )
        except Exception as e:
            logger.exception(f"Unexpected error in Gemini service: {e}")
            return AIChatResponse(
                success=False,
                message="An unexpected error occurred while communicating with the AI Assistant.",
                proposed_changes=[],
                error=str(e),
            )

    def _build_context_prompt(self, request: AIChatRequest) -> str:
        """Formats the context and user query into a structured prompt."""
        sections = []

        # 1. Job Description Summary
        jd = (request.job_description or "").strip()
        if jd:
            sections.append(f"### TARGET JOB DESCRIPTION:\n{jd[:2500]}")

        # 2. Parsed Resume Summary
        resume = request.resume_context or {}
        if resume:
            resume_summary = {
                "name": resume.get("name", ""),
                "skills": resume.get("skills", []),
                "experience": (resume.get("experience", "") or "")[:1200],
                "education": (resume.get("education", "") or "")[:600],
                "projects": (resume.get("projects", "") or "")[:800],
            }
            sections.append(f"### SUBMITTED RESUME DATA:\n{json.dumps(resume_summary, indent=2)}")

        # 3. ATS Analysis Context
        analysis = request.analysis_context or {}
        if analysis:
            analysis_summary = {
                "ats_score": analysis.get("score") or analysis.get("ats_score", 0),
                "matched_skills": analysis.get("matched_skills", []),
                "missing_skills": analysis.get("missing_skills", []),
                "required_missing": analysis.get("required_missing", []),
                "preferred_missing": analysis.get("preferred_missing", []),
                "suggestions": analysis.get("suggestions", []),
            }
            sections.append(f"### EXISTING ATS ANALYSIS (DETERMINISTIC SOURCE OF TRUTH):\n{json.dumps(analysis_summary, indent=2)}")

        # 4. Conversation History
        if request.conversation_history:
            history_lines = []
            # Keep up to the last 6 messages to maintain context without overloading
            for msg in request.conversation_history[-6:]:
                role = "User" if msg.role == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.content}")
            sections.append("### RECENT CONVERSATION HISTORY:\n" + "\n".join(history_lines))

        # 5. Current User Message
        sections.append(f"### CURRENT USER MESSAGE:\n{request.message}")

        return "\n\n".join(sections)

    def _parse_gemini_json_response(self, raw_text: str) -> AIChatResponse:
        """Safely parses structured JSON response from Gemini."""
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed = json.loads(clean_text)
            message = parsed.get("message", "I reviewed your resume context.")
            raw_changes = parsed.get("proposed_changes", [])

            valid_proposals = []
            for item in raw_changes:
                if isinstance(item, dict) and item.get("value"):
                    valid_proposals.append(
                        ProposedChange(
                            type=item.get("type", "add_skill"),
                            section=item.get("section", "skills"),
                            value=str(item.get("value", "")).strip(),
                            reason=item.get("reason", "User indicated possession of this skill."),
                        )
                    )

            return AIChatResponse(
                success=True,
                message=message,
                proposed_changes=valid_proposals,
            )
        except Exception as e:
            logger.warning(f"Could not parse Gemini JSON response directly: {e}. Raw text: {raw_text[:200]}")
            # Fallback: return raw text as message with no proposals
            return AIChatResponse(
                success=True,
                message=raw_text.strip(),
                proposed_changes=[],
            )

    def apply_approved_changes(
        self,
        original_resume: Dict[str, Any],
        approved_changes: List[ProposedChange],
        job_description: str,
    ) -> Tuple[Dict[str, Any], AnalyzeResponse]:
        """
        Validates and applies approved changes to create an updated resume representation,
        then invokes the EXISTING deterministic ATS engine to re-score.
        The original resume remains completely untouched.
        """
        # 1. Deep copy so original resume is never altered
        updated_resume = copy.deepcopy(original_resume) if isinstance(original_resume, dict) else {}

        # Ensure skills list and raw_text exist
        existing_skills = list(updated_resume.get("skills") or [])
        skills_lower_set = {s.lower().strip() for s in existing_skills if isinstance(s, str)}
        raw_text = str(updated_resume.get("raw_text") or "")

        added_skills = []

        # 2. Validate and apply each change
        for change in approved_changes:
            # Backend Validation:
            # - type must be 'add_skill'
            # - section must be 'skills'
            # - value must be non-empty string between 1 and 60 chars
            # - value must not contain malicious characters
            if change.type != "add_skill" or change.section != "skills":
                logger.warning(f"Rejected invalid proposed change type/section: {change}")
                continue

            cleaned_val = change.value.strip()
            if not cleaned_val or len(cleaned_val) > 60:
                logger.warning(f"Rejected invalid proposed skill value length: {change.value}")
                continue

            # Check for basic clean text (alphanumeric, plus, sharp, dot, dash, space)
            if not re.match(r"^[\w\s\.\+\#\-\/]+$", cleaned_val):
                logger.warning(f"Rejected potentially unsafe skill value: {cleaned_val}")
                continue

            # Add to skills list if not duplicate
            if cleaned_val.lower() not in skills_lower_set:
                existing_skills.append(cleaned_val)
                skills_lower_set.add(cleaned_val.lower())
                added_skills.append(cleaned_val)

        updated_resume["skills"] = existing_skills

        # 3. Augment raw_text with approved skills so full-text keyword matching finds them
        if added_skills:
            addition_note = "\n\nSkills Added via Candidate Confirmation: " + ", ".join(added_skills)
            updated_resume["raw_text"] = raw_text + addition_note

        # 4. Deterministic Re-scoring: Call EXISTING ATS engine
        report_dict = ats_service.analyze(
            parsed_resume=updated_resume,
            job_description=job_description,
        )

        analysis_response = AnalyzeResponse(
            success=report_dict.get("success", True),
            score=report_dict.get("score", 0),
            ats_score=report_dict.get("ats_score", 0),
            matched_skills=report_dict.get("matched_skills", []),
            missing_skills=report_dict.get("missing_skills", []),
            matched_keywords=report_dict.get("matched_keywords", []),
            missing_keywords=report_dict.get("missing_keywords", []),
            required_matched=report_dict.get("required_matched", []),
            required_missing=report_dict.get("required_missing", []),
            preferred_matched=report_dict.get("preferred_matched", []),
            preferred_missing=report_dict.get("preferred_missing", []),
            score_breakdown=report_dict.get("score_breakdown"),
            experience_analysis=report_dict.get("experience_analysis"),
            education_analysis=report_dict.get("education_analysis"),
            project_relevance=report_dict.get("project_relevance"),
            match_details=report_dict.get("match_details", []),
            suggestions=report_dict.get("suggestions", []),
            parsed_resume=updated_resume,
        )

        return updated_resume, analysis_response


gemini_service = GeminiService()
