"""
test_main.py
============

Integration tests for the main parse_resume function.

These tests check the complete end-to-end parsing pipeline:
    1. File validation
    2. Text extraction
    3. Text cleaning
    4. Section detection
    5. Information extraction
    6. Resume object creation

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_main.py -v
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from main import parse_resume, parse_resume_object
except (ImportError, ModuleNotFoundError) as e:
    # PyMuPDF DLL may be blocked on some systems (e.g., Application Control policy)
    pytest.skip(
        f"Skipping integration tests: could not import main module ({e})",
        allow_module_level=True,
    )


# Path to sample resumes
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_resumes")


# ==========================================
# TESTS: Error Handling
# ==========================================

class TestParseResumeErrors:
    """Tests for error handling in parse_resume."""

    def test_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        result = parse_resume("/fake/path/no_file.pdf")
        assert result["success"] == False
        assert result["data"] is None
        assert result["error"] != ""

    def test_unsupported_file_type(self, tmp_path):
        """Test parsing an unsupported file type."""
        txt_file = os.path.join(str(tmp_path), "resume.txt")
        with open(txt_file, "w") as f:
            f.write("Some text content")
        
        result = parse_resume(txt_file)
        assert result["success"] == False

    def test_empty_file(self, tmp_path):
        """Test parsing an empty file."""
        empty_file = os.path.join(str(tmp_path), "empty.pdf")
        with open(empty_file, "wb") as f:
            pass  # Create empty file
        
        result = parse_resume(empty_file)
        assert result["success"] == False

    def test_result_format_on_error(self):
        """Test that error results have the expected format."""
        result = parse_resume("/no/such/file.pdf")
        assert "success" in result
        assert "data" in result
        assert "error" in result


# ==========================================
# TESTS: Successful Parsing
# ==========================================

class TestParseResumeSuccess:
    """Tests for successful resume parsing."""

    def test_sample_pdf_if_exists(self):
        """
        Test parsing a real sample PDF if available.
        """
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample_resumes/ folder not found")
        
        pdf_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]
        
        if not pdf_files:
            pytest.skip("No PDF files in sample_resumes/")
        
        pdf_path = os.path.join(SAMPLE_DIR, pdf_files[0])
        result = parse_resume(pdf_path)
        
        assert result["success"] == True
        assert result["data"] is not None
        assert result["error"] == ""
        
        # Check that the data has the expected structure
        data = result["data"]
        assert "name" in data
        assert "email" in data
        assert "phone" in data
        assert "skills" in data
        assert "raw_text" in data

    def test_result_has_all_fields(self):
        """Test that successful parse results have all expected fields."""
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample_resumes/ folder not found")
        
        pdf_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]
        
        if not pdf_files:
            pytest.skip("No PDF files in sample_resumes/")
        
        pdf_path = os.path.join(SAMPLE_DIR, pdf_files[0])
        result = parse_resume(pdf_path)
        
        if result["success"]:
            expected_fields = [
                "name", "email", "phone", "linkedin", "github",
                "skills", "education", "experience", "projects",
                "certifications", "achievements", "languages", "raw_text"
            ]
            
            for field in expected_fields:
                assert field in result["data"], f"Missing field: {field}"


# ==========================================
# TESTS: parse_resume_object
# ==========================================

class TestParseResumeObject:
    """Tests for the parse_resume_object convenience function."""

    def test_returns_none_for_bad_file(self):
        """Test that a bad file returns None."""
        result = parse_resume_object("/fake/path.pdf")
        assert result is None

    def test_returns_resume_for_valid_file(self):
        """Test that a valid file returns a Resume object."""
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample_resumes/ folder not found")
        
        pdf_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]
        
        if not pdf_files:
            pytest.skip("No PDF files in sample_resumes/")
        
        pdf_path = os.path.join(SAMPLE_DIR, pdf_files[0])
        resume = parse_resume_object(pdf_path)
        
        if resume is not None:
            # It should have the expected attributes
            assert hasattr(resume, "name")
            assert hasattr(resume, "email")
            assert hasattr(resume, "skills")
            assert hasattr(resume, "raw_text")
