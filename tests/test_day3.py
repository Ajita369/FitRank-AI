import os
import sys
import json

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.loader import load_sample_candidates
from lenses.lens2_skill_depth import score_skill_depth

def test_lens2():
    sample_file = "data/sample_candidates.json"
    if not os.path.exists(sample_file):
        print(f"Error: Sample file not found at {sample_file}")
        return
        
    candidates = load_sample_candidates(sample_file)
    print(f"Loaded {len(candidates)} sample candidates. Running tests on first 15...")
    
    print("\n" + "="*80)
    print(" LENS 2 (SKILL DEPTH & BREADTH) TEST")
    print("="*80)
    
    for i, cand in enumerate(candidates[:15]):
        cid = cand.get("candidate_id")
        title = cand.get("profile", {}).get("current_title")
        skills = cand.get("skills", [])
        
        # Run Lens 2
        res = score_skill_depth(cand)
        
        print(f"\n[{i+1}] Candidate: {cid} | Title: {title} | Total Skills: {len(skills)}")
        # Print actual skills for context
        skills_summary = ", ".join([f"{s.get('name')}({s.get('proficiency')}, {s.get('duration_months')}m)" for s in skills[:6]])
        print(f"    Skills: {skills_summary}...")
        print(f"    Score: {res['score']}")
        print(f"    Explanation: {res['explanation']}")
        print(f"    Details: nice_to_have_boost={res['details']['nice_to_have_boost']:.3f}, stuffing_penalty={res['details']['stuffing_penalty']:.3f}")
        
    print("\n" + "="*80)
    print("Test completed.")
    print("="*80)

if __name__ == "__main__":
    test_lens2()
