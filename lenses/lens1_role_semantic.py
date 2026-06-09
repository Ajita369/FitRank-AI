import os
import sys
import numpy as np
from typing import Dict, Any, Optional

# Add the parent directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Global cache for pre-computed similarity scores
_CANDIDATE_SIMILARITIES = {}
_INITIALIZED = False

def initialize_semantic_scores():
    """
    Loads pre-computed embeddings and pre-calculates the base cosine similarity 
    for all candidate IDs. Stored in a global dictionary for O(1) runtime lookup.
    """
    global _CANDIDATE_SIMILARITIES, _INITIALIZED
    if _INITIALIZED:
        return
        
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    jd_emb_path = os.path.join(workspace_dir, "artifacts", "jd_embedding.npy")
    cand_emb_path = os.path.join(workspace_dir, "artifacts", "candidate_embeddings.npy")
    ids_path = os.path.join(workspace_dir, "artifacts", "candidate_ids.txt")
    
    # Check if files exist
    if not (os.path.exists(jd_emb_path) and os.path.exists(cand_emb_path) and os.path.exists(ids_path)):
        # If pre-computation hasn't run yet, we will fallback to lazy initialization or on-the-fly scoring
        print("Warning: Pre-computed embeddings not found. Semantic scores will return a default or fall back.")
        return
        
    print("Initializing semantic scores from pre-computed embeddings...")
    try:
        jd_emb = np.load(jd_emb_path)
        cand_embs = np.load(cand_emb_path)
        
        # Load candidate IDs
        with open(ids_path, 'r', encoding='utf-8') as f:
            cand_ids = [line.strip() for line in f if line.strip()]
            
        # Ensure sizes match
        if len(cand_ids) != cand_embs.shape[0]:
            raise ValueError(f"Mismatch between candidate IDs count ({len(cand_ids)}) and embeddings shape ({cand_embs.shape[0]})")
            
        # Compute cosine similarity
        # Cosine similarity = dot(A, B) / (norm(A) * norm(B))
        # First, normalize the vectors
        jd_norm = jd_emb / np.linalg.norm(jd_emb)
        cand_norms = cand_embs / np.linalg.norm(cand_embs, axis=1, keepdims=True)
        
        # Matrix multiply (dot product)
        similarities = np.dot(cand_norms, jd_norm)
        
        # Store in dict
        _CANDIDATE_SIMILARITIES = {cid: float(sim) for cid, sim in zip(cand_ids, similarities)}
        _INITIALIZED = True
        print(f"Pre-calculated semantic similarity for {len(_CANDIDATE_SIMILARITIES)} candidates.")
    except Exception as e:
        print(f"Error initializing semantic scores: {e}")

def score_role_semantic_fit(candidate: Dict[str, Any], model_fallback: Optional[Any] = None) -> Dict[str, Any]:
    """
    Evaluates Lens 1: Role Semantic Fit.
    
    Looks up the pre-calculated cosine similarity between the candidate and JD embeddings,
    then adds a 'production bonus' based on presence of scalability/deployment terms in career descriptions.
    
    Production keywords: "production", "deployed", "shipped", "real users", "scale", "A/B test", "system design"
    Production boost: +0.02 per unique keyword hit (capped at +0.10)
    
    Returns:
        dict containing "score", "explanation", and "details" dict.
    """
    global _INITIALIZED
    if not _INITIALIZED:
        initialize_semantic_scores()
        
    cid = candidate.get("candidate_id")
    
    # 1. Retrieve base cosine similarity
    base_sim = _CANDIDATE_SIMILARITIES.get(cid, 0.0)
    
    # If not in cache and fallback model is provided (e.g. for dynamic testing), compute on the fly
    if base_sim == 0.0 and model_fallback is not None:
        try:
            from pipeline.text_builder import build_candidate_text
            workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            jd_path = os.path.join(workspace_dir, "data", "job_description.docx")
            if os.path.exists(jd_path):
                import docx
                doc = docx.Document(jd_path)
                jd_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                
                jd_emb = model_fallback.encode(jd_text)
                cand_text = build_candidate_text(candidate)
                cand_emb = model_fallback.encode(cand_text)
                
                jd_norm = jd_emb / np.linalg.norm(jd_emb)
                cand_norm = cand_emb / np.linalg.norm(cand_emb)
                base_sim = float(np.dot(cand_norm, jd_norm))
        except Exception:
            pass
            
    # 2. Compute Production Bonus
    production_keywords = ["production", "deployed", "shipped", "real users", "scale", "a/b test", "system design"]
    career_history = candidate.get("career_history", [])
    career_text = " ".join(role.get("description", "").lower() for role in career_history)
    
    hits = [kw for kw in production_keywords if kw in career_text]
    # +0.02 per hit, capped at 0.10
    production_bonus = min(len(hits) * 0.02, 0.10)
    
    # Final Score
    final_score = round(base_sim + production_bonus, 4)
    final_score = min(final_score, 1.0)
    
    # Build explanation
    explanation = (
        f"Semantic alignment with JD is {base_sim*100:.1f}%. "
    )
    if production_bonus > 0:
        explanation += f"Includes production bonus (+{production_bonus:.2f}) for shipping experience keywords ({', '.join(hits[:3])})."
    else:
        explanation += "No production deployment keywords found in career history descriptions."
        
    return {
        "score": final_score,
        "explanation": explanation,
        "details": {
            "base_similarity": base_sim,
            "production_bonus": production_bonus,
            "keyword_hits": hits
        }
    }
