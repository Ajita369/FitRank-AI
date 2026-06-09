import os
import sys

# Add the parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.loader import load_sample_candidates
from lenses.lens1_role_semantic import score_role_semantic_fit, initialize_semantic_scores

def test_lens1():
    # Initialize the semantic scores
    initialize_semantic_scores()
    
    sample_file = "data/sample_candidates.json"
    if not os.path.exists(sample_file):
        print(f"Error: Sample file not found at {sample_file}")
        return
        
    candidates = load_sample_candidates(sample_file)
    print(f"Loaded {len(candidates)} sample candidates. Running Lens 1 tests on first 15...")
    
    print("\n" + "="*80)
    print(" LENS 1 (ROLE SEMANTIC FIT) TEST")
    print("="*80)
    
    for i, cand in enumerate(candidates[:15]):
        cid = cand.get("candidate_id")
        title = cand.get("profile", {}).get("current_title")
        
        # Run Lens 1
        res = score_role_semantic_fit(cand)
        
        print(f"\n[{i+1}] Candidate: {cid} | Title: {title}")
        print(f"    Semantic Fit Score: {res['score']}")
        print(f"    Explanation: {res['explanation']}")
        print(f"    Details: base_similarity={res['details']['base_similarity']:.4f}, production_bonus={res['details']['production_bonus']:.2f}")
        
    print("\n" + "="*80)
    print("Test completed.")
    print("="*80)

if __name__ == "__main__":
    test_lens1()
