import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Add the parent directory to path so we can import pipeline modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pipeline.loader import stream_candidates
from pipeline.text_builder import build_candidate_text

def precompute_candidate_embeddings(limit=None):
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidates_file = os.path.join(workspace_dir, "data", "candidates.jsonl")
    embeddings_out = os.path.join(workspace_dir, "artifacts", "candidate_embeddings.npy")
    ids_out = os.path.join(workspace_dir, "artifacts", "candidate_ids.txt")
    
    # Check if data directory exists
    if not os.path.exists(candidates_file):
        print(f"Error: Candidate file not found at {candidates_file}")
        return
        
    print(f"Reading candidates from {candidates_file}...")
    candidate_ids = []
    documents = []
    
    # First, read and build documents
    for cand in tqdm(stream_candidates(candidates_file, limit), desc="Building profile texts"):
        cid = cand.get("candidate_id")
        doc_text = build_candidate_text(cand)
        candidate_ids.append(cid)
        documents.append(doc_text)
        
    print(f"Loaded {len(documents)} candidate profiles.")
    
    print("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Set PyTorch thread count to prevent thrashing and maximize throughput
    import torch
    print("Setting PyTorch threads to 8 (optimized for 12-core CPU)...")
    torch.set_num_threads(8)
    
    # Prevent Windows from going to sleep during encoding
    import platform
    if platform.system() == "Windows":
        try:
            import ctypes
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
            print("Windows sleep prevention activated.")
        except Exception as e:
            print(f"Could not activate sleep prevention: {e}")
            
    print("Encoding candidate documents (this may take a few minutes on CPU)...")
    embeddings = model.encode(
        documents,
        batch_size=128,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    print(f"Computed candidate embeddings shape: {embeddings.shape}")
    
    # Create artifacts directory if it doesn't exist
    os.makedirs(os.path.dirname(embeddings_out), exist_ok=True)
    
    # Save embeddings
    print(f"Saving embeddings to {embeddings_out}...")
    np.save(embeddings_out, embeddings)
    
    # Save candidate IDs
    print(f"Saving candidate IDs to {ids_out}...")
    with open(ids_out, 'w', encoding='utf-8') as f:
        for cid in candidate_ids:
            f.write(f"{cid}\n")
            
    print("Pre-computation completed successfully!")

if __name__ == "__main__":
    # If run as script, process all candidates
    precompute_candidate_embeddings()
