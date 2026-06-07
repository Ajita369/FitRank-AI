import datetime
from typing import Dict, Any, List, Tuple

def analyze_honeypot_signals(candidate: Dict[str, Any]) -> Tuple[List[str], float]:
    """
    Analyzes a candidate for honeypot indicators (impossible/contradictory profiles).
    
    Returns:
        A tuple of (list of reasons, severity score between 0.0 and 1.0).
        A severity score >= 0.8 implies high likelihood of being a honeypot.
    """
    reasons = []
    severity = 0.0
    
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    
    # Reference date for the platform (discovered to be June 1, 2026)
    ref_date = datetime.datetime(2026, 6, 1)
    
    # 1. Date-Duration Mismatch in Career History (Definitive Honeypot)
    for r_idx, role in enumerate(career_history):
        start_str = role.get("start_date")
        end_str = role.get("end_date")
        is_current = role.get("is_current", False)
        dur = role.get("duration_months", 0)
        
        if start_str:
            try:
                start = datetime.datetime.strptime(start_str, "%Y-%m-%d")
                if is_current or not end_str:
                    end = ref_date
                else:
                    end = datetime.datetime.strptime(end_str, "%Y-%m-%d")
                    
                expected_months = (end.year - start.year) * 12 + (end.month - start.month)
                # If there's a severe mismatch (greater than 3 months)
                if abs(expected_months - dur) > 3:
                    reasons.append(
                        f"Career role {r_idx} ({role.get('company')}): dates imply {expected_months} months, "
                        f"but duration_months claims {dur}"
                    )
                    severity = max(severity, 1.0) # Definitive red flag
            except ValueError:
                pass

    # 2. Implausible Skills Heuristics (Definitive Honeypot if 3+)
    expert_zero_duration = [
        s.get("name", "") for s in skills 
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0
    ]
    if len(expert_zero_duration) >= 3:
        reasons.append(
            f"Claimed 'expert' in {len(expert_zero_duration)} skills with 0 months of use: "
            f"{', '.join(expert_zero_duration[:5])}"
        )
        severity = max(severity, 1.0) # Definitive red flag
        
    # 3. Experience vs Career History Duration Anomaly
    yoe = profile.get("years_of_experience", 0.0)
    total_career_months = sum(role.get("duration_months", 0) for role in career_history)
    total_career_years = total_career_months / 12.0
    
    if yoe > total_career_years + 5.0 and yoe > 3.0:
        reasons.append(
            f"Claimed {yoe} YOE but career history only documents {total_career_years:.1f} years"
        )
        severity = max(severity, 0.8)
        
    # 4. Total experience is 0 but has senior/lead titles
    if yoe == 0 and len(career_history) > 0:
        titles = [r.get("title", "").lower() for r in career_history]
        has_senior_title = any("senior" in t or "lead" in t or "head" in t or "manager" in t for t in titles)
        if has_senior_title:
            reasons.append("Claimed 0 YOE but has senior/lead titles in career history")
            severity = max(severity, 0.8)

    # 5. Overlapping full-time roles (3+ concurrent full-time roles)
    current_roles = [r for r in career_history if r.get("is_current", False)]
    if len(current_roles) >= 3:
        reasons.append(f"Claimed to hold {len(current_roles)} concurrent current roles")
        severity = max(severity, 0.8)

    # 6. Many expert skills with no endorsements and no assessments (suspicious)
    expert_unverified = [
        s.get("name", "") for s in skills
        if s.get("proficiency") == "expert" and s.get("endorsements", 0) == 0
    ]
    assessment_scores = signals.get("skill_assessment_scores", {})
    expert_untested_unverified = [
        s for s in expert_unverified if s not in assessment_scores
    ]
    if len(expert_untested_unverified) >= 8:
        reasons.append(f"Claimed 'expert' in {len(expert_untested_unverified)} skills with 0 endorsements and no platform assessments")
        severity = max(severity, 0.6)

    # Clamp severity to [0.0, 1.0]
    severity = min(severity, 1.0)
    
    return reasons, severity

def is_honeypot(candidate: Dict[str, Any]) -> bool:
    """
    Returns True if the candidate's profile is highly likely to be a honeypot.
    """
    _, severity = analyze_honeypot_signals(candidate)
    return severity >= 0.8
