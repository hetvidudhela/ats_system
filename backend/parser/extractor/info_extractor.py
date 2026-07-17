"""
info_extractor.py
=================

WHY THIS FILE EXISTS:
    This file extracts specific pieces of information from resume text:
    
    - Name (first line of the resume, usually the person's name)
    - Email address (using regex)
    - Phone number (using regex)
    - LinkedIn URL (using regex)
    - GitHub URL (using regex)
    - Skills list (from the skills section)
    - Languages list (from the languages section)
    
    It uses regular expressions (regex) for pattern matching.
    No AI or machine learning is used.

HOW IT CONNECTS:
    - main.py calls the extraction functions after text cleaning.
    - The extracted info is stored in the Resume object (resume_model.py).
    - Some functions work on the full text, others work on specific sections.
"""

import re


# ==========================================
# EMAIL EXTRACTION
# ==========================================

def extract_email(text: str) -> str:
    """
    Extract an email address from the resume text.
    
    Looks for patterns like: someone@example.com
    
    Args:
        text (str): The resume text to search in.
    
    Returns:
        str: The first email address found, or empty string if none found.
    """
    # Email regex pattern:
    # - One or more word characters, dots, percent, plus, minus before @
    # - One or more word characters, dots, minus after @
    # - A dot followed by 2-4 letters at the end (like .com, .edu, .info)
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    match = re.search(email_pattern, text)
    
    if match:
        return match.group(0)
    else:
        return ""


# ==========================================
# PHONE NUMBER EXTRACTION
# ==========================================

def extract_phone(text: str) -> str:
    """
    Extract a phone number from the resume text.
    
    Handles various phone number formats:
    - +91 9876543210
    - +91-9876543210
    - (123) 456-7890
    - 123-456-7890
    - 9876543210
    - +1 (123) 456-7890
    
    Args:
        text (str): The resume text to search in.
    
    Returns:
        str: The first phone number found, or empty string if none found.
    """
    # Phone regex patterns (we try multiple patterns)
    phone_patterns = [
        # Pattern 1: International format with country code
        # +91 9876543210 or +91-9876543210 or +1-123-456-7890
        r'(?:\+\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}',
        
        # Pattern 2: Simple 10-digit number
        r'\b\d{10}\b',
        
        # Pattern 3: With country code prefix
        r'\+\d{1,3}\s?\d{10}',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0).strip()
            # Make sure it looks like a real phone number (at least 10 digits)
            digits_only = re.sub(r'\D', '', phone)
            if len(digits_only) >= 10:
                return phone
    
    return ""


# ==========================================
# NAME EXTRACTION
# ==========================================

def extract_name(text: str) -> str:
    """
    Extract the candidate's name from the resume text.
    
    In most resumes, the name appears on the very first line.
    We take the first non-empty line and check if it looks like a name.
    
    A name typically:
    - Contains only letters and spaces
    - Has 2-5 words
    - Is not too long
    
    Args:
        text (str): The resume text to search in.
    
    Returns:
        str: The extracted name, or empty string if not found.
    """
    # Split the text into lines
    lines = text.strip().split("\n")
    
    # Look at the first few lines to find the name
    for line in lines[:5]:  # Check first 5 lines only
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip lines that look like email or phone
        if "@" in line:
            continue
        if re.search(r'\d{5,}', line):  # Skip lines with many digits
            continue
        
        # Check if the line looks like a name
        # A name usually contains only letters, spaces, and maybe dots
        if is_likely_name(line):
            return line
    
    return ""


def is_likely_name(text: str) -> bool:
    """
    Check if a text string looks like a person's name.
    
    Args:
        text (str): The text to check.
    
    Returns:
        bool: True if it looks like a name, False otherwise.
    """
    # Remove dots and spaces for checking
    cleaned = text.replace(".", "").strip()
    
    # A name should have mostly letters
    letter_count = sum(1 for char in cleaned if char.isalpha() or char == ' ')
    if len(cleaned) == 0:
        return False
    
    letter_ratio = letter_count / len(cleaned)
    if letter_ratio < 0.8:
        return False
    
    # A name should have 1-5 words
    words = cleaned.split()
    if len(words) < 1 or len(words) > 5:
        return False
    
    # A name should not be too long
    if len(cleaned) > 50:
        return False
    
    return True


# ==========================================
# LINKEDIN URL EXTRACTION
# ==========================================

def extract_linkedin(text: str) -> str:
    """
    Extract a LinkedIn profile URL from the resume text.
    
    Looks for patterns like:
    - linkedin.com/in/username
    - www.linkedin.com/in/username
    - https://linkedin.com/in/username
    
    Args:
        text (str): The resume text to search in.
    
    Returns:
        str: The LinkedIn URL found, or empty string if none found.
    """
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+'
    
    match = re.search(linkedin_pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(0)
    else:
        return ""


# ==========================================
# GITHUB URL EXTRACTION
# ==========================================

def extract_github(text: str) -> str:
    """
    Extract a GitHub profile URL from the resume text.
    
    Looks for patterns like:
    - github.com/username
    - www.github.com/username
    - https://github.com/username
    
    Args:
        text (str): The resume text to search in.
    
    Returns:
        str: The GitHub URL found, or empty string if none found.
    """
    github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+'
    
    match = re.search(github_pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(0)
    else:
        return ""


# ==========================================
# SKILLS LIST EXTRACTION
# ==========================================

def extract_skills_list(skills_text: str) -> list:
    """
    Parse the skills section text into a clean list of individual skills.
    
    Skills in resumes can be formatted in many ways:
    - Comma separated: "Python, Java, SQL"
    - Bullet points: "- Python\n- Java\n- SQL"
    - Pipe separated: "Python | Java | SQL"
    - Mixed: "Python, Java | SQL - C++"
    
    Args:
        skills_text (str): The raw text from the skills section.
    
    Returns:
        list: A list of individual skill strings.
    """
    if not skills_text:
        return []

    # Replace common separators with commas so we can split easily
    text = skills_text.replace("|", ",")
    text = text.replace(" - ", ",")
    text = text.replace(" – ", ",")
    text = text.replace("\n", ",")
    text = text.replace(";", ",")
    text = text.replace("•", ",")
    text = text.replace("●", ",")

    # Split by comma
    raw_skills = text.split(",")

    # Clean each skill and remove empty ones
    skills = []
    for skill in raw_skills:
        # Remove extra whitespace
        clean_skill = skill.strip()
        
        # Remove leading dashes or bullets
        clean_skill = clean_skill.lstrip("-").lstrip("*").strip()
        
        # Skip empty strings and very short ones (likely garbage)
        if len(clean_skill) >= 1 and clean_skill not in skills:
            skills.append(clean_skill)

    return skills


# ==========================================
# LANGUAGES LIST EXTRACTION
# ==========================================

def extract_languages_list(languages_text: str) -> list:
    """
    Parse the languages section text into a clean list of languages.
    
    Works the same way as skills extraction.
    
    Args:
        languages_text (str): The raw text from the languages section.
    
    Returns:
        list: A list of language strings.
    """
    # Languages are formatted similarly to skills, so reuse the same logic
    if not languages_text:
        return []
    
    return extract_skills_list(languages_text)
