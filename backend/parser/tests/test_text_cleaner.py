"""
test_text_cleaner.py
====================

Tests for the text cleaning module.

Tests cover:
    - Unicode character replacement
    - Special character removal
    - Whitespace normalization
    - Blank line removal
    - Line stripping
    - Full cleaning pipeline

HOW TO RUN:
    From the parser/ directory:
        pytest tests/test_text_cleaner.py -v
"""

import os
import sys
import pytest

# Add the parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from extractor.text_cleaner import (
        clean_text,
        replace_unicode_characters,
        remove_special_characters,
        normalize_whitespace,
        remove_extra_blank_lines,
        strip_lines,
    )
except (ImportError, ValueError):
    from ..extractor.text_cleaner import (
        clean_text,
        replace_unicode_characters,
        remove_special_characters,
        normalize_whitespace,
        remove_extra_blank_lines,
        strip_lines,
    )


# ==========================================
# TESTS: Unicode Replacement
# ==========================================

class TestUnicodeReplacement:
    """Tests for replacing unicode characters."""

    def test_smart_quotes_replaced(self):
        """Test that smart quotes are replaced with normal quotes."""
        text = "\u201cHello\u201d"
        result = replace_unicode_characters(text)
        assert result == '"Hello"'

    def test_em_dash_replaced(self):
        """Test that em dashes are replaced with normal dashes."""
        text = "Python \u2014 Programming"
        result = replace_unicode_characters(text)
        assert result == "Python - Programming"

    def test_bullet_points_replaced(self):
        """Test that bullet characters are replaced with dashes."""
        text = "\u2022 Skill 1\n\u2022 Skill 2"
        result = replace_unicode_characters(text)
        assert "- Skill 1" in result
        assert "- Skill 2" in result

    def test_non_breaking_space_replaced(self):
        """Test that non-breaking spaces become regular spaces."""
        text = "Hello\u00a0World"
        result = replace_unicode_characters(text)
        assert result == "Hello World"


# ==========================================
# TESTS: Special Character Removal
# ==========================================

class TestSpecialCharacterRemoval:
    """Tests for removing special characters."""

    def test_keeps_normal_text(self):
        """Test that normal text is not affected."""
        text = "Hello World 123"
        result = remove_special_characters(text)
        assert result == "Hello World 123"

    def test_keeps_email_characters(self):
        """Test that @ and . are kept (needed for emails)."""
        text = "user@email.com"
        result = remove_special_characters(text)
        assert "@" in result
        assert "." in result

    def test_keeps_phone_characters(self):
        """Test that + and - are kept (needed for phone numbers)."""
        text = "+91-9876543210"
        result = remove_special_characters(text)
        assert "+" in result
        assert "-" in result

    def test_removes_weird_symbols(self):
        """Test that unusual symbols are removed."""
        text = "Hello §¶ World"
        result = remove_special_characters(text)
        # The weird symbols should be gone
        assert "§" not in result
        assert "¶" not in result


# ==========================================
# TESTS: Whitespace Normalization
# ==========================================

class TestWhitespaceNormalization:
    """Tests for normalizing whitespace."""

    def test_multiple_spaces_collapsed(self):
        """Test that multiple spaces become one space."""
        text = "Hello     World"
        result = normalize_whitespace(text)
        assert result == "Hello World"

    def test_tabs_replaced(self):
        """Test that tabs are replaced with spaces."""
        text = "Hello\tWorld"
        result = normalize_whitespace(text)
        assert "\t" not in result
        assert "Hello World" in result

    def test_newlines_preserved(self):
        """Test that newlines are NOT removed."""
        text = "Line 1\nLine 2\nLine 3"
        result = normalize_whitespace(text)
        assert "\n" in result


# ==========================================
# TESTS: Blank Line Removal
# ==========================================

class TestBlankLineRemoval:
    """Tests for removing extra blank lines."""

    def test_excessive_blank_lines_removed(self):
        """Test that 3+ consecutive newlines become 2."""
        text = "Line 1\n\n\n\n\nLine 2"
        result = remove_extra_blank_lines(text)
        assert result == "Line 1\n\nLine 2"

    def test_single_blank_line_kept(self):
        """Test that a single blank line is kept."""
        text = "Line 1\n\nLine 2"
        result = remove_extra_blank_lines(text)
        assert result == "Line 1\n\nLine 2"


# ==========================================
# TESTS: Line Stripping
# ==========================================

class TestLineStripping:
    """Tests for stripping whitespace from lines."""

    def test_leading_spaces_removed(self):
        """Test that leading spaces on lines are removed."""
        text = "   Hello\n   World"
        result = strip_lines(text)
        lines = result.split("\n")
        assert lines[0] == "Hello"
        assert lines[1] == "World"

    def test_trailing_spaces_removed(self):
        """Test that trailing spaces on lines are removed."""
        text = "Hello   \nWorld   "
        result = strip_lines(text)
        lines = result.split("\n")
        assert lines[0] == "Hello"
        assert lines[1] == "World"


# ==========================================
# TESTS: Full Cleaning Pipeline
# ==========================================

class TestCleanText:
    """Tests for the complete clean_text function."""

    def test_empty_input(self):
        """Test that empty string returns empty string."""
        assert clean_text("") == ""

    def test_none_input(self):
        """Test that None returns empty string."""
        assert clean_text(None) == ""

    def test_normal_text_unchanged(self):
        """Test that clean text is not damaged."""
        text = "John Doe\nSoftware Engineer"
        result = clean_text(text)
        assert "John Doe" in result
        assert "Software Engineer" in result

    def test_messy_text_cleaned(self):
        """Test that messy text gets properly cleaned."""
        messy = "  John   Doe  \n\n\n\n  \u2022 Python  \n  \u2022 Java  "
        result = clean_text(messy)
        # Should have no excessive blank lines
        assert "\n\n\n" not in result
        # Should have no leading/trailing spaces on lines
        lines = result.split("\n")
        for line in lines:
            assert line == line.strip()
