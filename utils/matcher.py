# utils/matcher.py
from utils.semantic_matcher import calculate_semantic_match

def calculate_experience_score(candidate_years: float, required_years: float) -> tuple[float, list]:
    """Calculates experience fit score with penalties for under/over-qualification."""
    warnings = []
    
    if not required_years or required_years <= 0:
        return 100.0, warnings
    
    # 1. Under-qualified Case
    if candidate_years < required_years:
        ratio = candidate_years / required_years
        gap = round(required_years - candidate_years, 1)
        warnings.append(f"⚠️ Under-qualified: Job requires {required_years} yrs, candidate has {candidate_years} yrs (Gap: {gap} yrs).")
        
        if ratio < 0.5:
            return round(ratio * 50.0, 1), warnings
        return round(ratio * 100.0, 1), warnings

    # 2. Perfect or Near-Ideal Fit (0 to 3 years above requirement)
    gap = candidate_years - required_years
    if gap <= 3.0:
        return 100.0, warnings

    # 3. Over-qualified Case (4+ years above requirement)
    over_qual_score = max(50.0, 100.0 - ((gap - 3.0) * 5.0))
    warnings.append(f"ℹ️ Over-qualified: Job requires {required_years} yrs, candidate has {candidate_years} yrs (Exceeds by {round(gap, 1)} yrs).")
    
    return round(over_qual_score, 1), warnings


def evaluate_composite_fit(
    candidate_skills: list,
    candidate_certs: list,
    candidate_years: float,
    job_skills: list,
    job_certs: list,
    required_years: float
) -> dict:
    
    # 1. Skill Match
    skill_score, matched_skills, missing_skills = calculate_semantic_match(
        candidate_skills, job_skills
    )
    
    # 2. Experience Match
    exp_score, warnings = calculate_experience_score(candidate_years, required_years)
    
    # 3. Certification Match & Weight Adjustment
    if not job_certs:
        # No certs required: Re-weight Skills (70%) and Experience (30%)
        cert_score = None  # Signal that no certs are required
        final_score = round((skill_score * 0.70) + (exp_score * 0.30), 1)
    else:
        if not candidate_certs:
            cert_score = 0.0
        else:
            cert_score, _, _ = calculate_semantic_match(candidate_certs, job_certs)
            
        final_score = round((skill_score * 0.60) + (exp_score * 0.30) + (cert_score * 0.10), 1)

    return {
        "final_score": final_score,
        "skill_score": skill_score,
        "experience_score": exp_score,
        "certification_score": cert_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "required_certs": job_certs,  # Pass required certs to UI
        "warnings": warnings,
        "required_years": required_years
    }