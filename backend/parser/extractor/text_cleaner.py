"""
text_cleaner.py
===============

WHY THIS FILE EXISTS:
    Raw text extracted from PDFs and DOCX files is usually messy.
    It can have:
    - Extra whitespace and blank lines
    - Special characters that don't belong
    - Inconsistent spacing
    - Unicode artifacts
    
    This file cleans all that up so the text is easy to work with
    for section detection and info extraction.

HOW IT CONNECTS:
    - main.py calls clean_text() after extracting raw text from the resume.
    - The cleaned text is then passed to section_detector.py and info_extractor.py.
    - The cleaned text is also stored in the Resume object as 'raw_text'.
"""

import re


def clean_text(raw_text: str) -> str:
    """
    Clean the raw text extracted from a resume.
    
    This function runs multiple cleaning steps in order.
    Each step fixes a specific type of messiness.
    
    Args:
        raw_text (str): The raw text extracted from a PDF or DOCX file.
    
    Returns:
        str: The cleaned text, ready for further processing.
    """
    
    # If the input is empty or None, return empty string
    if not raw_text:
        return ""

    # Step 1: Replace common unicode artifacts
    text = replace_unicode_characters(raw_text)

    # Step 2: Remove unnecessary special characters
    text = remove_special_characters(text)

    # Step 3: Normalize whitespace (tabs, multiple spaces, etc.)
    text = normalize_whitespace(text)

    # Step 4: Remove excessive blank lines (keep max one blank line)
    text = remove_extra_blank_lines(text)

    # Step 5: Strip leading and trailing whitespace from each line
    text = strip_lines(text)

    # Step 6: Final trim of the whole text
    text = text.strip()

    return text


# ==========================================
# INDIVIDUAL CLEANING FUNCTIONS
# ==========================================

def replace_unicode_characters(text: str) -> str:
    """
    Replace common unicode characters with their normal versions.
    
    PDFs often use fancy unicode characters instead of normal ones.
    For example, smart quotes instead of regular quotes.
    
    Args:
        text (str): Input text.
    
    Returns:
        str: Text with unicode characters replaced.
    """
    # Replace smart quotes with normal quotes
    text = text.replace("\u2018", "'")   # Left single quote
    text = text.replace("\u2019", "'")   # Right single quote
    text = text.replace("\u201c", '"')   # Left double quote
    text = text.replace("\u201d", '"')   # Right double quote

    # Replace em dash and en dash with normal dash
    text = text.replace("\u2013", "-")   # En dash
    text = text.replace("\u2014", "-")   # Em dash

    # Replace bullet characters with a simple dash
    text = text.replace("\u2022", "-")   # Bullet point
    text = text.replace("\u25cf", "-")   # Black circle
    text = text.replace("\u25cb", "-")   # White circle
    text = text.replace("\u25aa", "-")   # Small black square
    text = text.replace("\u25a0", "-")   # Black square
    text = text.replace("\u00b7", "-")   # Middle dot

    # Replace non-breaking space with normal space
    text = text.replace("\u00a0", " ")   # Non-breaking space
    text = text.replace("\xa0", " ")     # Same thing, different notation

    return text


def remove_special_characters(text: str) -> str:
    """
    Remove special characters that don't belong in resume text.
    
    We keep: letters, numbers, common punctuation, whitespace.
    We remove: weird symbols, control characters, etc.
    
    Args:
        text (str): Input text.
    
    Returns:
        str: Text with special characters removed.
    """
    # Keep: letters, digits, common punctuation, whitespace, newlines
    # The regex below keeps everything that's "normal" in a resume
    # \w = letters, digits, underscore
    # \s = whitespace (spaces, tabs, newlines)
    # The rest are common punctuation marks found in resumes
    cleaned_text = re.sub(
        r'[^\w\s@.,:;!?\-/()&+#\'\"|\[\]]',
        '',
        text
    )
    return cleaned_text


def normalize_whitespace(text: str) -> str:
    """
    Replace multiple consecutive spaces with a single space.
    Also replace tabs with spaces.
    
    Args:
        text (str): Input text.
    
    Returns:
        str: Text with normalized whitespace.
    """
    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Replace multiple spaces with a single space
    # But DON'T replace newlines (we handle those separately)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Replace multiple spaces with single space in each line
        cleaned_line = re.sub(r' +', ' ', line)
        cleaned_lines.append(cleaned_line)
    
    text = "\n".join(cleaned_lines)
    return text


def remove_extra_blank_lines(text: str) -> str:
    """
    Remove excessive blank lines from the text.
    
    Multiple consecutive empty lines are reduced to just one.
    This makes the text cleaner without losing section breaks.
    
    Args:
        text (str): Input text.
    
    Returns:
        str: Text with extra blank lines removed.
    """
    # Replace 3 or more consecutive newlines with just 2 (one blank line)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', text)
    return cleaned_text


def strip_lines(text: str) -> str:
    """
    Remove leading and trailing whitespace from each line.
    
    Args:
        text (str): Input text.
    
    Returns:
        str: Text with each line stripped.
    """
    lines = text.split("\n")
    stripped_lines = []
    for line in lines:
        stripped_lines.append(line.strip())
    
    text = "\n".join(stripped_lines)
    return text
