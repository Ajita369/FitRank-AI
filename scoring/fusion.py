import os
import sys
from typing import Dict, Any

# Define the standard weights for each lens
LENS_WEIGHTS = {
    "role_semantic_fit": 0.30,
    "skill_depth_breadth": 0.25,
    "seniority_level_match": 0.15,
    "behavioral_hirability": 0.15,
    "red_flag_detector": 0.10,
    "evidence_strength": 0.05
}

def fuse_scores(lens_scores: Dict[str, float], gate_multiplier: float) -> float:
    """
    Combines the 6 individual lens scores into a single final composite score
    using a weighted sum and applies the red flag gate multiplier.
    
    Formula:
      Weighted Sum = sum(lens_score * weight)
      Final Score = Weighted Sum * gate_multiplier
      
    Where gate_multiplier is 0.0 for honeypots/vetoed candidates and 1.0 otherwise.
    
    Args:
        lens_scores: Dictionary of lens_name -> score (0.0 to 1.0)
        gate_multiplier: Multiplier from Lens 5 (0.0 or 1.0)
        
    Returns:
        float: Rounded score (4 decimal places) clamped between 0.0 and 1.0.
    """
    weighted_sum = 0.0
    for lens_name, weight in LENS_WEIGHTS.items():
        score = lens_scores.get(lens_name, 0.0)
        weighted_sum += score * weight
        
    final_score = weighted_sum * gate_multiplier
    
    # Clamp and round
    final_score = min(max(final_score, 0.0), 1.0)
    return round(final_score, 4)
