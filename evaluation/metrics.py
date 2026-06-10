import numpy as np
from typing import List

def precision_at_k(relevances: List[int], k: int) -> float:
    """
    Computes Precision@K.
    Precision@K is the fraction of the top-K retrieved candidates that are relevant.
    We define "relevant" as relevance score >= 1 (e.g. not tier_0).
    """
    if k <= 0:
        return 0.0
    top_k = relevances[:k]
    relevant_count = sum(1 for r in top_k if r >= 1)
    return relevant_count / k

def dcg_at_k(relevances: List[float], k: int) -> float:
    """
    Computes Discounted Cumulative Gain at K (DCG@K).
    Formula: DCG@K = sum( (2^rel_i - 1) / log2(i + 2) ) for i from 0 to K-1.
    """
    relevances = np.asfarray(relevances)[:k]
    if relevances.size == 0:
        return 0.0
    return np.sum((2 ** relevances - 1) / np.log2(np.arange(2, relevances.size + 2)))

def ndcg_at_k(relevances: List[float], ideal_relevances: List[float], k: int) -> float:
    """
    Computes Normalized Discounted Cumulative Gain at K (NDCG@K).
    NDCG@K = DCG@K / IDCG@K.
    """
    dcg = dcg_at_k(relevances, k)
    # Sort ideal relevances in descending order to get maximum possible DCG
    sorted_ideal = sorted(ideal_relevances, reverse=True)
    idcg = dcg_at_k(sorted_ideal, k)
    
    if idcg == 0.0:
        return 0.0
    return dcg / idcg

def average_precision(relevances: List[int]) -> float:
    """
    Computes Average Precision (AP).
    AP = sum( (Precision@i * rel_i) ) / (total number of relevant items).
    Where rel_i is binary relevance (1 if rel_score >= 1, else 0).
    """
    relevances = [1 if r >= 1 else 0 for r in relevances]
    num_relevant = sum(relevances)
    if num_relevant == 0:
        return 0.0
        
    ap = 0.0
    run_relevant = 0
    for i, rel in enumerate(relevances):
        if rel == 1:
            run_relevant += 1
            ap += run_relevant / (i + 1)
            
    return ap / num_relevant

def compute_composite_score(ndcg10: float, ndcg50: float, map_score: float, p10: float) -> float:
    """
    Calculates the final composite score using the challenge formula:
      Composite = 0.50 * NDCG@10 + 0.30 * NDCG@50 + 0.15 * MAP + 0.05 * P@10
    """
    score = 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * map_score + 0.05 * p10
    return round(score, 5)
