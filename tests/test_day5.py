import os
import sys

# Add the parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.loader import load_sample_candidates
from lenses.lens1_role_semantic import score_role_semantic_fit, initialize_semantic_scores
from lenses.lens2_skill_depth import score_skill_depth
from lenses.lens3_seniority import score_seniority_match
from lenses.lens4_behavioral import score_behavioral_hirability
from lenses.lens5_red_flags import score_red_flags
from lenses.lens6_evidence import score_evidence_strength
from scoring.fusion import fuse_scores

def test_full_pipeline():
    # 1. Initialize offline semantic scores
    initialize_semantic_scores()
    
    sample_file = "data/sample_candidates.json"
    if not os.path.exists(sample_file):
        print(f"Error: Sample file not found at {sample_file}")
        return
        
    candidates = load_sample_candidates(sample_file)
    print(f"Loaded {len(candidates)} sample candidates. Running full pipeline...")
    
    results = []
    
    # 2. Process each candidate
    for cand in candidates:
        cid = cand.get("candidate_id")
        title = cand.get("profile", {}).get("current_title")
        
        # Run all 6 lenses
        l1 = score_role_semantic_fit(cand)
        l2 = score_skill_depth(cand)
        l3 = score_seniority_match(cand)
        l4 = score_behavioral_hirability(cand)
        l5 = score_red_flags(cand)
        l6 = score_evidence_strength(cand)
        
        # Collect individual scores
        lens_scores = {
            "role_semantic_fit": l1["score"],
            "skill_depth_breadth": l2["score"],
            "seniority_level_match": l3["score"],
            "behavioral_hirability": l4["score"],
            "red_flag_detector": l5["score"],
            "evidence_strength": l6["score"]
        }
        
        # Fuse scores using Lens 5 gate multiplier
        final_score = fuse_scores(lens_scores, l5["gate_multiplier"])
        
        results.append({
            "id": cid,
            "title": title,
            "lens_scores": lens_scores,
            "gate": l5["gate_multiplier"],
            "score": final_score,
            "red_flags": l5["flags"]
        })
        
    # 3. Sort by score descending, tie-break by candidate_id ascending
    results.sort(key=lambda x: (-x["score"], x["id"]))
    
    # 4. Print results
    print("\n" + "="*110)
    print(f"{'Rank':<5} | {'Candidate ID':<13} | {'Current Title':<30} | {'Final Score':<11} | {'Gate':<5} | {'L1/L2/L3/L4/L5/L6 Scores'}")
    print("="*110)
    
    for rank, res in enumerate(results[:20]):
        scores_str = (
            f"{res['lens_scores']['role_semantic_fit']:.2f}/"
            f"{res['lens_scores']['skill_depth_breadth']:.2f}/"
            f"{res['lens_scores']['seniority_level_match']:.2f}/"
            f"{res['lens_scores']['behavioral_hirability']:.2f}/"
            f"{res['lens_scores']['red_flag_detector']:.2f}/"
            f"{res['lens_scores']['evidence_strength']:.2f}"
        )
        print(f"{rank+1:<5} | {res['id']:<13} | {res['title'][:30]:<30} | {res['score']:<11.4f} | {res['gate']:<5.1f} | {scores_str}")
        if res["red_flags"]:
            print(f"      -> VETOED/FLAGGED: {'; '.join(res['red_flags'])}")
            
    print("="*110)
    
    # Count total vetoed candidates
    vetoed_count = sum(1 for r in results if r["gate"] == 0.0)
    print(f"Total processed: {len(results)} | Total vetoed (honeypots): {vetoed_count}")
    print("="*110)

if __name__ == "__main__":
    test_full_pipeline()
