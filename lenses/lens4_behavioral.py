import os
import sys
import datetime
from typing import Dict, Any

# Add the parent directory to path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.jd_requirements import JD_REQUIREMENTS

def score_behavioral_hirability(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates Lens 4: Behavioral Hirability.
    
    Combines simulated platform behavior and availability signals:
      - Last active recency (days since last active)
      - Recruiter response rate & response time (responsiveness)
      - Interview completion rate (reliability)
      - Notice period (ideal <= 30 days)
      - Location fit (India preferred, Noida/Pune preferred)
      - Open-to-work status (boost/multiplier)
      
    Returns:
        dict containing "score", "explanation", and "details" dict.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    
    # 1. Recency of login
    # Platform reference date is June 1, 2026
    ref_date = datetime.datetime(2026, 6, 1)
    last_active_str = signals.get("last_active_date", "")
    recency_days = 365.0  # Default to very inactive
    
    if last_active_str:
        try:
            last_active = datetime.datetime.strptime(last_active_str, "%Y-%m-%d")
            recency_days = (ref_date - last_active).days
        except ValueError:
            pass
            
    if recency_days <= 14:
        recency_score = 1.0
    elif recency_days <= 30:
        recency_score = 0.9
    elif recency_days <= 90:
        recency_score = 0.6
    elif recency_days <= 180:
        recency_score = 0.3
    else:
        recency_score = 0.1
        
    # 2. Recruiter response rate (0.0 to 1.0)
    response_rate = signals.get("recruiter_response_rate", 0.0)
    
    # 3. Response time (fast response is better)
    rt = signals.get("avg_response_time_hours", 200.0)
    response_time_score = max(0.0, 1.0 - (rt / 200.0))  # Scale 0-200 hrs to 1-0
    
    # 4. Interview completion rate (0.0 to 1.0)
    interview_score = signals.get("interview_completion_rate", 0.0)
    
    # 5. Notice period (JD prefers <=30 days)
    np_days = signals.get("notice_period_days", 90)
    if np_days <= 30:
        notice_score = 1.0
    elif np_days <= 60:
        notice_score = 0.7
    elif np_days <= 90:
        notice_score = 0.4
    else:
        notice_score = 0.2
        
    # 6. Location and Relocation
    loc = profile.get("location", "")
    country = profile.get("country", "")
    willing_relocate = signals.get("willing_to_relocate", False)
    
    preferred_cities = JD_REQUIREMENTS["location_preferred"]
    
    # Check if candidate lives in one of our preferred cities in India
    is_preferred_city = any(city.lower() in loc.lower() for city in preferred_cities)
    
    if is_preferred_city or country.lower() == "india":
        location_score = 1.0
    elif willing_relocate:
        location_score = 0.6  # willing to move
    else:
        location_score = 0.3  # international, not willing to move
        
    # 7. Verification signals
    verified_email = signals.get("verified_email", False)
    verified_phone = signals.get("verified_phone", False)
    linkedin_connected = signals.get("linkedin_connected", False)
    
    verification_bonus = (
        0.05 * float(verified_email) +
        0.05 * float(verified_phone) +
        0.05 * float(linkedin_connected)
    )
    
    # 8. Open to work flag (modulating boost)
    open_to_work = signals.get("open_to_work_flag", False)
    open_boost = 1.1 if open_to_work else 0.9
    
    # Weighted base score calculation
    base_score = (
        0.25 * recency_score +
        0.25 * response_rate +
        0.10 * response_time_score +
        0.15 * interview_score +
        0.15 * notice_score +
        0.10 * location_score
    )
    
    # Apply verification bonuses and open-to-work multiplier
    final_score = round((base_score + verification_bonus) * open_boost, 4)
    final_score = min(final_score, 1.0)
    final_score = max(final_score, 0.0)
    
    # Natural language explanation
    activity_desc = "recently active" if recency_score >= 0.9 else "moderately active" if recency_score >= 0.6 else "mostly inactive"
    location_desc = "local/India-based" if location_score == 1.0 else "willing to relocate" if location_score == 0.6 else "non-local"
    
    explanation = (
        f"Behavioral signals are strong. Candidate is {activity_desc} on platform (last seen {recency_days} days ago). "
        f"Recruiter response rate is {response_rate*100:.1f}% (average response: {rt:.1f} hrs). "
        f"Notice period is {np_days} days. Candidate is {location_desc}."
    )
    if open_to_work:
        explanation += " Actively looking for opportunities (Open to Work)."
        
    return {
        "score": final_score,
        "explanation": explanation,
        "details": {
            "recency_days": recency_days,
            "recency_score": recency_score,
            "response_rate": response_rate,
            "response_time_score": response_time_score,
            "interview_score": interview_score,
            "notice_score": notice_score,
            "location_score": location_score,
            "verification_bonus": verification_bonus,
            "open_to_work": open_to_work,
            "open_boost": open_boost
        }
    }
