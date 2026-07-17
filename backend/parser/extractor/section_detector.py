"""
section_detector.py
===================

WHY THIS FILE EXISTS:
    Resumes have sections like "Skills", "Education", "Experience", etc.
    But different people write these headings differently:
    
    - "Skills" vs "Technical Skills" vs "Key Skills" vs "Core Skills"
    - "Experience" vs "Work Experience" vs "Professional Experience"
    - "Education" vs "Academic Background" vs "Qualification"
    
    This file detects these sections even when they are written differently.
    It uses simple keyword matching (no AI, no LLM).

HOW IT CONNECTS:
    - main.py calls detect_sections() after text cleaning is done.
    - The detected sections are stored in the Resume object.
    - section_detector works on the cleaned text from text_cleaner.py.
"""

import re


# ==========================================
# SECTION HEADING KEYWORDS
# ==========================================
# Each section has a list of possible heading variations.
# These are the keywords we look for (case-insensitive).

SECTION_KEYWORDS = {
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
    ],
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
    ],
    "achievements": [
        "achievements",
        "accomplishments",
        "awards",
        "honors",
        "honours",
        "recognition",
        "accolades",
        "extra curricular activities",
        "extracurricular activities",
        "activities",
    ],
    "languages": [
        "languages",
        "languages known",
        "language proficiency",
        "linguistic skills",
    ],
}

# These are ALL the section names we know about.
# We use this list to know when one section ends and another begins.
ALL_SECTION_KEYWORDS = []
for section_name in SECTION_KEYWORDS:
    for keyword in SECTION_KEYWORDS[section_name]:
        ALL_SECTION_KEYWORDS.append(keyword)


# ==========================================
# MAIN DETECTION FUNCTION
# ==========================================

def detect_sections(cleaned_text: str) -> dict:
    """
    Detect and extract resume sections from cleaned text.
    
    This function finds section headings in the text and extracts
    the content under each heading.
    
    Args:
        cleaned_text (str): The cleaned resume text.
    
    Returns:
        dict: A dictionary where keys are section names and values
              are the text content found under that section.
              
              Example:
              {
                  "skills": "Python, Java, SQL...",
                  "education": "B.Tech in Computer Science...",
                  "experience": "Software Developer at XYZ...",
                  ...
              }
    """
    
    # This will store the detected sections
    sections = {
        "skills": "",
        "education": "",
        "experience": "",
        "projects": "",
        "certifications": "",
        "achievements": "",
        "languages": "",
    }

    # Split the text into individual lines
    lines = cleaned_text.split("\n")

    # Step 1: Find where each section starts (line number + section name)
    section_positions = find_section_positions(lines)

    # Step 2: Extract text between section headings
    for i in range(len(section_positions)):
        section_name = section_positions[i]["section"]
        start_line = section_positions[i]["line_number"] + 1  # Skip the heading line

        # Find the end: either the next section or the end of the text
        if i + 1 < len(section_positions):
            end_line = section_positions[i + 1]["line_number"]
        else:
            end_line = len(lines)

        # Extract the lines that belong to this section
        section_lines = lines[start_line:end_line]

        # Join them back into a string and clean up
        section_text = "\n".join(section_lines).strip()

        # Store in the sections dictionary
        if section_text:
            sections[section_name] = section_text

    return sections


def find_section_positions(lines: list) -> list:
    """
    Find the line numbers where each section heading appears.
    
    This function goes through each line and checks if it matches
    any known section heading keyword.
    
    Args:
        lines (list): List of text lines from the resume.
    
    Returns:
        list: A list of dictionaries, each containing:
              - "line_number" (int): The line index where the heading was found.
              - "section" (str): The normalized section name (e.g., "skills").
    """
    
    section_positions = []

    for line_number in range(len(lines)):
        line = lines[line_number]
        
        # Check if this line is a section heading
        section_name = match_section_heading(line)
        
        if section_name is not None:
            section_positions.append({
                "line_number": line_number,
                "section": section_name,
            })

    return section_positions


def match_section_heading(line: str) -> str:
    """
    Check if a line matches any known section heading.
    
    A section heading is usually a short line (just a few words)
    that matches one of our known keywords.
    
    Args:
        line (str): A single line of text from the resume.
    
    Returns:
        str or None: The section name if matched, None otherwise.
    """
    
    # Clean up the line for comparison
    cleaned_line = line.strip().lower()
    
    # Remove common punctuation that might be around the heading
    # e.g., "--- SKILLS ---" or "** Education **" or "SKILLS:"
    cleaned_line = re.sub(r'[^a-z\s]', '', cleaned_line).strip()

    # Skip empty lines
    if not cleaned_line:
        return None

    # Skip lines that are too long to be a heading (more than 6 words)
    word_count = len(cleaned_line.split())
    if word_count > 6:
        return None

    # Check against all known section keywords
    for section_name in SECTION_KEYWORDS:
        keywords = SECTION_KEYWORDS[section_name]
        for keyword in keywords:
            if cleaned_line == keyword:
                return section_name

    return None
