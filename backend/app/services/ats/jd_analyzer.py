"""
jd_analyzer.py
==============
Deterministic Job Description (JD) analyzer for the ATS Engine.
Extracts required skills, preferred skills, keywords, experience, and education requirements.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.ats.normalizer import (
    SKILL_TAXONOMY,
    resolve_canonical_skill,
    get_display_name,
    normalize_token,
)


@dataclass
class JDAnalysis:
    """Structured extraction results from a Job Description."""
    job_title: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    all_skills: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    min_experience_years: Optional[float] = None
    required_education: str = ""
    raw_text: str = ""


# Section headers commonly found in Job Descriptions
REQUIRED_HEADERS = [
    "required skills", "requirements", "qualifications", "must have",
    "minimum qualifications", "core requirements", "what you need",
    "what you'll need", "technical requirements", "skills required",
    "key requirements", "essential requirements",
]

PREFERRED_HEADERS = [
    "preferred skills", "nice to have", "good to have", "preferred qualifications",
    "bonus points", "bonus", "plus", "desirable", "what gives you an edge",
    "preferred experience", "optional skills",
]

RESPONSIBILITY_HEADERS = [
    "responsibilities", "what you'll do", "role overview", "day to day",
    "key responsibilities", "duties",
]

ALL_HEADERS = REQUIRED_HEADERS + PREFERRED_HEADERS + RESPONSIBILITY_HEADERS


def split_jd_sections(jd_text: str) -> dict[str, str]:
    """
    Split JD text into logical buckets: 'required', 'preferred', 'responsibilities', 'other'.
    """
    lines = jd_text.split("\n")
    sections = {
        "required": [],
        "preferred": [],
        "responsibilities": [],
        "other": [],
    }

    current_bucket = "other"

    for line in lines:
        cleaned_line = re.sub(r"[^a-zA-Z\s]", " ", line).lower().strip()
        matched_header = False

        for h in REQUIRED_HEADERS:
            if h in cleaned_line:
                current_bucket = "required"
                matched_header = True
                break

        if not matched_header:
            for h in PREFERRED_HEADERS:
                if h in cleaned_line:
                    current_bucket = "preferred"
                    matched_header = True
                    break

        if not matched_header:
            for h in RESPONSIBILITY_HEADERS:
                if h in cleaned_line:
                    current_bucket = "responsibilities"
                    matched_header = True
                    break

        sections[current_bucket].append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


def extract_skills_from_text(text: str) -> list[str]:
    """
    Extract canonical skills found in the given text using strict boundary regex matching.
    Prevents false positives (e.g., 'Java' in 'JavaScript', 'C' in ordinary words).
    """
    found_skills: set[str] = set()
    norm_text = text.lower()

    for cid, (display, aliases) in SKILL_TAXONOMY.items():
        for alias in aliases:
            alias_lower = alias.lower()

            # Special boundary handling for single characters and symbols
            if alias_lower == "c":
                # Must be standalone 'C' surrounded by whitespace or punctuation, not part of words
                pattern = r"(?<![a-zA-Z0-9_#+])c(?![a-zA-Z0-9_#+])"
                # Require context: programming, language, or paired with C++ / developer
                if re.search(pattern, norm_text) and re.search(r"\b(c\s*(?:programming|language)|c\s*/\s*c\+\+|embedded\s+c)\b", norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower == "r":
                pattern = r"\br\s+(?:programming|language|scripting|studio)\b"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower == "go":
                pattern = r"\b(golang|go\s+language|go\s+developer|go\s+backend)\b"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower in ["c++", "cpp"]:
                pattern = r"(?:\bc\+\+|\bcpp\b)"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower in ["c#", "csharp"]:
                pattern = r"(?:\bc#|\bcsharp\b)"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower == "sql":
                # Must not match MySQL or PostgreSQL directly
                pattern = r"(?<![a-zA-Z0-9])sql(?![a-zA-Z0-9])"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower == "java":
                # Must not match javascript
                pattern = r"\bjava\b(?!\s*script)"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower == "react":
                # Must not match react native
                pattern = r"\breact\b(?!\s*native)"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            elif alias_lower == ".net":
                pattern = r"(?:\.net|\bdotnet\b)"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break
            else:
                # Standard word boundary match
                pattern = r"\b" + re.escape(alias_lower) + r"\b"
                if re.search(pattern, norm_text):
                    found_skills.add(display)
                    break

    # Also parse bullet points or comma-separated lists for unrecognized tech terms
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip().lstrip("-*•●").strip()
        if stripped and len(stripped.split()) <= 4:
            # Check if this line is an exact skill name or alias
            res = resolve_canonical_skill(stripped)
            if res:
                found_skills.add(res[1])

    return sorted(list(found_skills))


def extract_experience_years(text: str) -> Optional[float]:
    """
    Extract minimum years of experience required from JD.
    Returns float (e.g. 2.0) or None.
    """
    lower = text.lower()

    # Check for fresher/intern keywords
    if re.search(r"\b(freshers?\s+welcome|no\s+experience\s+required|0\s*-\s*1\s+years?|internship|entry\s+level)\b", lower):
        return 0.0

    # Patterns like: "2+ years", "3-5 years", "min 2 years of experience", "2 years"
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:to|-)\s*\d+\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+relevant)?(?:\s+experience|\s+exp)?",
        r"(?:minimum|min|at\s+least)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
    ]

    for p in patterns:
        m = re.search(p, lower)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                continue

    return None


def extract_education_requirement(text: str) -> str:
    """
    Extract required education level from JD.
    """
    lower = text.lower()
    if re.search(r"\b(ph\.?d|doctorate)\b", lower):
        return "Doctorate / Ph.D."
    if re.search(r"\b(master'?s?|m\.?tech|mca|m\.?s|m\.?sc)\b", lower):
        return "Master's Degree"
    if re.search(r"\b(bachelor'?s?|b\.?tech|b\.?e|bca|b\.?s|b\.?sc|undergraduate|degree in computer science)\b", lower):
        return "Bachelor's Degree"
    if re.search(r"\b(diploma|associate'?s?)\b", lower):
        return "Diploma / Associate"
    return ""


def extract_job_title(jd_text: str) -> str:
    """
    Extract or infer job title from the first non-empty lines of the JD.
    """
    lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
    for line in lines[:3]:
        # If line is short and looks like a title
        if 3 <= len(line) <= 60 and not any(h in line.lower() for h in ALL_HEADERS):
            # Check for common title words
            if re.search(r"\b(developer|engineer|analyst|architect|specialist|manager|lead|intern|designer|consultant)\b", line, re.I):
                return line
    return lines[0] if lines else "Target Role"


def analyze_job_description(jd_text: str) -> JDAnalysis:
    """
    Full pipeline to analyze and parse a Job Description.
    """
    if not jd_text or not jd_text.strip():
        return JDAnalysis()

    cleaned_jd = jd_text.strip()
    sections = split_jd_sections(cleaned_jd)

    # Extract skills by section
    required_extracted = extract_skills_from_text(sections["required"])
    preferred_extracted = extract_skills_from_text(sections["preferred"])
    all_extracted = extract_skills_from_text(cleaned_jd)

    # If the JD didn't explicitly separate sections:
    # Skills in 'required' or total skills default to required, unless specifically in 'preferred'
    if not required_extracted and not preferred_extracted:
        required_skills = all_extracted
        preferred_skills = []
    else:
        # Separate properly
        preferred_set = set(preferred_extracted)
        required_skills = [s for s in all_extracted if s not in preferred_set]
        preferred_skills = [s for s in preferred_extracted]

    # Extract keywords (methodologies, architecture, etc.)
    keywords = [s for s in all_extracted if s in [
        "REST API", "Microservices", "CI/CD", "Git", "Agile", "TDD",
        "MVVM", "MVC", "Unit Testing", "Machine Learning", "NLP"
    ]]

    # Extract experience and education
    exp_years = extract_experience_years(cleaned_jd)
    edu_req = extract_education_requirement(cleaned_jd)
    title = extract_job_title(cleaned_jd)

    return JDAnalysis(
        job_title=title,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        all_skills=all_extracted,
        keywords=keywords,
        min_experience_years=exp_years,
        required_education=edu_req,
        raw_text=cleaned_jd,
    )
