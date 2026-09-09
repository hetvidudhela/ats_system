"""
resume_validator.py
===================

WHY THIS FILE EXISTS:
    We want to validate whether an uploaded document (PDF or DOCX) is
    actually a resume. Currently, the parser accepts any PDF or DOCX file
    (e.g., lecture notes, textbook chapters, manuals) and parses it anyway.
    
    This validator implements a deterministic, rule-based approach:
    1. It extracts/checks if a valid email address is present.
    2. It extracts/checks if a valid phone number is present.
    3. It scans the text line-by-line for standard resume section headings:
       - Education
       - Experience
       - Skills
       - Projects
       - Certifications
       - Summary
       - Objective
    
    Based on these indicators, it calculates a confidence score.
    If the score is below the threshold, it rejects the document.
"""

import re
try:
    from ..extractor.info_extractor import extract_email, extract_phone
except (ImportError, ValueError):
    from extractor.info_extractor import extract_email, extract_phone

# Indicators and their corresponding weights/scores
INDICATOR_WEIGHTS = {
    "email": 30,
    "phone": 10,
    "education": 15,
    "experience": 15,
    "skills": 15,
    "projects": 15,
    "certifications": 10,
    "summary": 10,
    "objective": 10,
}

# Standard heading variations (keywords) for resume sections (case-insensitive)
RESUME_SECTIONS = {
    "education": [
        "education",
        "academic background",
        "academic details",
        "qualification",
        "qualifications",
        "educational qualification",
        "educational qualifications",
        "academic qualification",
        "academic qualifications",
        "academics",
        "educational details",
        "academic credentials",
        "educational background",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "employment",
        "work history",
        "professional background",
        "career history",
        "internship",
        "internships",
        "internship experience",
        "career outline",
        "professional history",
        "work record",
        "professional development",
    ],
    "skills": [
        "skills",
        "technical skills",
        "key skills",
        "core skills",
        "core competencies",
        "competencies",
        "technologies",
        "tools and technologies",
        "technical proficiency",
        "areas of expertise",
        "professional skills",
        "skills & expertise",
        "technical expertise",
    ],
    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "project work",
        "key projects",
        "major projects",
        "mini projects",
        "project details",
        "key undertakings",
        "technical projects",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "certification",
        "certificate",
        "professional certifications",
        "licenses",
        "courses",
        "training",
        "workshops",
        "credentials",
    ],
    "summary": [
        "summary",
        "professional summary",
        "career summary",
        "executive summary",
        "profile",
        "professional profile",
        "about me",
        "personal statement",
        "summary of qualifications",
    ],
    "objective": [
        "objective",
        "career objective",
        "job objective",
        "professional objective",
    ],
}

def is_section_heading(line: str, keywords: list) -> bool:
    """
    Check if a line looks like a section heading that matches any keyword in keywords.
    
    A section heading is usually a short line (up to 6 words) that contains only
    letters/numbers after punctuation is stripped, and matches one of the keywords.
    """
    # Clean the line by removing punctuation and converting to lowercase
    cleaned_line = line.strip().lower()
    # Keep only letters, digits, and spaces
    cleaned_line = re.sub(r'[^a-z0-9\s]', '', cleaned_line).strip()
    
    if not cleaned_line:
        return False
        
    # Check word count limit (headings are typically brief)
    words = cleaned_line.split()
    if len(words) > 6:
        return False
        
    # Check if the line exactly matches any normalized keyword
    for keyword in keywords:
        cleaned_keyword = re.sub(r'[^a-z0-9\s]', '', keyword.lower()).strip()
        if cleaned_line == cleaned_keyword:
            return True
            
    return False

def validate_resume_text(text: str, threshold: int = 40) -> dict:
    """
    Validate if the provided text resembles a resume based on deterministic rules.
    
    Checks for:
    - Valid email
    - Valid phone number
    - Specific section headings (Education, Experience, Skills, Projects, etc.)
    
    Calculates a confidence score and compares it against the threshold.
    
    Args:
        text (str): The cleaned text of the document.
        threshold (int): The minimum confidence score required to pass.
        
    Returns:
        dict: A validation result dictionary:
            {
                "is_valid": bool,
                "confidence_score": int,
                "error": str,
                "indicators": dict
            }
    """
    # Initialize indicators status
    indicators = {
        "email": False,
        "phone": False,
        "education": False,
        "experience": False,
        "skills": False,
        "projects": False,
        "certifications": False,
        "summary": False,
        "objective": False,
    }
    
    # 1. Check for email
    email = extract_email(text)
    if email:
        indicators["email"] = True
        
    # 2. Check for phone number
    phone = extract_phone(text)
    if phone:
        indicators["phone"] = True
        
    # 3. Check for section headings
    # Split text into lines to inspect each line as a potential heading
    lines = text.split("\n")
    for line in lines:
        for section, keywords in RESUME_SECTIONS.items():
            # If we haven't matched this section yet, check it
            if not indicators[section]:
                if is_section_heading(line, keywords):
                    indicators[section] = True
                    
    # Calculate confidence score
    confidence_score = 0
    for indicator, is_present in indicators.items():
        if is_present:
            confidence_score += INDICATOR_WEIGHTS.get(indicator, 0)
            
    # Check against the threshold
    is_valid = confidence_score >= threshold
    error = "" if is_valid else "Uploaded document does not appear to be a resume."
    
    return {
        "is_valid": is_valid,
        "confidence_score": confidence_score,
        "error": error,
        "indicators": indicators,
    }
