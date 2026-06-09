import os
import sys
from typing import Dict, Any

def score_evidence_strength(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates Lens 6: Evidence Strength.
    
    Measures the quality, completeness, and verification level of the candidate's profile:
      - Profile completeness score
      - Email, phone, and LinkedIn verification status
      - Social proof (saved by recruiters, profile views, search appearances)
      - GitHub activity score (penalizes nothing if missing, rewards if active)
      - Redrob skill assessment scores (measures verified test results)
      
    Returns:
        dict containing "score", "explanation", and "details" dict.
    """
    signals = candidate.get("redrob_signals", {})
    
    # 1. Profile completeness (0-100 score)
    completeness = signals.get("profile_completeness_score", 0.0) / 100.0
    
    # 2. Account verification level (0 to 1.0)
    verified_email = signals.get("verified_email", False)
    verified_phone = signals.get("verified_phone", False)
    linkedin_connected = signals.get("linkedin_connected", False)
    
    verified_score = (
        float(verified_email) +
        float(verified_phone) +
        float(linkedin_connected)
    ) / 3.0
    
    # 3. Social proof from recruiters (clamped scaling)
    saves = signals.get("saved_by_recruiters_30d", 0)
    saved_score = min(saves / 10.0, 1.0)  # Capped at 10 saves
    
    views = signals.get("profile_views_received_30d", 0)
    views_score = min(views / 20.0, 1.0)  # Capped at 20 views
    
    searches = signals.get("search_appearance_30d", 0)
    search_score = min(searches / 100.0, 1.0)  # Capped at 100 search appearances
    
    # 4. GitHub activity (neutral if missing, rewarded if active)
    github = signals.get("github_activity_score", -1.0)
    if github == -1.0:
        github_score = 0.3  # Neutral score
        github_desc = "no GitHub linked"
    else:
        github_score = 0.3 + 0.7 * (github / 100.0)
        github_desc = f"GitHub activity: {github:.1f}/100"
        
    # 5. Redrob Platform Assessment scores (neutral if none, based on scores if taken)
    assessments = signals.get("skill_assessment_scores", {})
    if assessments:
        avg_assessment = sum(assessments.values()) / len(assessments)
        assessment_score = avg_assessment / 100.0
        assess_desc = f"{len(assessments)} skill assessments completed (avg score: {avg_assessment:.1f})"
    else:
        assessment_score = 0.3  # Neutral score
        assess_desc = "no platform skill assessments taken"
        
    # Base weighted score calculation
    base_score = (
        0.20 * completeness +
        0.15 * verified_score +
        0.15 * saved_score +
        0.10 * views_score +
        0.05 * search_score +
        0.20 * github_score +
        0.15 * assessment_score
    )
    
    final_score = round(base_score, 4)
    final_score = min(final_score, 1.0)
    final_score = max(final_score, 0.0)
    
    # Natural language explanation
    verification_pct = verified_score * 100.0
    explanation = (
        f"Profile completeness is {completeness*100:.1f}%. "
        f"Verification status: {verification_pct:.1f}% (email/phone/socials). "
        f"Platform proof: {assess_desc}. "
        f"Candidate has {github_desc}."
    )
    
    return {
        "score": final_score,
        "explanation": explanation,
        "details": {
            "completeness_score": completeness,
            "verification_score": verified_score,
            "saved_score": saved_score,
            "views_score": views_score,
            "search_score": search_score,
            "github_score": github_score,
            "assessment_score": assessment_score,
            "assessments_count": len(assessments)
        }
    }
