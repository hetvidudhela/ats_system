"""
test_file_validator.py
======================

Tests for the file validation module.

Tests cover:
    - Accepting valid PDF files
    - Accepting valid DOCX files
    - Rejecting non-existent files
    - Rejecting unsupported file types
    - Rejecting empty files
    - Rejecting oversized files
    - Checking file extension helper

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_file_validator.py -v
"""

import os
import sys
import pytest

# Add the parser directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validators.file_validator import (
    validate_file,
    check_file_exists,
    check_file_extension,
    check_file_not_empty,
    check_file_size,
    get_file_extension,
)


# ==========================================
# HELPER: Create temporary test files
# ==========================================

def create_temp_file(tmp_path, filename, content=b"dummy content"):
    """Create a temporary file with given content."""
    file_path = os.path.join(str(tmp_path), filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


# ==========================================
# TESTS: File Existence
# ==========================================

class TestFileExists:
    """Tests for checking if a file exists."""

    def test_file_exists(self, tmp_path):
        """Test that an existing file passes the check."""
        file_path = create_temp_file(tmp_path, "test.pdf")
        result = check_file_exists(file_path)
        assert result["is_valid"] == True

    def test_file_not_exists(self):
        """Test that a non-existent file fails the check."""
        result = check_file_exists("/fake/path/resume.pdf")
        assert result["is_valid"] == False
        assert "not found" in result["error"].lower()

    def test_directory_not_file(self, tmp_path):
        """Test that a directory path fails the check."""
        result = check_file_exists(str(tmp_path))
        assert result["is_valid"] == False


# ==========================================
# TESTS: File Extension
# ==========================================

class TestFileExtension:
    """Tests for checking file extensions."""

    def test_pdf_extension_accepted(self, tmp_path):
        """Test that .pdf files are accepted."""
        file_path = create_temp_file(tmp_path, "resume.pdf")
        result = check_file_extension(file_path)
        assert result["is_valid"] == True

    def test_docx_extension_accepted(self, tmp_path):
        """Test that .docx files are accepted."""
        file_path = create_temp_file(tmp_path, "resume.docx")
        result = check_file_extension(file_path)
        assert result["is_valid"] == True

    def test_txt_extension_rejected(self, tmp_path):
        """Test that .txt files are rejected."""
        file_path = create_temp_file(tmp_path, "resume.txt")
        result = check_file_extension(file_path)
        assert result["is_valid"] == False
        assert "unsupported" in result["error"].lower()

    def test_jpg_extension_rejected(self, tmp_path):
        """Test that .jpg files are rejected."""
        file_path = create_temp_file(tmp_path, "resume.jpg")
        result = check_file_extension(file_path)
        assert result["is_valid"] == False

    def test_uppercase_pdf_accepted(self, tmp_path):
        """Test that .PDF (uppercase) files are also accepted."""
        file_path = create_temp_file(tmp_path, "resume.PDF")
        result = check_file_extension(file_path)
        assert result["is_valid"] == True

    def test_no_extension_rejected(self, tmp_path):
        """Test that files without extension are rejected."""
        file_path = create_temp_file(tmp_path, "resume")
        result = check_file_extension(file_path)
        assert result["is_valid"] == False


# ==========================================
# TESTS: Empty File Check
# ==========================================

class TestFileNotEmpty:
    """Tests for checking if a file is empty."""

    def test_non_empty_file(self, tmp_path):
        """Test that a file with content passes."""
        file_path = create_temp_file(tmp_path, "resume.pdf", b"some content")
        result = check_file_not_empty(file_path)
        assert result["is_valid"] == True

    def test_empty_file(self, tmp_path):
        """Test that an empty file (0 bytes) fails."""
        file_path = create_temp_file(tmp_path, "empty.pdf", b"")
        result = check_file_not_empty(file_path)
        assert result["is_valid"] == False
        assert "empty" in result["error"].lower()


# ==========================================
# TESTS: File Size Check
# ==========================================

class TestFileSize:
    """Tests for checking file size limits."""

    def test_small_file_accepted(self, tmp_path):
        """Test that a small file passes the size check."""
        file_path = create_temp_file(tmp_path, "small.pdf", b"x" * 100)
        result = check_file_size(file_path)
        assert result["is_valid"] == True

    def test_oversized_file_rejected(self, tmp_path):
        """Test that a file larger than 10 MB is rejected."""
        # Create a file slightly over 10 MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11 MB
        file_path = create_temp_file(tmp_path, "large.pdf", large_content)
        result = check_file_size(file_path)
        assert result["is_valid"] == False
        assert "too large" in result["error"].lower()


# ==========================================
# TESTS: Full Validation Pipeline
# ==========================================

class TestValidateFile:
    """Tests for the complete validate_file function."""

    def test_valid_pdf_file(self, tmp_path):
        """Test complete validation with a valid PDF file."""
        file_path = create_temp_file(tmp_path, "good.pdf", b"PDF content here")
        result = validate_file(file_path)
        assert result["is_valid"] == True
        assert result["error"] == ""

    def test_valid_docx_file(self, tmp_path):
        """Test complete validation with a valid DOCX file."""
        file_path = create_temp_file(tmp_path, "good.docx", b"DOCX content here")
        result = validate_file(file_path)
        assert result["is_valid"] == True

    def test_nonexistent_file_fails(self):
        """Test that a nonexistent file fails validation."""
        result = validate_file("/no/such/file.pdf")
        assert result["is_valid"] == False

    def test_wrong_extension_fails(self, tmp_path):
        """Test that a .txt file fails validation."""
        file_path = create_temp_file(tmp_path, "bad.txt", b"text content")
        result = validate_file(file_path)
        assert result["is_valid"] == False


# ==========================================
# TESTS: File Extension Helper
# ==========================================

class TestGetFileExtension:
    """Tests for the get_file_extension helper function."""

    def test_pdf_extension(self):
        """Test getting .pdf extension."""
        assert get_file_extension("resume.pdf") == ".pdf"

    def test_docx_extension(self):
        """Test getting .docx extension."""
        assert get_file_extension("resume.docx") == ".docx"

    def test_uppercase_extension(self):
        """Test that uppercase extensions are lowercased."""
        assert get_file_extension("resume.PDF") == ".pdf"

    def test_path_with_directories(self):
        """Test getting extension from a full path."""
        assert get_file_extension("/home/user/docs/resume.pdf") == ".pdf"
