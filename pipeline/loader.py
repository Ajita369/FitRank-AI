import json
import os
from typing import Generator, Any, Dict, List, Optional

def stream_candidates(file_path: str, limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Streams candidates from a JSONL file line-by-line to minimize memory footprint.
    
    Args:
        file_path: Path to the candidates JSONL file.
        limit: Optional maximum number of candidates to yield.
        
    Yields:
        Candidate dictionaries.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Candidate file not found: {file_path}")
        
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            yield json.loads(line)
            count += 1
            if limit is not None and count >= limit:
                break

def load_candidates(file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Loads candidates into a list in memory.
    
    Args:
        file_path: Path to the candidates JSONL file.
        limit: Optional maximum number of candidates to load.
        
    Returns:
        List of candidate dictionaries.
    """
    return list(stream_candidates(file_path, limit))

def load_sample_candidates(file_path: str) -> List[Dict[str, Any]]:
    """
    Loads candidates from a standard JSON array file (like sample_candidates.json).
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        List of candidate dictionaries.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sample candidates file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
