class ATSService:
    """
    Service responsible for interacting with the ATS Engine.
    """

    def analyze(
        self,
        parsed_resume: dict,
        job_description: str,
    ) -> dict:
        """
        Temporary dummy ATS analysis.

        Later this method will call Member 2's ATS engine.
        """

        return {
            "success": True,
            "score": 85,
            "matched_skills": [
                "Python",
                "FastAPI",
            ],
            "missing_skills": [
                "Docker",
                "AWS",
            ],
            "suggestions": [
                "Add Docker experience.",
                "Mention cloud projects.",
            ],
        }


ats_service = ATSService()