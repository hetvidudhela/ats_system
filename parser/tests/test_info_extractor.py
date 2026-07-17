"""
test_info_extractor.py
======================

Tests for the information extraction module.

Tests cover:
    - Email extraction
    - Phone number extraction
    - Name extraction
    - LinkedIn URL extraction
    - GitHub URL extraction
    - Skills list parsing
    - Languages list parsing

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_info_extractor.py -v
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extractor.info_extractor import (
    extract_email,
    extract_phone,
    extract_name,
    extract_linkedin,
    extract_github,
    extract_skills_list,
    extract_languages_list,
    is_likely_name,
)


# ==========================================
# TESTS: Email Extraction
# ==========================================

class TestExtractEmail:
    """Tests for extracting email addresses."""

    def test_simple_email(self):
        text = "Contact me at john@example.com for details"
        assert extract_email(text) == "john@example.com"

    def test_gmail_email(self):
        text = "Email: johndoe123@gmail.com"
        assert extract_email(text) == "johndoe123@gmail.com"

    def test_email_with_dots(self):
        text = "john.doe@company.co.in"
        assert extract_email(text) == "john.doe@company.co.in"

    def test_email_with_plus(self):
        text = "user+tag@email.com"
        assert extract_email(text) == "user+tag@email.com"

    def test_no_email_found(self):
        text = "No email address here"
        assert extract_email(text) == ""

    def test_email_in_multiline_text(self):
        text = "John Doe\nSoftware Dev\njohn@mail.com\n+91 1234567890"
        assert extract_email(text) == "john@mail.com"


# ==========================================
# TESTS: Phone Number Extraction
# ==========================================

class TestExtractPhone:
    """Tests for extracting phone numbers."""

    def test_ten_digit_number(self):
        text = "Phone: 9876543210"
        result = extract_phone(text)
        assert "9876543210" in result

    def test_with_country_code(self):
        text = "Call: +91 9876543210"
        result = extract_phone(text)
        assert "9876543210" in result

    def test_with_dashes(self):
        text = "Phone: 987-654-3210"
        result = extract_phone(text)
        assert result != ""

    def test_us_format(self):
        text = "Phone: (123) 456-7890"
        result = extract_phone(text)
        assert result != ""

    def test_no_phone_found(self):
        text = "No phone number here at all"
        assert extract_phone(text) == ""

    def test_short_number_ignored(self):
        """Numbers with less than 10 digits should not be detected as phone."""
        text = "Pin: 12345"
        assert extract_phone(text) == ""


# ==========================================
# TESTS: Name Extraction
# ==========================================

class TestExtractName:
    """Tests for extracting the candidate's name."""

    def test_simple_name(self):
        text = "John Doe\njohn@email.com\nSkills\nPython"
        assert extract_name(text) == "John Doe"

    def test_three_word_name(self):
        text = "John Michael Doe\nSoftware Engineer"
        assert extract_name(text) == "John Michael Doe"

    def test_skips_email_line(self):
        """If the first line is an email, it should be skipped."""
        text = "john@email.com\nJohn Doe\nSkills"
        assert extract_name(text) == "John Doe"

    def test_empty_text(self):
        assert extract_name("") == ""

    def test_skips_phone_line(self):
        """If the first line has many digits, it should be skipped."""
        text = "+91 9876543210\nJohn Doe\nSkills"
        assert extract_name(text) == "John Doe"


# ==========================================
# TESTS: Name Likelihood Check
# ==========================================

class TestIsLikelyName:
    """Tests for the is_likely_name helper function."""

    def test_normal_name(self):
        assert is_likely_name("John Doe") == True

    def test_single_name(self):
        assert is_likely_name("John") == True

    def test_long_sentence(self):
        """A long sentence should not be detected as a name."""
        assert is_likely_name("This is definitely not a name at all in any way") == False

    def test_numbers_not_name(self):
        assert is_likely_name("12345") == False

    def test_empty_string(self):
        assert is_likely_name("") == False


# ==========================================
# TESTS: LinkedIn URL Extraction
# ==========================================

class TestExtractLinkedIn:
    """Tests for extracting LinkedIn URLs."""

    def test_full_url(self):
        text = "LinkedIn: https://www.linkedin.com/in/johndoe"
        result = extract_linkedin(text)
        assert "linkedin.com/in/johndoe" in result

    def test_without_https(self):
        text = "linkedin.com/in/johndoe"
        result = extract_linkedin(text)
        assert "linkedin.com/in/johndoe" in result

    def test_with_www(self):
        text = "www.linkedin.com/in/john-doe-123"
        result = extract_linkedin(text)
        assert "linkedin.com/in/john-doe-123" in result

    def test_no_linkedin(self):
        text = "No LinkedIn here"
        assert extract_linkedin(text) == ""


# ==========================================
# TESTS: GitHub URL Extraction
# ==========================================

class TestExtractGitHub:
    """Tests for extracting GitHub URLs."""

    def test_full_url(self):
        text = "GitHub: https://github.com/johndoe"
        result = extract_github(text)
        assert "github.com/johndoe" in result

    def test_without_https(self):
        text = "github.com/johndoe"
        result = extract_github(text)
        assert "github.com/johndoe" in result

    def test_no_github(self):
        text = "No GitHub here"
        assert extract_github(text) == ""


# ==========================================
# TESTS: Skills List Extraction
# ==========================================

class TestExtractSkillsList:
    """Tests for parsing skills text into a list."""

    def test_comma_separated(self):
        text = "Python, Java, SQL, JavaScript"
        skills = extract_skills_list(text)
        assert "Python" in skills
        assert "Java" in skills
        assert "SQL" in skills
        assert "JavaScript" in skills

    def test_newline_separated(self):
        text = "Python\nJava\nSQL"
        skills = extract_skills_list(text)
        assert "Python" in skills
        assert "Java" in skills

    def test_pipe_separated(self):
        text = "Python | Java | SQL"
        skills = extract_skills_list(text)
        assert "Python" in skills
        assert "Java" in skills

    def test_bullet_points(self):
        text = "- Python\n- Java\n- SQL"
        skills = extract_skills_list(text)
        assert "Python" in skills

    def test_empty_text(self):
        assert extract_skills_list("") == []

    def test_no_duplicates(self):
        """Same skill should not appear twice."""
        text = "Python, Python, Java"
        skills = extract_skills_list(text)
        python_count = skills.count("Python")
        assert python_count == 1


# ==========================================
# TESTS: Languages List Extraction
# ==========================================

class TestExtractLanguagesList:
    """Tests for parsing languages text into a list."""

    def test_comma_separated_languages(self):
        text = "English, Hindi, Gujarati"
        languages = extract_languages_list(text)
        assert "English" in languages
        assert "Hindi" in languages
        assert "Gujarati" in languages

    def test_empty_text(self):
        assert extract_languages_list("") == []
