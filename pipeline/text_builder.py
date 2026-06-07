import re
from typing import Dict, Any

def build_candidate_text(candidate: Dict[str, Any]) -> str:
    """
    Constructs a rich textual representation of a candidate profile to be used
    for semantic matching with the job description.
    
    Includes headline, summary, current title, career history titles & descriptions,
    education fields, and skills.
    
    Args:
        candidate: Candidate profile dictionary.
        
    Returns:
        A unified clean string containing candidate's career narrative.
    """
    profile = candidate.get("profile", {})
    headline = profile.get("headline", "")
    summary = profile.get("summary", "")
    current_title = profile.get("current_title", "")
    
    # Start with core profile description
    text_parts = []
    if current_title:
        text_parts.append(f"Current role: {current_title}.")
    if headline:
        text_parts.append(headline)
    if summary:
        text_parts.append(summary)
        
    # Append career history (title, company, description)
    career_history = candidate.get("career_history", [])
    if career_history:
        text_parts.append("Work Experience:")
        for role in career_history:
            title = role.get("title", "")
            company = role.get("company", "")
            desc = role.get("description", "")
            duration = role.get("duration_months", 0)
            
            role_str = f"- {title} at {company}"
            if duration:
                role_str += f" ({duration} months)"
            role_str += f": {desc}"
            text_parts.append(role_str)
            
    # Append skills (including proficiency)
    skills = candidate.get("skills", [])
    if skills:
        skills_str = "Skills: " + ", ".join(
            f"{s.get('name', '')} ({s.get('proficiency', '')})"
            for s in skills if s.get("name")
        )
        text_parts.append(skills_str)
        
    # Append education (degree and field of study)
    education = candidate.get("education", [])
    if education:
        edu_parts = []
        for edu in education:
            deg = edu.get("degree", "")
            field = edu.get("field_of_study", "")
            inst = edu.get("institution", "")
            if deg or field:
                edu_parts.append(f"{deg} in {field} from {inst}")
        if edu_parts:
            text_parts.append("Education: " + "; ".join(edu_parts))
            
    # Join and clean up whitespace
    full_text = " ".join(text_parts)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    return full_text
