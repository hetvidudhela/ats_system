"""
test_resume_model.py
====================

Tests for the Resume data model.

Tests cover:
    - Default initialization
    - to_dict() conversion
    - to_json() conversion
    - __str__() representation

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_resume_model.py -v
"""

import os
import sys
import json
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.resume_model import Resume


# ==========================================
# TESTS: Resume Model
# ==========================================

class TestResumeModel:
    """Tests for the Resume class."""

    def test_default_values(self):
        """Test that a new Resume has empty default values."""
        resume = Resume()
        assert resume.name == ""
        assert resume.email == ""
        assert resume.phone == ""
        assert resume.linkedin == ""
        assert resume.github == ""
        assert resume.skills == []
        assert resume.education == ""
        assert resume.experience == ""
        assert resume.projects == ""
        assert resume.certifications == ""
        assert resume.achievements == ""
        assert resume.languages == []
        assert resume.raw_text == ""

    def test_setting_values(self):
        """Test that we can set values on a Resume object."""
        resume = Resume()
        resume.name = "John Doe"
        resume.email = "john@email.com"
        resume.skills = ["Python", "Java"]
        
        assert resume.name == "John Doe"
        assert resume.email == "john@email.com"
        assert resume.skills == ["Python", "Java"]

    def test_to_dict(self):
        """Test converting Resume to a dictionary."""
        resume = Resume()
        resume.name = "Jane Smith"
        resume.email = "jane@email.com"
        resume.skills = ["SQL", "Python"]
        
        result = resume.to_dict()
        
        assert isinstance(result, dict)
        assert result["name"] == "Jane Smith"
        assert result["email"] == "jane@email.com"
        assert result["skills"] == ["SQL", "Python"]

    def test_to_dict_has_all_keys(self):
        """Test that to_dict() includes all expected keys."""
        resume = Resume()
        result = resume.to_dict()
        
        expected_keys = [
            "name", "email", "phone", "linkedin", "github",
            "skills", "education", "experience", "projects",
            "certifications", "achievements", "languages", "raw_text"
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_to_json(self):
        """Test converting Resume to JSON string."""
        resume = Resume()
        resume.name = "Test User"
        
        json_string = resume.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_string)
        assert parsed["name"] == "Test User"

    def test_to_json_is_formatted(self):
        """Test that JSON output is nicely formatted (indented)."""
        resume = Resume()
        json_string = resume.to_json()
        
        # Indented JSON should have newlines
        assert "\n" in json_string

    def test_str_representation(self):
        """Test the string representation of Resume."""
        resume = Resume()
        resume.name = "John Doe"
        resume.email = "john@email.com"
        
        text = str(resume)
        assert "John Doe" in text
        assert "john@email.com" in text
        assert "PARSED RESUME" in text
