import os
import sys
from typing import Dict, Any, List, Tuple

# Add the parent directory to the path so we can import config and pipeline modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.honeypot_detector import analyze_honeypot_signals, is_honeypot
from config.jd_requirements import JD_REQUIREMENTS

def score_red_flags(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates Lens 5: Red Flag Detector.
    
    Checks for:
    - Honeypots (impossible/contradictory profiles) -> VETO (gate_multiplier = 0)
    - Consulting-only career paths (TCS, Wipro, Infosys, etc.)
    - Title-role mismatches (non-technical current titles without ML history)
    - Keyword stuffing (unverified skills list)
    - Ghost candidate behavior (high inactivity + low recruiter response)
    
    Returns a dict with:
        "score": float (1.0 = clean, 0.0 = severe red flags)
        "gate_multiplier": float (1.0 = pass, 0.0 = veto/disqualify)
        "flags": List[str] (natural language explanations of detected concerns)
        "explanation": str (summary text)
    """
    flags = []
    severity = 0.0
    gate_multiplier = 1.0
    
    # 1. Honeypot check (hard gate/veto)
    honeypot_reasons, honeypot_severity = analyze_honeypot_signals(candidate)
    if honeypot_severity >= 0.8:
        flags.extend(honeypot_reasons)
        severity = max(severity, 1.0)
        gate_multiplier = 0.0  # VETO
        
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    
    # 2. Consulting-only career path (Anti-signal in JD)
    consulting_firms = JD_REQUIREMENTS["anti_signals"]["consulting_firms"]
    companies = [role.get("company", "") for role in career_history]
    
    if companies:
        is_consulting_only = all(
            any(cf.lower() in comp.lower() for cf in consulting_firms)
            for comp in companies if comp
        )
        if is_consulting_only:
            flags.append("Entire career history is at consulting/services firms (TCS, Wipro, Infosys, etc.)")
            severity = max(severity, 0.3)
            
    # 3. Title-role mismatch (Non-tech title but claiming expert AI skills)
    non_tech_titles = JD_REQUIREMENTS["anti_signals"]["non_technical_titles"]
    current_title = profile.get("current_title", "").lower()
    
    if any(nt in current_title for nt in non_tech_titles):
        # Examine history descriptions for actual ML experience
        history_desc = " ".join(role.get("description", "").lower() for role in career_history)
        ml_keywords = [
            "machine learning", "ml", "neural network", "deep learning", "embedding", 
            "vector database", " Pinecone", " Weaviate", " Qdrant", " Milvus", "nlp", 
            "transformer", "sentence-transformer", "retrieval", "search engine", "ranking"
        ]
        ml_evidence_hits = sum(1 for kw in ml_keywords if kw in history_desc)
        
        # If they have a non-tech current title and very weak ML work history
        if ml_evidence_hits < 2:
            flags.append(
                f"Non-technical current title '{profile.get('current_title')}' "
                "with minimal machine learning evidence in career history description"
            )
            severity = max(severity, 0.4)
            
    # 4. Keyword stuffing detection
    # Claiming many ML/AI skills without endorsements or platform assessments
    skill_names = [s.get("name", "").lower() for s in skills]
    ai_skills_claimed = [
        s for s in skill_names if any(kw in s for kw in [
            "ml", "ai", "machine learning", "deep learning", "nlp", "neural", 
            "embedding", "vector", "transformer", "bert", "gpt", "rag", "retrieval", "ranking"
        ])
    ]
    if len(ai_skills_claimed) >= 6:
        # Check credibility
        avg_endorsements = sum(s.get("endorsements", 0) for s in skills if s.get("name", "").lower() in ai_skills_claimed) / len(ai_skills_claimed)
        assessments_taken = len(signals.get("skill_assessment_scores", {}))
        
        if avg_endorsements < 3 and assessments_taken == 0:
            flags.append(
                f"Claimed {len(ai_skills_claimed)} AI/ML skills, but has near-zero endorsements "
                "and no platform assessments (potential keyword stuffer)"
            )
            severity = max(severity, 0.3)
            
    # 5. Ghost Candidate (high inactivity + low recruiter response)
    # Check last active date (if older than 180 days)
    last_active_str = signals.get("last_active_date", "")
    if last_active_str:
        try:
            last_active = datetime.datetime.strptime(last_active_str, "%Y-%m-%d")
            ref_date = datetime.datetime(2026, 6, 1) # Platform reference date
            days_inactive = (ref_date - last_active).days
            
            response_rate = signals.get("recruiter_response_rate", 0.0)
            if days_inactive > 180 and response_rate < 0.15:
                flags.append(
                    f"Inactive for {days_inactive} days with very low recruiter response rate ({response_rate * 100:.1f}%)"
                )
                severity = max(severity, 0.3)
        except (ValueError, NameError):
            # Fallback if datetime is not imported locally (though we can import it)
            import datetime
            last_active = datetime.datetime.strptime(last_active_str, "%Y-%m-%d")
            ref_date = datetime.datetime(2026, 6, 1)
            days_inactive = (ref_date - last_active).days
            response_rate = signals.get("recruiter_response_rate", 0.0)
            if days_inactive > 180 and response_rate < 0.15:
                flags.append(
                    f"Inactive for {days_inactive} days with very low recruiter response rate ({response_rate * 100:.1f}%)"
                )
                severity = max(severity, 0.3)
                
    # Final score is 1.0 - severity
    score = round(1.0 - severity, 4)
    
    # Generate explanation
    if not flags:
        explanation = "No significant red flags or career inconsistencies detected."
    elif gate_multiplier == 0.0:
        explanation = f"DISQUALIFIED: Impossible/contradictory profile details detected. Reasons: {'; '.join(flags)}."
    else:
        explanation = f"Concerns detected: {'; '.join(flags)}."
        
    return {
        "score": score,
        "gate_multiplier": gate_multiplier,
        "flags": flags,
        "explanation": explanation
    }
