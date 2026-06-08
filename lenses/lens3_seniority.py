import os
import sys
from typing import Dict, Any, List

# Add the parent directory to the path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.jd_requirements import JD_REQUIREMENTS

def score_seniority_match(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates Lens 3: Seniority & Level Match.
    
    Scores are based on:
    1. Experience Fit: Total Years of Experience (YOE) relative to the JD range (5-9 years)
    2. Career Progression: Progression as an Individual Contributor (IC) rather than pure management/non-tech
    3. Industry Trajectory: Focus on product companies vs IT services/consulting firms
    4. Job-Hopping Penalty: Penalty for frequent job switches (<18 months per company)
    
    Formula:
        Raw Score = 0.40 * Experience Score + 0.35 * Progression Score + 0.25 * Industry Score
        Final Score = Raw Score * Job Hopping Penalty
        
    Returns:
        dict containing "score", "explanation", and "details" dict.
    """
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    
    # 1. Experience Score (JD: 5-9 years, flexible)
    yoe = profile.get("years_of_experience", 0.0)
    
    if 5.0 <= yoe <= 9.0:
        exp_score = 1.0
    elif (4.0 <= yoe < 5.0) or (9.0 < yoe <= 12.0):
        exp_score = 0.8  # close enough
    elif (3.0 <= yoe < 4.0) or (12.0 < yoe <= 15.0):
        exp_score = 0.5  # marginal
    else:
        exp_score = 0.2  # too junior or too senior
        
    # 2. Career Progression Score
    # Looking for Individual Contributor (IC) track progression
    titles = [role.get("title", "") for role in career_history]
    titles_lower = [t.lower() for t in titles if t]
    
    has_ic_title = any(
        any(eng in t for eng in ["engineer", "scientist", "developer", "programmer", "analyst"])
        for t in titles_lower
    )
    has_senior_ic_title = any(
        any(sen in t for sen in ["senior", "lead", "staff", "principal", "architect"])
        for t in titles_lower
        if any(eng in t for eng in ["engineer", "scientist", "developer", "programmer"])
    )
    
    # Check current title specifically
    current_title_lower = profile.get("current_title", "").lower()
    is_current_management = any(m in current_title_lower for m in ["manager", "director", "head", "vp"])
    is_current_ic = any(ic in current_title_lower for ic in ["engineer", "scientist", "developer", "programmer"])
    
    if has_senior_ic_title:
        # Strong technical progression
        prog_score = 1.0
        prog_desc = "senior IC engineering track"
    elif is_current_ic:
        # Standard IC track
        prog_score = 0.8
        prog_desc = "IC engineering track"
    elif is_current_management and has_ic_title:
        # Moved to manager from IC (startup founding teams still value this)
        prog_score = 0.6
        prog_desc = "engineering management with technical background"
    elif has_ic_title:
        # Has had some engineering roles in past
        prog_score = 0.5
        prog_desc = "some technical engineering history"
    else:
        # Purely non-technical or management history
        prog_score = 0.2
        prog_desc = "non-technical career track"
        
    # 3. Industry Trajectory Score (Product > Services)
    consulting_firms = JD_REQUIREMENTS["anti_signals"]["consulting_firms"]
    industries = [role.get("industry", "") for role in career_history]
    companies = [role.get("company", "") for role in career_history]
    
    product_company_count = 0
    total_companies = max(len(companies), 1)
    
    for comp, ind in zip(companies, industries):
        if not comp:
            continue
        # Check if company is in consulting firms list
        is_consulting = any(cf.lower() in comp.lower() for cf in consulting_firms)
        # Check if industry is service-oriented
        is_services_ind = any(si.lower() in ind.lower() for si in ["services", "consulting", "outsourcing", "agency"])
        
        if not is_consulting and not is_services_ind:
            product_company_count += 1
            
    product_ratio = product_company_count / total_companies
    industry_score = round(0.3 + 0.7 * product_ratio, 4)
    
    # 4. Job-Hopping Penalty (Stability Check)
    # Penalize if they switch companies too frequently (<18 months average, or 3+ short roles)
    short_duration_roles = [
        role for role in career_history 
        if role.get("duration_months", 0) < JD_REQUIREMENTS["anti_signals"]["job_hopping_threshold_months"]
        and not role.get("is_current", False)  # Current role is allowed to be short since they are active
    ]
    
    if len(short_duration_roles) >= JD_REQUIREMENTS["anti_signals"]["job_hopping_count_limit"]:
        hop_penalty = 0.7  # 30% penalty
        stability_desc = "frequent company switching (potential title-chaser)"
    elif len(short_duration_roles) == 2:
        hop_penalty = 0.9  # 10% penalty
        stability_desc = "moderate job-hopping"
    else:
        hop_penalty = 1.0  # no penalty
        stability_desc = "stable career history"
        
    # Compute Raw and Final scores
    raw_score = 0.40 * exp_score + 0.35 * prog_score + 0.25 * industry_score
    final_score = round(raw_score * hop_penalty, 4)
    
    # Build explanation
    explanation = (
        f"{yoe:.1f} years of experience ({'ideal' if exp_score == 1.0 else 'marginal' if exp_score == 0.5 else 'suboptimal'} range). "
        f"Career path shows {prog_desc}. "
        f"Product-company exposure is {product_ratio*100:.1f}%. "
        f"Career stability is characterized as {stability_desc}."
    )
    
    return {
        "score": final_score,
        "explanation": explanation,
        "details": {
            "experience_years": yoe,
            "experience_score": exp_score,
            "progression_score": prog_score,
            "industry_score": industry_score,
            "hop_penalty": hop_penalty,
            "product_company_ratio": product_ratio
        }
    }
