import os
import sys
from typing import Dict, Any

def generate_candidate_reasoning(
    candidate: Dict[str, Any],
    l1_res: Dict[str, Any],
    l2_res: Dict[str, Any],
    l3_res: Dict[str, Any],
    l4_res: Dict[str, Any],
    l5_res: Dict[str, Any],
    l6_res: Dict[str, Any]
) -> str:
    """
    Assembles a compositional, natural language explanation of a candidate's fit 
    based on the factual output of all 6 lenses.
    
    Ensures:
      - Specific facts (years of experience, current title, named skills, location)
      - JD connections (specific matching core skills, production deployment keywords)
      - Gaps/Concerns (mentions of any warning signals or red flags)
      - Avoids templates (constructed dynamically based on active signals)
      - Output is 1-2 sentences.
      
    Args:
        candidate: Candidate dictionary.
        l1_res to l6_res: Results dictionaries returned by each lens.
        
    Returns:
        str: Factual reasoning text.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    
    yoe = profile.get("years_of_experience", 0.0)
    current_title = profile.get("current_title", "Engineer")
    location = profile.get("location", "India")
    
    # 1. Main Professional Identity & YOE
    # We will build parts dynamically
    parts = []
    
    role_desc = f"{yoe:.1f} yrs experience as a {current_title}"
    
    # 2. Add core technical strengths (from Lens 2)
    # Note: best_skills was constructed as a list, but wait, l2_res['explanation'] has text.
    # We can retrieve skills from the candidate normalized skills or directly from l2_res
    # Let's extract best matching skills
    from config.skill_taxonomy import SKILL_GROUPS, normalize_skill_name
    skills = candidate.get("skills", [])
    matched_core_skills = []
    for s in skills:
        norm_name = normalize_skill_name(s.get("name", ""))
        # Check if it matches any group
        is_match = False
        for g_key, group in SKILL_GROUPS.items():
            if any(kw in norm_name for kw in group["keywords"]):
                is_match = True
                break
        if is_match and s.get("proficiency") in ["advanced", "expert"]:
            matched_core_skills.append(s.get("name"))
            
    if matched_core_skills:
        skills_str = f"with expertise in {', '.join(matched_core_skills[:3])}"
    else:
        skills_str = ""
        
    # 3. Add production scaling keyword evidence (from Lens 1)
    prod_hits = l1_res.get("details", {}).get("keyword_hits", [])
    if prod_hits:
        actions = []
        if any(k in prod_hits for k in ["scale", "system design", "real users"]):
            actions.append("scaling systems")
        if any(k in prod_hits for k in ["deployed", "shipped", "production"]):
            actions.append("deploying to production")
        if "a/b test" in prod_hits:
            actions.append("running A/B tests")
            
        if actions:
            prod_str = f"and experience " + " and ".join(actions[:2])
        else:
            prod_str = "and experience in production deployment"
    else:
        prod_str = ""
        
    # Combine identity, skills, and production
    first_sentence_parts = [role_desc]
    if skills_str:
        first_sentence_parts.append(skills_str)
    if prod_str:
        first_sentence_parts.append(prod_str)
        
    first_sentence = " ".join(first_sentence_parts) + "."
    parts.append(first_sentence)
    
    # 4. Behavioral & Engagement Profile
    recency_days = l4_res.get("details", {}).get("recency_days", 90)
    notice_days = signals.get("notice_period_days", 90)
    
    if recency_days <= 30:
        activity_str = "highly active recently"
    else:
        activity_str = "moderately active"
        
    second_sentence_parts = [
        f"Located in {location}, candidate is {activity_str} with {notice_days}-day notice"
    ]
    
    # 5. Concerns / Gaps (from Lens 5)
    red_flags = l5_res.get("flags", [])
    if red_flags:
        # Avoid naming it "RED FLAG" if it's a minor concern, use "Concern:"
        second_sentence_parts.append(f"but has gaps: {red_flags[0]}")
    else:
        # Add small positive evidence instead of concern if clean
        gh_score = signals.get("github_activity_score", -1)
        if gh_score > 50:
            second_sentence_parts.append(f"and shows strong social evidence ({gh_score:.0f}/100 GitHub activity)")
            
    second_sentence = " ".join(second_sentence_parts) + "."
    parts.append(second_sentence)
    
    # Join parts into 1-2 sentence text
    reasoning = " ".join(parts)
    
    # Final cleanup (replace multiple spaces, clamp lengths)
    reasoning = " ".join(reasoning.split())
    if len(reasoning) > 250:
        reasoning = reasoning[:247] + "..."
        
    return reasoning
