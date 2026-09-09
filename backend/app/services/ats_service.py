"""
ats_service.py
==============
Service wrapper connecting FastAPI endpoints to the production ATS Engine.
Preserves existing public interface for backward compatibility.
"""

from typing import Any, Dict
from app.services.ats.engine import ATSEngine, analyze_resume_against_jd


class ATSService:
    """
    Service responsible for interacting with the ATS Engine.
    """

    def __init__(self):
        self._engine = ATSEngine()

    def analyze(
        self,
        parsed_resume: dict,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Analyze a parsed resume dictionary against a job description text.

        Args:
            parsed_resume: Dictionary produced by parser_service / parse_resume()
            job_description: Text of the target job posting

        Returns:
            Dictionary containing score, breakdown, matched/missing skills, and suggestions.
        """
        report = self._engine.analyze(parsed_resume, job_description)
        return report.to_dict()


ats_service = ATSService()