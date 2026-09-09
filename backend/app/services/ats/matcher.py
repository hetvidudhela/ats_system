"""
matcher.py
==========
Multi-tiered resume and Job Description matching engine.
Performs exact, normalized, alias, and conservative fuzzy matching with evidence tracking.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from rapidfuzz import fuzz

from app.services.ats.normalizer import (
    SKILL_TAXONOMY,
    ALIAS_MAP,
    DISPLAY_NAMES,
    resolve_canonical_skill,
    get_display_name,
    normalize_token,
)
from app.services.ats.jd_analyzer import JDAnalysis, extract_skills_from_text
from app.services.ats.models import (
    SkillMatchDetail,
    ExperienceAnalysis,
    EducationAnalysis,
    ProjectRelevanceAnalysis,
)

# Negative context patterns indicating lack of actual experience
NEGATIVE_CONTEXT_PATTERNS = [
    r"\b(?:interested in learning|looking forward to learning|want to learn|planning to learn|aspiring to learn|wish to learn|eager to learn)\s+([a-zA-Z0-9+#.]+)",
    r"\b(?:familiarity with|basic theoretical knowledge of)\s+([a-zA-Z0-9+#.]+)",
]


def is_in_negative_context(text: str, skill_name: str) -> bool:
    """Check if skill is only mentioned in a context expressing intent to learn rather than practice."""
    lower = text.lower()
    for pattern in NEGATIVE_CONTEXT_PATTERNS:
        match = re.search(pattern, lower)
        if match and skill_name.lower() in match.group(1):
            return True
    return False


class ResumeEvidence:
    """Holds parsed resume skills and section context."""
    def __init__(self, resume_data: dict):
        self.skills_raw: list[str] = resume_data.get("skills") or []
        self.experience_text: str = resume_data.get("experience") or ""
        self.projects_text: str = resume_data.get("projects") or ""
        self.education_text: str = resume_data.get("education") or ""
        self.certifications_text: str = resume_data.get("certifications") or ""
        self.raw_text: str = resume_data.get("raw_text") or ""

        # Map canonical_id -> (display_name, source_section, snippet)
        self.extracted_skills: dict[str, tuple[str, str, str]] = {}
        self._aggregate_all_skills()

    def _aggregate_all_skills(self):
        # 1. Primary Skills Section
        for s in self.skills_raw:
            if not s or not s.strip():
                continue
            res = resolve_canonical_skill(s)
            if res:
                cid, display = res
                self.extracted_skills[cid] = (display, "Skills Section", f"Listed in skills: {s}")
            else:
                norm = normalize_token(s)
                if len(norm) >= 2:
                    self.extracted_skills[norm] = (get_display_name(s), "Skills Section", f"Listed in skills: {s}")

        # 2. Extract from Experience (real project usage)
        if self.experience_text:
            exp_skills = extract_skills_from_text(self.experience_text)
            for disp in exp_skills:
                res = resolve_canonical_skill(disp)
                if res:
                    cid, display = res
                    if cid not in self.extracted_skills:
                        snippet = self._find_context_snippet(self.experience_text, display)
                        if not is_in_negative_context(snippet, display):
                            self.extracted_skills[cid] = (display, "Experience", snippet)

        # 3. Extract from Projects
        if self.projects_text:
            proj_skills = extract_skills_from_text(self.projects_text)
            for disp in proj_skills:
                res = resolve_canonical_skill(disp)
                if res:
                    cid, display = res
                    if cid not in self.extracted_skills:
                        snippet = self._find_context_snippet(self.projects_text, display)
                        if not is_in_negative_context(snippet, display):
                            self.extracted_skills[cid] = (display, "Projects", snippet)

        # 4. Extract from Certifications
        if self.certifications_text:
            cert_skills = extract_skills_from_text(self.certifications_text)
            for disp in cert_skills:
                res = resolve_canonical_skill(disp)
                if res:
                    cid, display = res
                    if cid not in self.extracted_skills:
                        snippet = self._find_context_snippet(self.certifications_text, display)
                        self.extracted_skills[cid] = (display, "Certifications", snippet)

    def _find_context_snippet(self, text: str, term: str) -> str:
        """Find line or short sentence containing the term."""
        lines = text.split("\n")
        for line in lines:
            if re.search(r"\b" + re.escape(term.lower()) + r"\b", line.lower()):
                clean = line.strip()
                return clean[:120] + ("..." if len(clean) > 120 else "")
        return f"Mentioned in {term}"


def match_single_skill(target_skill: str, evidence: ResumeEvidence) -> SkillMatchDetail:
    """
    Match a target JD skill against resume evidence using 4-tier evaluation:
    Exact -> Normalized -> Alias -> Conservative Fuzzy.
    """
    target_clean = target_skill.strip()
    target_res = resolve_canonical_skill(target_clean)
    target_cid = target_res[0] if target_res else normalize_token(target_clean)
    display_name = target_res[1] if target_res else target_clean

    # Tier 1 & 2: Direct or Canonical Match in extracted skills
    if target_cid in evidence.extracted_skills:
        _, section, snippet = evidence.extracted_skills[target_cid]
        return SkillMatchDetail(
            skill=display_name,
            status="matched",
            match_type="canonical",
            evidence=f"{section}: {snippet}",
        )

    # Tier 3: Search raw text for exact word-boundary occurrence
    raw_norm = evidence.raw_text.lower()
    target_lower = target_skill.lower()

    aliases_to_try = [target_lower]
    if target_res and target_cid in SKILL_TAXONOMY:
        aliases_to_try.extend(SKILL_TAXONOMY[target_cid][1])

    for alias in aliases_to_try:
        alias_clean = alias.strip()
        if len(alias_clean) <= 2:
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(alias_clean) + r"(?![a-zA-Z0-9])"
        else:
            pattern = r"\b" + re.escape(alias_clean) + r"\b"

        if re.search(pattern, raw_norm):
            snippet = evidence._find_context_snippet(evidence.raw_text, alias_clean)
            if not is_in_negative_context(snippet, alias_clean):
                return SkillMatchDetail(
                    skill=display_name,
                    status="matched",
                    match_type="exact",
                    evidence=f"Resume: {snippet}",
                )

    # Tier 4: Conservative Fuzzy Matching (only for words with length >= 5, threshold >= 90)
    if len(target_clean) >= 5:
        for cid, (cand_display, section, snippet) in evidence.extracted_skills.items():
            if len(cand_display) >= 5:
                if {"python", "java", "javascript", "c", "c++", "c#", "ruby", "rust", "go"} & {target_cid, cid}:
                    continue

                sim = fuzz.ratio(target_clean.lower(), cand_display.lower())
                if sim >= 90:
                    return SkillMatchDetail(
                        skill=display_name,
                        status="matched",
                        match_type="fuzzy",
                        evidence=f"{section} (Fuzzy {sim}% match with '{cand_display}'): {snippet}",
                    )

    # Not found
    return SkillMatchDetail(
        skill=display_name,
        status="missing",
        match_type="none",
        evidence="Not found in resume",
    )


def match_skills(jd_analysis: JDAnalysis, resume_data: dict) -> Tuple[List[SkillMatchDetail], Dict[str, Any]]:
    """
    Match all JD skills (required and preferred) against resume data.
    """
    evidence = ResumeEvidence(resume_data)
    details: List[SkillMatchDetail] = []

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    required_matched: list[str] = []
    required_missing: list[str] = []
    preferred_matched: list[str] = []
    preferred_missing: list[str] = []

    req_set = set(jd_analysis.required_skills)
    pref_set = set(jd_analysis.preferred_skills)

    for skill in jd_analysis.all_skills:
        match_res = match_single_skill(skill, evidence)
        is_req = skill in req_set or skill not in pref_set
        match_res.is_required = is_req
        details.append(match_res)

        disp = match_res.skill
        if match_res.status == "matched":
            matched_skills.append(disp)
            if is_req:
                required_matched.append(disp)
            else:
                preferred_matched.append(disp)
        else:
            missing_skills.append(disp)
            if is_req:
                required_missing.append(disp)
            else:
                preferred_missing.append(disp)

    matched_keywords = [k for k in jd_analysis.keywords if k in matched_skills]
    missing_keywords = [k for k in jd_analysis.keywords if k in missing_skills]

    summary = {
        "matched_skills": sorted(list(set(matched_skills))),
        "missing_skills": sorted(list(set(missing_skills))),
        "required_matched": sorted(list(set(required_matched))),
        "required_missing": sorted(list(set(required_missing))),
        "preferred_matched": sorted(list(set(preferred_matched))),
        "preferred_missing": sorted(list(set(preferred_missing))),
        "matched_keywords": sorted(list(set(matched_keywords))),
        "missing_keywords": sorted(list(set(missing_keywords))),
    }

    return details, summary


def evaluate_experience(jd_analysis: JDAnalysis, resume_data: dict) -> ExperienceAnalysis:
    """
    Evaluate candidate experience against JD required years.
    Ensures:
    - Education dates/duration are NEVER counted as work experience.
    - Project duration is NOT counted as professional experience unless in experience section.
    - Date ranges are parsed ONLY from dedicated professional/work experience sections.
    - Explicit statements (e.g. '4 years of experience') outside education/projects are captured.
    - If no valid experience evidence exists, returns 'insufficient_evidence'.
    """
    required_years = jd_analysis.min_experience_years
    if required_years is None:
        return ExperienceAnalysis(
            status="not_specified",
            required_years=None,
            estimated_years=None,
            details="Job description does not specify minimum years of experience.",
        )

    exp_section = (resume_data.get("experience") or "").strip()

    # 1. Date ranges: Parse ONLY from explicit professional/work experience section.
    # Education and project dates MUST NEVER be included here.
    calc_years = 0.0
    if exp_section:
        date_ranges = re.findall(
            r"\b(?:[a-zA-Z]{3,9}\s+|\d{1,2}[/-])?(19\d\d|200\d|201\d|202\d)\s*[-–]\s*(?:[a-zA-Z]{3,9}\s+|\d{1,2}[/-])?(19\d\d|200\d|201\d|202\d|present|current)\b",
            exp_section,
            re.I,
        )
        parsed_intervals = []
        for start, end in date_ranges:
            start_y = int(start)
            end_y = 2026 if end.lower() in ["present", "current"] else int(end)
            if start_y <= end_y:
                parsed_intervals.append((start_y, end_y))

        if parsed_intervals:
            parsed_intervals.sort(key=lambda x: (x[0], x[1]))
            merged = [parsed_intervals[0]]
            for current in parsed_intervals[1:]:
                prev_start, prev_end = merged[-1]
                if current[0] <= prev_end:
                    merged[-1] = (prev_start, max(prev_end, current[1]))
                else:
                    merged.append(current)

            for start_y, end_y in merged:
                diff = max(0.0, float(end_y - start_y))
                if diff == 0.0 and start_y <= 2026:
                    diff = 0.5  # Sub-year tenure (e.g. Feb 2025 - Jun 2025)
                calc_years += diff

    # 2. Explicitly stated experience: e.g. "4 years of experience", "3+ years developing"
    # Search in experience section and general summary text, strictly excluding education and projects
    non_edu_text = resume_data.get("raw_text") or ""
    edu_text = resume_data.get("education") or ""
    proj_text = resume_data.get("projects") or ""
    if edu_text:
        non_edu_text = non_edu_text.replace(edu_text, " ")
    if proj_text:
        non_edu_text = non_edu_text.replace(proj_text, " ")

    explicit_search_text = exp_section + "\n" + non_edu_text

    exp_matches = re.findall(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+[a-zA-Z\s]{0,35})?\s*(?:experience|exp|developing|working|engineering)",
        explicit_search_text,
        re.I,
    )
    detected_years = []
    for m in exp_matches:
        try:
            detected_years.append(float(m))
        except ValueError:
            continue

    candidates = detected_years + ([calc_years] if calc_years > 0 else [])
    estimated = max(candidates) if candidates else None

    if estimated is not None:
        if estimated >= required_years:
            status = "meets"
            details = f"Candidate has approximately {estimated:.1f} years of experience, meeting the required {required_years:.1f} years."
        elif estimated >= required_years * 0.6:
            status = "partially_meets"
            details = f"Candidate has approximately {estimated:.1f} years of experience, partially meeting the required {required_years:.1f} years."
        else:
            status = "does_not_meet"
            details = f"Candidate has approximately {estimated:.1f} years of experience, below the required {required_years:.1f} years."
    else:
        status = "insufficient_evidence"
        if exp_section:
            details = f"Experience section is present, but specific total years could not be deterministically calculated. Required: {required_years:.1f} years."
        else:
            details = f"No valid professional work experience detected in resume; insufficient evidence to evaluate required {required_years:.1f} years."

    return ExperienceAnalysis(
        status=status,
        required_years=required_years,
        estimated_years=estimated,
        details=details,
    )


def evaluate_education(jd_analysis: JDAnalysis, resume_data: dict) -> EducationAnalysis:
    """
    Compare JD education requirements with resume education.
    """
    required_edu = jd_analysis.required_education
    if not required_edu:
        return EducationAnalysis(
            status="not_specified",
            required_level="Not Specified",
            detected_education=resume_data.get("education", "")[:60],
            details="Job description does not require a specific degree level.",
        )

    edu_text = (resume_data.get("education") or "") + "\n" + (resume_data.get("raw_text") or "")
    lower = edu_text.lower()

    has_phd = bool(re.search(r"\b(ph\.?d|doctorate)\b", lower))
    has_masters = bool(re.search(r"\b(master'?s?|m\.?tech|mca|m\.?s|m\.?sc)\b", lower))
    has_bachelors = bool(re.search(r"\b(bachelor'?s?|b\.?tech|b\.?e|bca|b\.?s|b\.?sc|undergraduate)\b", lower))
    has_diploma = bool(re.search(r"\b(diploma|associate'?s?)\b", lower))

    detected_level = "None detected"
    meets = False
    partially_meets = False

    if has_phd:
        detected_level = "Doctorate / Ph.D."
        meets = True
    elif has_masters:
        detected_level = "Master's Degree"
        meets = required_edu in ["Master's Degree", "Bachelor's Degree", "Diploma / Associate"]
    elif has_bachelors:
        detected_level = "Bachelor's Degree"
        if required_edu == "Bachelor's Degree" or required_edu == "Diploma / Associate":
            meets = True
        elif required_edu == "Master's Degree":
            partially_meets = True
    elif has_diploma:
        detected_level = "Diploma / Associate"
        if required_edu == "Diploma / Associate":
            meets = True
        else:
            partially_meets = True

    if meets:
        status = "meets"
        details = f"Candidate's education ({detected_level}) meets or exceeds the required level ({required_edu})."
    elif partially_meets:
        status = "partially_meets"
        details = f"Candidate has {detected_level}, whereas the role preferred {required_edu}."
    else:
        status = "does_not_meet"
        details = f"Required education is {required_edu}, but resume indicates {detected_level}."

    return EducationAnalysis(
        status=status,
        required_level=required_edu,
        detected_education=detected_level,
        details=details,
    )


def evaluate_project_relevance(jd_analysis: JDAnalysis, resume_data: dict) -> ProjectRelevanceAnalysis:
    """
    Evaluate whether resume projects actively employ technologies required in the JD.
    """
    proj_text = resume_data.get("projects") or ""
    max_score = 15.0

    if not proj_text.strip():
        return ProjectRelevanceAnalysis(
            score=0.0,
            max_score=max_score,
            matched_technologies=[],
            details="No projects section found in resume.",
        )

    proj_skills = extract_skills_from_text(proj_text)
    jd_skills = set(jd_analysis.all_skills)

    matched_techs = [s for s in proj_skills if s in jd_skills]

    if not jd_skills:
        return ProjectRelevanceAnalysis(
            score=12.0,
            max_score=max_score,
            matched_technologies=proj_skills[:5],
            details="Projects are documented in resume.",
        )

    match_ratio = len(matched_techs) / max(1, min(len(jd_skills), 6))
    score = min(max_score, round(match_ratio * max_score, 1))

    return ProjectRelevanceAnalysis(
        score=score,
        max_score=max_score,
        matched_technologies=matched_techs,
        details=f"Projects demonstrate {len(matched_techs)} target technologies: {', '.join(matched_techs) if matched_techs else 'None'}.",
    )
