"""
test_pdf.py
===========

Tests for the PDF parser module.

These tests check that the PDF parser can:
    - Successfully extract text from valid PDF files
    - Handle errors gracefully for invalid PDF files
    - Return the correct result format

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_pdf.py -v

NOTE:
    Some tests use sample PDF files from the sample_resumes/ folder.
    If no sample PDFs are available, those tests will be skipped.
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parsers.pdf_parser import extract_text_from_pdf


# Path to sample resumes
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_resumes")


# ==========================================
# TESTS: PDF Parsing
# ==========================================

class TestPdfParser:
    """Tests for the PDF text extraction function."""

    def test_invalid_pdf_file(self, tmp_path):
        """Test that a non-PDF file (just named .pdf) returns an error."""
        # Create a fake PDF file (just a text file renamed to .pdf)
        fake_pdf = os.path.join(str(tmp_path), "fake.pdf")
        with open(fake_pdf, "w") as f:
            f.write("This is not a real PDF file")
        
        result = extract_text_from_pdf(fake_pdf)
        # It should either fail or return empty text
        # (depends on how PyMuPDF handles it)
        assert isinstance(result, dict)
        assert "success" in result
        assert "text" in result
        assert "error" in result

    def test_nonexistent_file(self):
        """Test that a file that doesn't exist returns an error."""
        result = extract_text_from_pdf("/fake/path/no_file.pdf")
        assert result["success"] == False
        assert result["error"] != ""

    def test_result_format(self, tmp_path):
        """Test that the result always has the expected keys."""
        fake_pdf = os.path.join(str(tmp_path), "test.pdf")
        with open(fake_pdf, "w") as f:
            f.write("dummy")
        
        result = extract_text_from_pdf(fake_pdf)
        assert "success" in result
        assert "text" in result
        assert "error" in result

    def test_sample_pdf_if_exists(self):
        """
        Test parsing a real sample PDF if one exists.
        This test is skipped if no sample PDFs are available.
        """
        if not os.path.exists(SAMPLE_DIR):
            pytest.skip("sample_resumes/ folder not found")
        
        # Find any PDF file in the sample folder
        pdf_files = [f for f in os.listdir(SAMPLE_DIR) if f.endswith(".pdf")]
        
        if not pdf_files:
            pytest.skip("No PDF files found in sample_resumes/")
        
        # Test the first PDF file found
        pdf_path = os.path.join(SAMPLE_DIR, pdf_files[0])
        result = extract_text_from_pdf(pdf_path)
        
        assert result["success"] == True
        assert len(result["text"]) > 0
        assert result["error"] == ""
