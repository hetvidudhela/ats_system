"""
test_section_detector.py
========================

Tests for the section detection module.

Tests cover:
    - Detecting standard section headings
    - Detecting alternate section heading variations
    - Ignoring long lines (not headings)
    - Handling empty text
    - Extracting content between sections

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_section_detector.py -v
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ..extractor.section_detector import (
    detect_sections,
    match_section_heading,
    find_section_positions,
)


# ==========================================
# TESTS: Section Heading Matching
# ==========================================

class TestMatchSectionHeading:
    """Tests for matching individual section headings."""

    # ----- Skills variations -----
    def test_skills_heading(self):
        assert match_section_heading("Skills") == "skills"

    def test_technical_skills_heading(self):
        assert match_section_heading("Technical Skills") == "skills"

    def test_key_skills_heading(self):
        assert match_section_heading("Key Skills") == "skills"

    def test_core_skills_heading(self):
        assert match_section_heading("Core Skills") == "skills"

    # ----- Education variations -----
    def test_education_heading(self):
        assert match_section_heading("Education") == "education"

    def test_academic_background_heading(self):
        assert match_section_heading("Academic Background") == "education"

    def test_qualification_heading(self):
        assert match_section_heading("Qualification") == "education"

    # ----- Experience variations -----
    def test_experience_heading(self):
        assert match_section_heading("Experience") == "experience"

    def test_work_experience_heading(self):
        assert match_section_heading("Work Experience") == "experience"

    def test_professional_experience_heading(self):
        assert match_section_heading("Professional Experience") == "experience"

    def test_employment_history_heading(self):
        assert match_section_heading("Employment History") == "experience"

    # ----- Projects variations -----
    def test_projects_heading(self):
        assert match_section_heading("Projects") == "projects"

    def test_academic_projects_heading(self):
        assert match_section_heading("Academic Projects") == "projects"

    def test_personal_projects_heading(self):
        assert match_section_heading("Personal Projects") == "projects"

    # ----- Certifications variations -----
    def test_certifications_heading(self):
        assert match_section_heading("Certifications") == "certifications"

    def test_certificates_heading(self):
        assert match_section_heading("Certificates") == "certifications"

    # ----- Achievements variations -----
    def test_achievements_heading(self):
        assert match_section_heading("Achievements") == "achievements"

    def test_accomplishments_heading(self):
        assert match_section_heading("Accomplishments") == "achievements"

    # ----- Case insensitivity -----
    def test_uppercase_heading(self):
        assert match_section_heading("SKILLS") == "skills"

    def test_mixed_case_heading(self):
        assert match_section_heading("SkIlLs") == "skills"

    # ----- Headings with punctuation -----
    def test_heading_with_colon(self):
        assert match_section_heading("Skills:") == "skills"

    def test_heading_with_dashes(self):
        assert match_section_heading("--- Skills ---") == "skills"

    # ----- Non-heading lines -----
    def test_long_line_not_heading(self):
        """Lines with more than 6 words should not be detected as headings."""
        long_line = "I have many technical skills in software development"
        assert match_section_heading(long_line) is None

    def test_empty_line_not_heading(self):
        assert match_section_heading("") is None

    def test_random_text_not_heading(self):
        assert match_section_heading("Python is a programming language") is None


# ==========================================
# TESTS: Section Position Finding
# ==========================================

class TestFindSectionPositions:
    """Tests for finding section positions in a list of lines."""

    def test_finds_single_section(self):
        lines = ["John Doe", "Skills", "Python, Java"]
        positions = find_section_positions(lines)
        assert len(positions) == 1
        assert positions[0]["section"] == "skills"
        assert positions[0]["line_number"] == 1

    def test_finds_multiple_sections(self):
        lines = [
            "John Doe",
            "Skills",
            "Python, Java",
            "Education",
            "B.Tech CS",
        ]
        positions = find_section_positions(lines)
        assert len(positions) == 2
        section_names = [p["section"] for p in positions]
        assert "skills" in section_names
        assert "education" in section_names

    def test_no_sections_found(self):
        lines = ["Just some random text", "More text here"]
        positions = find_section_positions(lines)
        assert len(positions) == 0


# ==========================================
# TESTS: Full Section Detection
# ==========================================

class TestDetectSections:
    """Tests for the complete detect_sections function."""

    def test_detects_skills_section(self):
        text = "John Doe\nSkills\nPython, Java, SQL\nEducation\nB.Tech"
        sections = detect_sections(text)
        assert "Python" in sections["skills"]
        assert "Java" in sections["skills"]

    def test_detects_education_section(self):
        text = "Education\nB.Tech in Computer Science\nXYZ University"
        sections = detect_sections(text)
        assert "B.Tech" in sections["education"]

    def test_detects_experience_section(self):
        text = "Work Experience\nSoftware Developer at ABC Corp\n2020-2023"
        sections = detect_sections(text)
        assert "Software Developer" in sections["experience"]

    def test_empty_text_returns_empty_sections(self):
        sections = detect_sections("")
        assert sections["skills"] == ""
        assert sections["education"] == ""
        assert sections["experience"] == ""

    def test_multiple_sections_detected(self):
        text = (
            "John Doe\n"
            "Skills\n"
            "Python, Java\n"
            "Education\n"
            "B.Tech CS\n"
            "Experience\n"
            "Developer at XYZ\n"
            "Projects\n"
            "Project Alpha"
        )
        sections = detect_sections(text)
        assert sections["skills"] != ""
        assert sections["education"] != ""
        assert sections["experience"] != ""
        assert sections["projects"] != ""
