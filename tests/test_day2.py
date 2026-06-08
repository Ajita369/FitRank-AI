import os
import sys
import json

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.loader import load_sample_candidates
from lenses.lens5_red_flags import score_red_flags
from lenses.lens3_seniority import score_seniority_match

def test_lenses():
    sample_file = "data/sample_candidates.json"
    if not os.path.exists(sample_file):
        print(f"Error: Sample file not found at {sample_file}")
        return
        
    candidates = load_sample_candidates(sample_file)
    print(f"Loaded {len(candidates)} sample candidates. Running tests on the first 10...")
    
    print("\n" + "="*80)
    print(" LENS 5 (RED FLAGS) AND LENS 3 (SENIORITY) TEST")
    print("="*80)
    
    honeypot_count = 0
    
    for i, cand in enumerate(candidates[:15]):
        cid = cand.get("candidate_id")
        title = cand.get("profile", {}).get("current_title")
        yoe = cand.get("profile", {}).get("years_of_experience")
        
        # Run Lens 5
        red_flags_res = score_red_flags(cand)
        # Run Lens 3
        seniority_res = score_seniority_match(cand)
        
        is_hp = red_flags_res["gate_multiplier"] == 0.0
        if is_hp:
            honeypot_count += 1
            
        print(f"\n[{i+1}] Candidate: {cid} | Title: {title} | YOE: {yoe}")
        print(f"    - Lens 5 Score: {red_flags_res['score']} | Gate: {red_flags_res['gate_multiplier']}")
        print(f"      Explanation: {red_flags_res['explanation']}")
        print(f"    - Lens 3 Score: {seniority_res['score']}")
        print(f"      Explanation: {seniority_res['explanation']}")
        
    print("\n" + "="*80)
    print(f"Test summary: Processed 15 candidates. Detected {honeypot_count} honeypots.")
    print("="*80)

if __name__ == "__main__":
    test_lenses()
