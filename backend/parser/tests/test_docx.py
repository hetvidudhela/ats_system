"""
test_docx.py
============

Tests for the DOCX parser module.

These tests check that the DOCX parser can:
    - Handle errors gracefully for invalid DOCX files
    - Return the correct result format

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_docx.py -v

NOTE:
    Some tests use sample DOCX files from the sample_resumes/ folder.
    If no sample DOCX files are available, those tests will be skipped.
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parsers.docx_parser import extract_text_from_docx


# Path to sample resumes
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_resumes")


# ==========================================
# TESTS: DOCX Parsing
# ==========================================

class TestDocxParser:
    """Tests for the DOCX text extraction function."""

    def test_invalid_docx_file(self, tmp_path):
        """Test that a non-DOCX file (just named .docx) returns an error."""
        # Create a fake DOCX file (just a text file renamed to .docx)
        fake_docx = os.path.join(str(tmp_path), "fake.docx")
        with open(fake_docx, "w") as f:
            f.write("This is not a real DOCX file")
        
        result = extract_text_from_docx(fake_docx)
        assert isinstance(result, dict)
        assert result["success"] == False
        assert result["error"] != ""

    def test_nonexistent_file(self):
        """Test that a file that doesn't exist returns an error."""
        result = extract_text_from_docx("/fake/path/no_file.docx")
        assert result["success"] == False
        assert result["error"] != ""

    def test_result_format(self, tmp_path):
        """Test that the result always has the expected keys."""
        fake_docx = os.path.join(str(tmp_path), "test.docx")
        with open(fake_docx, "w") as f:
            f.write("dummy")
        
        result = extract_text_from_docx(fake_docx)
        assert "success" in result
        assert "text" in result
        assert "error" in result

    def test_sample_docx_if_exists(self):
        """
        Test parsing a real sample DOCX if one exists.
        This test is skipped if no sample DOCX files are available.
        """
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample_resumes/ folder not found")
        
        # Find any DOCX file in the sample folder
        docx_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".docx")]
        
        if not docx_files:
            pytest.skip("No DOCX files found in sample_resumes/")
        
        # Test the first DOCX file found
        docx_path = os.path.join(SAMPLE_DIR, docx_files[0])
        result = extract_text_from_docx(docx_path)
        
        assert result["success"] == True
        assert len(result["text"]) > 0
        assert result["error"] == ""
