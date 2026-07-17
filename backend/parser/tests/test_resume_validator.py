"""
test_resume_validator.py
========================

Tests for the resume validator module.
Checks:
    - Normal resumes (students, experienced, etc.) are accepted.
    - Non-resumes (semester notes, research papers, textbooks, etc.) are rejected.
    - Edge cases (empty strings, minimal contact info, various thresholds) are handled correctly.
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validators.resume_validator import validate_resume_text
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx

# Path to sample resumes
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_resumes")


# ==========================================
# TEST CASES: VALID RESUMES
# ==========================================

class TestValidResumes:
    """Verify that actual resumes are successfully validated."""

    def test_mock_student_resume(self):
        """Test a typical student resume with projects, education, and skills."""
        text = """
        John Doe
        john.doe@email.com | (123) 456-7890 | github.com/johndoe
        
        EDUCATION
        Bachelor of Science in Computer Science - XYZ University (GPA: 3.8)
        
        TECHNICAL SKILLS
        Languages: Python, Java, SQL, HTML/CSS
        Tools: Git, Docker, VS Code
        
        PROJECTS
        Portfolio Website: Built a personal website using HTML, CSS, and JS.
        Database App: Created a library management system using Python and MySQL.
        """
        result = validate_resume_text(text)
        assert result["is_valid"] == True
        assert result["confidence_score"] >= 40
        assert result["indicators"]["email"] == True
        assert result["indicators"]["phone"] == True
        assert result["indicators"]["education"] == True
        assert result["indicators"]["skills"] == True
        assert result["indicators"]["projects"] == True

    def test_mock_experienced_resume(self):
        """Test a typical experienced resume with summary, experience, and certifications."""
        text = """
        Jane Smith
        jane.smith@email.com | +1-555-555-5555
        
        PROFESSIONAL SUMMARY
        Senior Software Engineer with 8+ years of experience leading teams and building scalable web apps.
        
        WORK EXPERIENCE
        Tech Corp - Lead Developer (2020 - Present)
        - Led a team of 5 engineers to build a new microservice architecture.
        - Improved application performance by 30%.
        
        CERTIFICATIONS
        AWS Certified Solutions Architect
        """
        result = validate_resume_text(text)
        assert result["is_valid"] == True
        assert result["confidence_score"] >= 40
        assert result["indicators"]["email"] == True
        assert result["indicators"]["phone"] == True
        assert result["indicators"]["experience"] == True
        assert result["indicators"]["summary"] == True
        assert result["indicators"]["certifications"] == True

    def test_real_docx_resume_if_exists(self):
        """Test with the actual sample docx resume if it exists."""
        docx_path = os.path.join(SAMPLE_DIR, "kirtan resume.docx")
        if not os.path.exists(docx_path):
            pytest.skip("kirtan resume.docx not found in sample_resumes")
            
        parse_result = extract_text_from_docx(docx_path)
        assert parse_result["success"] == True
        
        result = validate_resume_text(parse_result["text"])
        assert result["is_valid"] == True
        assert result["confidence_score"] >= 40


# ==========================================
# TEST CASES: INVALID DOCUMENTS
# ==========================================

class TestInvalidDocuments:
    """Verify that non-resume documents are rejected."""

    def test_mock_semester_notes(self):
        """Test text representing lecture/semester notes."""
        text = """
        BCA V Semester - Web Designing Study Notes
        Unit 3: Advanced CSS Layouts
        
        Today we covered Flexbox and Grid layout. 
        Flexbox is one-dimensional while Grid is two-dimensional.
        
        Review Questions:
        1. What is the difference between justify-content and align-items?
        2. How do you create a grid container?
        
        Assignment 3 due by next Friday. Marks obtained will be added to the final grade.
        """
        result = validate_resume_text(text)
        assert result["is_valid"] == False
        assert "does not appear to be a resume" in result["error"]

    def test_mock_research_paper(self):
        """Test text representing a research paper abstract page."""
        text = """
        A Novel Approach to ATS Scoring Using Rule-Based Parsers
        Dr. Alan Turing, Turing Institute (turing@inst.edu)
        Dr. Grace Hopper, Hopper Lab (hopper@lab.org)
        
        Abstract:
        This paper introduces a fast, deterministic method for evaluating resumes.
        Using simple line cleaning and exact match, we achieve high accuracy.
        
        Keywords: Parser, ATS, Regular Expression, Rule-based.
        
        1. Introduction
        Traditional parsers rely on heavy AI models. In this work, we propose...
        """
        result = validate_resume_text(text)
        # Should be rejected because it lacks standard resume headings like Education, Experience, Skills, etc.
        assert result["is_valid"] == False
        assert result["confidence_score"] < 40

    def test_real_sem_5_marksheet(self):
        """Test that the sem-5.pdf marksheet is correctly rejected."""
        pdf_path = os.path.join(SAMPLE_DIR, "sem-5.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("sem-5.pdf not found in sample_resumes")
            
        parse_result = extract_text_from_pdf(pdf_path)
        assert parse_result["success"] == True
        
        result = validate_resume_text(parse_result["text"])
        assert result["is_valid"] == False
        assert "does not appear to be a resume" in result["error"]


# ==========================================
# TEST CASES: EDGE CASES & CONFIGURATION
# ==========================================

class TestEdgeCases:
    """Test validation boundary conditions and custom configurations."""

    def test_empty_text(self):
        """Test empty or whitespace-only text is rejected."""
        result = validate_resume_text("")
        assert result["is_valid"] == False
        assert result["confidence_score"] == 0

        result = validate_resume_text("   \n  \t  ")
        assert result["is_valid"] == False
        assert result["confidence_score"] == 0

    def test_minimal_resume_with_custom_threshold(self):
        """Test that validation respects custom threshold parameter."""
        # Text with only contact details (30 + 10 = 40 points)
        text = "contact@me.com | 9876543210"
        
        # Passes with threshold <= 40
        result_pass = validate_resume_text(text, threshold=30)
        assert result_pass["is_valid"] == True
        
        # Fails with threshold > 40
        result_fail = validate_resume_text(text, threshold=50)
        assert result_fail["is_valid"] == False
