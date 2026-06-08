import os
import sys
from typing import Dict, Any, List

# Add the parent directory to the path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.skill_taxonomy import SKILL_GROUPS, NICE_TO_HAVE_KEYWORDS, normalize_skill_name

def score_skill_depth(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates Lens 2: Skill Depth & Breadth.
    
    Scores each of the 4 key skill groups based on candidate's matching skills:
      skill_score = proficiency * duration_factor * endorsement_factor * assessment_factor
      
    Where:
      - proficiency: beginner (0.2), intermediate (0.5), advanced (0.8), expert (1.0)
      - duration_factor: min(duration_months / 24, 1.0)
      - endorsement_factor: min(endorsements / 20, 1.0) * 0.3 + 0.7 (scales from 0.7 to 1.0)
      - assessment_factor: score / 100 if platform assessment exists, else 0.7 (neutral)
      
    Weighted sum of max skill scores per group forms the base score.
    Nice-to-have skills add a small boost (up to 0.06).
    Anti-keyword-stuffing penalty (x0.3 multiplier) is applied if a candidate claims 
    >5 'expert' skills with an average duration of <6 months.
    
    Returns:
        dict containing "score", "explanation", and "details" dict.
    """
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    assessment_scores = signals.get("skill_assessment_scores", {})
    
    # 1. Normalize candidate skills and map them
    normalized_skills = []
    for s in skills:
        name = s.get("name", "")
        norm_name = normalize_skill_name(name)
        if norm_name:
            normalized_skills.append({
                "name": norm_name,
                "proficiency": s.get("proficiency", "beginner"),
                "endorsements": s.get("endorsements", 0),
                "duration_months": s.get("duration_months", 0)
            })
            
    # 2. Score each skill group
    group_scores = {}
    best_skills = []
    
    proficiency_map = {
        "beginner": 0.2,
        "intermediate": 0.5,
        "advanced": 0.8,
        "expert": 1.0
    }
    
    for g_key, group in SKILL_GROUPS.items():
        max_skill_score = 0.0
        best_skill_name = None
        
        for s in normalized_skills:
            # Check if skill matches group keywords
            is_match = any(kw in s["name"] for kw in group["keywords"])
            
            if is_match:
                prof = proficiency_map.get(s["proficiency"], 0.2)
                dur_factor = min(s["duration_months"] / 24.0, 1.0)
                end_factor = min(s["endorsements"] / 20.0, 1.0) * 0.3 + 0.7
                
                verify_score = None
                for k, v in assessment_scores.items():
                    if normalize_skill_name(k) == s["name"]:
                        verify_score = v
                        break
                        
                if verify_score is not None:
                    assess_factor = verify_score / 100.0
                else:
                    assess_factor = 0.7
                    
                skill_score = prof * dur_factor * end_factor * assess_factor
                
                if skill_score > max_skill_score:
                    max_skill_score = skill_score
                    best_skill_name = s["name"]
                    
        group_scores[g_key] = max_skill_score
        if best_skill_name:
            best_skills.append(best_skill_name)
            
    # Compute base weighted score
    base_score = sum(group_scores[gk] * SKILL_GROUPS[gk]["weight"] for gk in SKILL_GROUPS)
    
    # 3. Nice-to-have skill boost
    nice_to_have_count = 0
    matched_nice_to_haves = []
    
    for s in normalized_skills:
        if any(nth_kw in s["name"] for nth_kw in NICE_TO_HAVE_KEYWORDS):
            nice_to_have_count += 1
            matched_nice_to_haves.append(s["name"])
            
    # Boost by 0.02 per nice-to-have, capped at 0.06
    nice_to_have_boost = min(nice_to_have_count * 0.02, 0.06)
    
    # 4. Anti-Keyword-Stuffing Penalty
    expert_skills = [s for s in normalized_skills if s["proficiency"] == "expert"]
    stuffing_penalty = 1.0
    stuffing_flagged = False
    
    if len(expert_skills) > 5:
        avg_duration = sum(s["duration_months"] for s in expert_skills) / len(expert_skills)
        if avg_duration < 6.0:
            stuffing_penalty = 0.3
            stuffing_flagged = True
            
    # Final Score
    final_score = round((base_score + nice_to_have_boost) * stuffing_penalty, 4)
    final_score = min(final_score, 1.0)
    
    # Construct natural language reasoning
    explanation_parts = []
    if best_skills:
        explanation_parts.append(f"Demonstrated core skills: {', '.join(best_skills)}.")
    else:
        explanation_parts.append("No core JD matching skills detected.")
        
    if nice_to_have_boost > 0:
        explanation_parts.append(f"Nice-to-have boost from: {', '.join(matched_nice_to_haves[:3])}.")
        
    if stuffing_flagged:
        explanation_parts.append("WARNING: Severe penalty applied for keyword-stuffing anti-pattern (too many expert skills with near-zero duration).")
        
    explanation = " ".join(explanation_parts)
    
    return {
        "score": final_score,
        "explanation": explanation,
        "details": {
            "group_scores": group_scores,
            "nice_to_have_boost": nice_to_have_boost,
            "stuffing_penalty": stuffing_penalty,
            "expert_count": len(expert_skills),
            "base_score": base_score
        }
    }
