import os
import sys

# Add parent directory to path so we can import project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scoring.reasoning import generate_candidate_reasoning

def test_generate_reasoning_clean():
    # Mock candidate with clean profile
    cand = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "years_of_experience": 6.5,
            "current_title": "Senior AI Engineer",
            "location": "Pune, Maharashtra"
        },
        "skills": [
            {"name": "Sentence Transformers", "proficiency": "expert", "endorsements": 5, "duration_months": 24},
            {"name": "Pinecone", "proficiency": "advanced", "endorsements": 10, "duration_months": 18}
        ],
        "redrob_signals": {
            "notice_period_days": 30,
            "github_activity_score": 75,
            "last_active_date": "2026-05-20"
        }
    }
    
    l1 = {"score": 0.85, "details": {"keyword_hits": ["scale", "production"]}}
    l2 = {"score": 0.80}
    l3 = {"score": 0.90}
    l4 = {"score": 0.88, "details": {"recency_days": 12}}
    l5 = {"score": 1.00, "flags": [], "gate_multiplier": 1.0}
    l6 = {"score": 0.75}
    
    reason = generate_candidate_reasoning(cand, l1, l2, l3, l4, l5, l6)
    
    # Assertions
    assert "6.5 yrs experience as a Senior AI Engineer" in reason
    assert "expertise in Sentence Transformers, Pinecone" in reason
    assert "experience scaling systems and deploying to production" in reason
    assert "Located in Pune, Maharashtra" in reason
    assert "highly active recently" in reason
    assert "shows" in reason
    assert len(reason) <= 250
    print("test_generate_reasoning_clean passed!")

def test_generate_reasoning_with_concerns():
    # Mock candidate with non-technical title concern
    cand = {
        "candidate_id": "CAND_0000002",
        "profile": {
            "years_of_experience": 5.0,
            "current_title": "Marketing Associate",
            "location": "Hyderabad, Telangana"
        },
        "skills": [],
        "redrob_signals": {
            "notice_period_days": 60,
            "github_activity_score": 10,
            "last_active_date": "2026-04-15"
        }
    }
    
    l1 = {"score": 0.50, "details": {"keyword_hits": []}}
    l2 = {"score": 0.20}
    l3 = {"score": 0.40}
    l4 = {"score": 0.50, "details": {"recency_days": 47}}
    l5 = {
        "score": 0.60, 
        "flags": ["Non-technical current title 'Marketing Associate' with minimal machine learning evidence in career history description"], 
        "gate_multiplier": 1.0
    }
    l6 = {"score": 0.30}
    
    reason = generate_candidate_reasoning(cand, l1, l2, l3, l4, l5, l6)
    
    # Assertions
    assert "5.0 yrs experience as a Marketing Associate" in reason
    assert "gaps: Non-technical current title" in reason
    assert "Located in Hyderabad, Telangana" in reason
    assert len(reason) <= 250
    print("test_generate_reasoning_with_concerns passed!")

if __name__ == "__main__":
    test_generate_reasoning_clean()
    test_generate_reasoning_with_concerns()
    print("All Day 7 unit tests passed successfully!")
