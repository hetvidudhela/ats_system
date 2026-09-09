"""
suggestions.py
==============
Deterministic, actionable suggestion generator based on actual ATS deficiencies.
Follows ethical ATS guidelines: never instructs users to fabricate skills.
"""

from typing import Any, Dict, List
from app.services.ats.models import ExperienceAnalysis, EducationAnalysis, ProjectRelevanceAnalysis


def generate_actionable_suggestions(
    skills_summary: Dict[str, Any],
    exp_analysis: ExperienceAnalysis,
    edu_analysis: EducationAnalysis,
    proj_analysis: ProjectRelevanceAnalysis,
    resume_data: dict,
) -> List[str]:
    """
    Generate prioritized, actionable suggestions tailored to specific resume gaps.
    """
    suggestions: List[str] = []

    # 1. Missing Required Skills (Highest Priority)
    req_missing = skills_summary.get("required_missing", [])
    if req_missing:
        top_missing = req_missing[:3]
        if len(top_missing) == 1:
            suggestions.append(
                f"The job requires '{top_missing[0]}'. If you have hands-on experience with it, consider highlighting it prominently in your Skills and Experience sections."
            )
        else:
            missing_str = ", ".join(f"'{s}'" for s in top_missing)
            suggestions.append(
                f"Core required skills missing from your resume: {missing_str}. If you have worked with these technologies, ensure they are explicitly named."
            )

    # 2. Missing Preferred Skills
    pref_missing = skills_summary.get("preferred_missing", [])
    if pref_missing and len(suggestions) < 4:
        top_pref = pref_missing[:2]
        pref_str = ", ".join(f"'{s}'" for s in top_pref)
        suggestions.append(
            f"Bonus qualification skills not found: {pref_str}. Adding these can give your application a competitive edge if you have relevant experience."
        )

    # 3. Missing Methodologies / Keywords
    missing_kw = skills_summary.get("missing_keywords", [])
    if missing_kw and len(suggestions) < 5:
        kw_str = ", ".join(f"'{k}'" for k in missing_kw[:2])
        suggestions.append(
            f"Consider mentioning industry practices like {kw_str} within your bullet points to demonstrate modern development workflow familiarity."
        )

    # 4. Project Relevance
    if proj_analysis.score < 10.0 and len(suggestions) < 5:
        suggestions.append(
            "Detail the specific tools, libraries, and architecture used in your projects. Measurable achievements (e.g., 'reduced latency by 20%') significantly improve ATS ranking."
        )

    # 5. Experience Clarity
    if exp_analysis.status in ["partially_meets", "insufficient_evidence"] and len(suggestions) < 5:
        suggestions.append(
            "State your employment dates and total years of technical experience clearly (e.g., '3 years of backend engineering') to help ATS parsers calculate tenure."
        )

    # 6. Contact & Professional Presence
    if not resume_data.get("linkedin") and not resume_data.get("github") and len(suggestions) < 6:
        suggestions.append(
            "Add clickable links to your LinkedIn profile and GitHub repository in the contact header for recruiter verification."
        )

    # If no deficiencies found (exceptional resume)
    if not suggestions:
        suggestions.append(
            "Excellent alignment with the job description! Your resume demonstrates core skills, relevant project experience, and clear structural formatting."
        )

    return suggestions
