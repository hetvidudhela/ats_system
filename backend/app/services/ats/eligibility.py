"""
eligibility.py
==============
Eligibility Assessment Engine for TrueHire ATS Resume Analyzer.

Evaluates deterministic criteria to detect if a candidate may be ineligible
for a job position based on:
1. Overall ATS score strictly below 40%.
2. Zero matching required skills or very low matching-skill ratio (< 25% when >= 3 required).
3. Mandatory eligibility criteria explicitly not fulfilled or unverifiable
   (education/degree level, minimum years of experience).

Important Design Rules:
- Distinguishes confirmed mismatches (potentially_ineligible) from missing / unverifiable information (requirements_not_verified).
- Does not infer a failed criterion merely because the resume does not mention it.
- Never claims guaranteed hiring eligibility.
- Deduplicates all specific reasons.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Documented Thresholds
MIN_ATS_SCORE_THRESHOLD = 40
MIN_REQUIRED_SKILLS_FOR_RATIO = 3
LOW_SKILL_RATIO_THRESHOLD = 0.25  # 25%


class EligibilityAssessment(BaseModel):
    """
    Structured eligibility evaluation result.
    Compatible with frontend, backend, and extension models.
    """
    eligible: Optional[bool] = Field(
        default=None,
        description="True if no issues detected, False if confirmed mismatch, None if unverified/unknown",
    )
    warning: bool = Field(
        default=False,
        description="True if an eligibility warning banner should be displayed to the user",
    )
    status: str = Field(
        default="no_major_issues_detected",
        description="'potentially_ineligible', 'requirements_not_verified', or 'no_major_issues_detected'",
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="List of specific, human-readable reasons explaining the eligibility status",
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def evaluate_candidate_eligibility(
    overall_score: int,
    skills_summary: Dict[str, Any],
    exp_analysis: Any,
    edu_analysis: Any,
    jd_analysis: Any,
) -> EligibilityAssessment:
    """
    Evaluate candidate eligibility against job requirements.

    Args:
        overall_score: Integer ATS score between 0 and 100.
        skills_summary: Dictionary containing required_matched and required_missing lists.
        exp_analysis: ExperienceAnalysis model or dict.
        edu_analysis: EducationAnalysis model or dict.
        jd_analysis: JDAnalysis dataclass or None.

    Returns:
        EligibilityAssessment instance with warning flag, status, and specific reasons.
    """
    reasons: List[str] = []
    has_confirmed_ineligibility = False
    has_unverified = False

    # -------------------------------------------------------------------------
    # Rule 1: ATS score strictly below 40%
    # -------------------------------------------------------------------------
    if overall_score < MIN_ATS_SCORE_THRESHOLD:
        has_confirmed_ineligibility = True
        reasons.append(f"ATS score is {overall_score}%, strictly below the {MIN_ATS_SCORE_THRESHOLD}% minimum threshold.")

    # -------------------------------------------------------------------------
    # Rule 2: Zero matching required skills OR very low matching-skill ratio
    # -------------------------------------------------------------------------
    required_matched = list(skills_summary.get("required_matched", []) or [])
    required_missing = list(skills_summary.get("required_missing", []) or [])
    total_required = len(required_matched) + len(required_missing)

    all_jd_skills = getattr(jd_analysis, "all_skills", []) or []
    has_any_jd_skills = total_required > 0 or len(all_jd_skills) > 0

    if has_any_jd_skills:
        if total_required > 0:
            if len(required_matched) == 0:
                has_confirmed_ineligibility = True
                reasons.append(f"Zero matching required skills (0 of {total_required} required skills identified).")
            elif total_required >= MIN_REQUIRED_SKILLS_FOR_RATIO:
                ratio = len(required_matched) / total_required
                if ratio < LOW_SKILL_RATIO_THRESHOLD:
                    has_confirmed_ineligibility = True
                    matched_pct = int(round(ratio * 100))
                    threshold_pct = int(round(LOW_SKILL_RATIO_THRESHOLD * 100))
                    reasons.append(
                        f"Very few required skills matched: only {len(required_matched)} of {total_required} matched ({matched_pct}%, threshold is {threshold_pct}%)."
                    )
        elif len(all_jd_skills) > 0 and len(skills_summary.get("matched_skills", []) or []) == 0:
            # Fallback if section header parsing didn't separate required vs preferred
            has_confirmed_ineligibility = True
            reasons.append(f"No matching skills identified out of {len(all_jd_skills)} target job skills.")

    # -------------------------------------------------------------------------
    # Rule 3: Mandatory Eligibility Criterion (Education & Experience)
    # -------------------------------------------------------------------------
    # 3A. Education Requirements
    edu_dict: Dict[str, Any] = (
        edu_analysis.model_dump()
        if hasattr(edu_analysis, "model_dump")
        else (edu_analysis if isinstance(edu_analysis, dict) else {})
    )
    required_edu = edu_dict.get("required_level", "")
    edu_status = edu_dict.get("status", "not_specified")
    detected_edu = (edu_dict.get("detected_education") or "").strip()

    if required_edu and required_edu != "Not Specified":
        if edu_status == "does_not_meet":
            if not detected_edu or detected_edu.lower() in ["none detected", "none", "not specified"]:
                has_unverified = True
                reasons.append(f"Required {required_edu} could not be verified from the resume.")
            else:
                has_confirmed_ineligibility = True
                reasons.append(f"Candidate holds {detected_edu}, which does not fulfill the mandatory {required_edu} requirement.")
        elif edu_status == "insufficient_evidence":
            has_unverified = True
            reasons.append(f"Required {required_edu} could not be verified from the resume.")

    # 3B. Experience Requirements
    exp_dict: Dict[str, Any] = (
        exp_analysis.model_dump()
        if hasattr(exp_analysis, "model_dump")
        else (exp_analysis if isinstance(exp_analysis, dict) else {})
    )
    required_years = exp_dict.get("required_years")
    exp_status = exp_dict.get("status", "not_specified")
    estimated_years = exp_dict.get("estimated_years")

    if required_years is not None and required_years > 0:
        if exp_status == "does_not_meet":
            if estimated_years is not None:
                has_confirmed_ineligibility = True
                reasons.append(
                    f"Candidate has approximately {estimated_years:.1f} years of experience, below the required {required_years:.1f} years."
                )
            else:
                has_unverified = True
                reasons.append(f"Required minimum experience ({required_years:.1f} years) could not be verified from the resume.")
        elif exp_status == "insufficient_evidence":
            has_unverified = True
            reasons.append(f"Required minimum experience ({required_years:.1f} years) could not be verified from the resume.")

    # -------------------------------------------------------------------------
    # Deduplication & Status Resolution
    # -------------------------------------------------------------------------
    unique_reasons: List[str] = []
    seen = set()
    for r in reasons:
        clean_r = r.strip()
        if clean_r and clean_r not in seen:
            unique_reasons.append(clean_r)
            seen.add(clean_r)

    if has_confirmed_ineligibility:
        return EligibilityAssessment(
            eligible=False,
            warning=True,
            status="potentially_ineligible",
            reasons=unique_reasons,
        )
    elif has_unverified:
        return EligibilityAssessment(
            eligible=None,
            warning=True,
            status="requirements_not_verified",
            reasons=unique_reasons,
        )
    else:
        return EligibilityAssessment(
            eligible=True,
            warning=False,
            status="no_major_issues_detected",
            reasons=[],
        )
