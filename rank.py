import os
import sys
import argparse
import csv
from tqdm import tqdm

# Add current directory to path so we can import packages
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from pipeline.loader import stream_candidates
from lenses.lens1_role_semantic import score_role_semantic_fit, initialize_semantic_scores
from lenses.lens2_skill_depth import score_skill_depth
from lenses.lens3_seniority import score_seniority_match
from lenses.lens4_behavioral import score_behavioral_hirability
from lenses.lens5_red_flags import score_red_flags
from lenses.lens6_evidence import score_evidence_strength
from scoring.fusion import fuse_scores
from scoring.reasoning import generate_candidate_reasoning
from data.validate_submission import validate_submission

def main():
    parser = argparse.ArgumentParser(description="FitRank AI Candidate Ranking Pipeline")
    parser.add_argument("--candidates", required=True, help="Path to the input candidates JSONL file")
    parser.add_argument("--out", required=True, help="Path to write the output CSV file")
    args = parser.parse_args()
    
    # 1. Verify that pre-computed embeddings exist
    workspace_dir = os.path.abspath(os.path.dirname(__file__))
    jd_emb_path = os.path.join(workspace_dir, "artifacts", "jd_embedding.npy")
    cand_emb_path = os.path.join(workspace_dir, "artifacts", "candidate_embeddings.npy")
    ids_path = os.path.join(workspace_dir, "artifacts", "candidate_ids.txt")
    
    if not (os.path.exists(jd_emb_path) and os.path.exists(cand_emb_path) and os.path.exists(ids_path)):
        print("\n" + "="*80)
        print("ERROR: Pre-computed embeddings or candidate ID indices not found!")
        print("FitRank AI requires offline pre-computation to run within the 5-minute CPU budget.")
        print("Please run the pre-computation script first:")
        print("  python precompute/embed_candidates.py")
        print("  python precompute/embed_jd.py")
        print("="*80 + "\n")
        sys.exit(1)
        
    # 2. Initialize Lens 1 semantic scores
    initialize_semantic_scores()
    
    # 3. Process candidates pool
    print(f"Ranking candidates from {args.candidates}...")
    scored_candidates = []
    
    # Count total candidates for tqdm
    total_candidates = 100000  # Default expected count
    
    for cand in tqdm(stream_candidates(args.candidates), total=total_candidates, desc="Evaluating candidates"):
        # Run all 6 lenses
        l1 = score_role_semantic_fit(cand)
        l2 = score_skill_depth(cand)
        l3 = score_seniority_match(cand)
        l4 = score_behavioral_hirability(cand)
        l5 = score_red_flags(cand)
        l6 = score_evidence_strength(cand)
        
        lens_scores = {
            "role_semantic_fit": l1["score"],
            "skill_depth_breadth": l2["score"],
            "seniority_level_match": l3["score"],
            "behavioral_hirability": l4["score"],
            "red_flag_detector": l5["score"],
            "evidence_strength": l6["score"]
        }
        
        # Fuse scores using gate multiplier
        final_score = fuse_scores(lens_scores, l5["gate_multiplier"])
        
        # Only compile full reasoning for candidates who are NOT vetoed (score > 0.0) 
        # to save execution time during ranking.
        reasoning = ""
        if final_score > 0.0:
            reasoning = generate_candidate_reasoning(cand, l1, l2, l3, l4, l5, l6)
            
        scored_candidates.append({
            "candidate_id": cand.get("candidate_id"),
            "score": final_score,
            "reasoning": reasoning
        })
        
    # 4. Sort candidates
    # Sort criteria: score descending, then candidate_id ascending for ties (lexicographical)
    print("Sorting scored candidates...")
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # 5. Extract top 100
    top_candidates = scored_candidates[:100]
    
    # Ensure scores are strictly monotonic (non-increasing)
    # This prevents any potential floating point comparison issues in validator
    for i in range(1, len(top_candidates)):
        if top_candidates[i]["score"] > top_candidates[i-1]["score"]:
            top_candidates[i]["score"] = top_candidates[i-1]["score"]
            
    # Regenerate reasoning for any rank fillers that might have been vetoed 
    # (though no vetoed candidate should make it to top 100 unless pool is empty)
    for i, res in enumerate(top_candidates):
        if not res["reasoning"]:
            res["reasoning"] = f"Backup filler candidate (Rank {i+1}) included based on experience profile."
            
    # 6. Write to output CSV
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    print(f"Writing ranked shortlist to {args.out}...")
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for idx, item in enumerate(top_candidates):
            rank = idx + 1
            # Clean up reasoning to be CSV-safe
            safe_reasoning = item["reasoning"].replace('\n', ' ').replace('\r', '').replace('"', "'")
            writer.writerow([item["candidate_id"], rank, f"{item['score']:.4f}", safe_reasoning])
            
    # 7. Validate output CSV
    print("Running format validator...")
    errors = validate_submission(args.out)
    if errors:
        print("\n" + "="*80)
        print("SUBMISSION FORMAT VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        print("="*80 + "\n")
        sys.exit(1)
    else:
        print("\n" + "="*80)
        print("SUCCESS: Shortlist generated and validated successfully!")
        print(f"Output saved to: {args.out}")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()
