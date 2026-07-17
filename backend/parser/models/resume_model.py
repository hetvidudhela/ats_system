"""
resume_model.py
===============

WHY THIS FILE EXISTS:
    This file defines the Resume data model.
    It holds all the structured information extracted from a resume.
    
    When parsing is done, all data goes into a Resume object.
    This object can then be easily converted into JSON for the FastAPI backend.

HOW IT CONNECTS:
    - main.py creates a Resume object after all parsing is done.
    - info_extractor.py fills in fields like name, email, phone.
    - section_detector.py fills in sections like skills, education, experience.
    - FastAPI backend receives the JSON version of this object.
"""

import json


class Resume:
    """
    A simple class to hold all resume data in one place.
    
    This is NOT a complex class. It's basically a container
    that holds all the fields we extract from a resume.
    """

    def __init__(self):
        """Initialize all resume fields with empty default values."""
        
        # --- Personal Information ---
        self.name = ""
        self.email = ""
        self.phone = ""
        self.linkedin = ""
        self.github = ""

        # --- Resume Sections ---
        self.skills = []           # List of skills found
        self.education = ""        # Education section text
        self.experience = ""       # Experience section text
        self.projects = ""         # Projects section text
        self.certifications = ""   # Certifications section text
        self.achievements = ""     # Achievements section text
        self.languages = []        # List of languages found

        # --- Raw Data ---
        self.raw_text = ""         # The full cleaned text from the resume

    def to_dict(self):
        """
        Convert the Resume object into a Python dictionary.
        
        This is useful when we want to convert the resume data
        into JSON format for the API response.
        
        Returns:
            dict: A dictionary with all resume fields.
        """
        resume_dict = {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "linkedin": self.linkedin,
            "github": self.github,
            "skills": self.skills,
            "education": self.education,
            "experience": self.experience,
            "projects": self.projects,
            "certifications": self.certifications,
            "achievements": self.achievements,
            "languages": self.languages,
            "raw_text": self.raw_text,
        }
        return resume_dict

    def to_json(self):
        """
        Convert the Resume object into a JSON string.
        
        Returns:
            str: A nicely formatted JSON string.
        """
        resume_dict = self.to_dict()
        # indent=4 makes the JSON look clean and readable
        json_string = json.dumps(resume_dict, indent=4, ensure_ascii=False)
        return json_string

    def __str__(self):
        """
        A readable string version of the Resume.
        Useful for printing and debugging.
        """
        output = "===== PARSED RESUME =====\n"
        output += f"Name        : {self.name}\n"
        output += f"Email       : {self.email}\n"
        output += f"Phone       : {self.phone}\n"
        output += f"LinkedIn    : {self.linkedin}\n"
        output += f"GitHub      : {self.github}\n"
        output += f"Skills      : {', '.join(self.skills) if self.skills else 'Not found'}\n"
        output += f"Languages   : {', '.join(self.languages) if self.languages else 'Not found'}\n"
        output += f"Education   : {'Found' if self.education else 'Not found'}\n"
        output += f"Experience  : {'Found' if self.experience else 'Not found'}\n"
        output += f"Projects    : {'Found' if self.projects else 'Not found'}\n"
        output += f"Certificates: {'Found' if self.certifications else 'Not found'}\n"
        output += f"Achievements: {'Found' if self.achievements else 'Not found'}\n"
        output += "========================="
        return output
