# FitRank AI — Candidate Ranking Pipeline

> **"Rank candidates the way a great recruiter thinks — not the way a search engine does."**

FitRank AI is a production-grade, local, CPU-only candidate ranking system designed to evaluate and rank a pool of 100,000 candidates against a **Senior AI Engineer** job description. It addresses the flaws of traditional keyword search systems (e.g., keyword stuffing, hidden gems, and impossible profiles) using a multi-layered evaluation architecture.

---

## 🌟 Signature Innovation: Recruiter Cognitive Model (RCM)

Instead of relying on a single semantic similarity or keyword-overlap score, FitRank AI implements the **Recruiter Cognitive Model (RCM)**. It evaluates each candidate through six independent, parallel cognitive lenses that correspond to different dimensions of candidate fit:

```
┌─────────────────────────────────────────────────────────┐
│                   RECRUITER COGNITIVE MODEL              │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  LENS 1  │  │  LENS 2  │  │  LENS 3  │               │
│  │  Role    │  │  Skill   │  │ Seniority│               │
│  │ Semantic │  │ Depth &  │  │  & Level │               │
│  │  Fit     │  │ Breadth  │  │  Match   │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │              │              │                     │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐               │
│  │  LENS 4  │  │  LENS 5  │  │  LENS 6  │               │
│  │Behavioral│  │Red Flag  │  │ Evidence │               │
│  │Hirability│  │ Detector │  │ Strength │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │              │              │                     │
│       └──────────────┼──────────────┘                     │
│                      ▼                                    │
│           ┌──────────────────┐                            │
│           │  WEIGHTED FUSION │                            │
│           │  + Gate Logic    │                            │
│           │  + Tie-breaking  │                            │
│           └────────┬─────────┘                            │
│                    ▼                                    │
│           Final Ranked List + Explanations                │
└─────────────────────────────────────────────────────────┘
```

### The 6 Lenses

1.  **Lens 1: Role Semantic Fit (Weight: 30%)**: Measures semantic alignment between the candidate's career narrative (Concatenated roles and descriptions) and the JD using local `sentence-transformers/all-MiniLM-L6-v2` embeddings, boosted by production deployment keywords (+0.02 boost per hit, capped at +0.10).
2.  **Lens 2: Skill Depth & Breadth (Weight: 25%)**: Evaluates structured expertise inside four core skill groups (Embeddings/Retrieval, Vector DBs, ML Engineering, and Evaluation/Ranking). Prevents keyword stuffing by factoring in self-reported proficiency, duration of use, endorsements, and assessment scores.
3.  **Lens 3: Seniority & Level Match (Weight: 15%)**: Assesses fit for the Senior IC track based on years of experience (ideal range: 5–9 years), progression history, product-company ratio, and job-hop stability penalties.
4.  **Lens 4: Behavioral Hirability (Weight: 15%)**: Incorporates engagement signals from the platform (last active recency, recruiter response rate, notice period, and relocation willingness) to score actual hireability.
5.  **Lens 5: Red Flag Detector (Weight: 10% & Gate)**: Flags consulting-only careers, title-role mismatches, and keyword stuffing. Acts as a **Hard Veto Gate** (score multiplier set to 0.0) for impossible date-duration or expertise anomalies (Honeypots).
6.  **Lens 6: Evidence Strength (Weight: 5%)**: Modulates confidence based on profile completeness, verified credentials, recruiter search appearances, and github activity scores.

---

## 📊 Evaluation & Ablation Results

We ran comprehensive ablation studies on the full 100K candidate pool to verify individual lens contributions.

| Experiment / Ablation | Weights [L1, L2, L3, L4, L5, L6] | Gate Active | Top-100 Overlap | Jaccard Similarity | Honeypots in Top-100 | Avg Score | Description |
|---|---|---|---|---|---|---|---|
| **Base (All Lenses)** | [0.30, 0.25, 0.15, 0.15, 0.10, 0.05] | Yes | 100% | 1.0000 | **0** | 0.7513 | Standard production weights |
| **Ablate L1 (Semantic)** | [0.00, 0.36, 0.21, 0.21, 0.14, 0.07] | Yes | 91% | 0.8349 | **0** | 0.8187 | Without semantic embeddings |
| **Ablate L2 (Skill Depth)** | [0.40, 0.00, 0.20, 0.20, 0.13, 0.07] | Yes | 44% | 0.2821 | **0** | 0.8157 | Without skill depth scoring |
| **Ablate L3 (Seniority)** | [0.35, 0.29, 0.00, 0.18, 0.12, 0.06] | Yes | 90% | 0.8182 | **0** | 0.7189 | Without seniority/YoE |
| **Ablate L4 (Behavioral)** | [0.35, 0.29, 0.18, 0.00, 0.12, 0.06] | Yes | 86% | 0.7544 | **0** | 0.7256 | Without behavioral availability |
| **Disable L5 Gate** | [0.30, 0.25, 0.15, 0.15, 0.10, 0.05] | No | 100% | 1.0000 | **0** | 0.7513 | Gate multiplier disabled |

*   **0% Honeypot Rate**: Verified that no impossible honeypots appear in the top-100 results, satisfying the strict competition vetting rules.
*   **Skill Depth Guard**: Ablating Lens 2 results in a massive 56% shift in the shortlist, proving its effectiveness in separating genuine developers from keyword-stuffed resumes.

---

## 🛠️ Setup & Local Execution

> [!IMPORTANT]
> **Data & Precomputed Embeddings Notice (Gitignored Files)**:
> Due to file size limits, the raw datasets (`data/` folder containing `candidates.jsonl`) and the precomputed numpy embedding matrices (`artifacts/*.npy`) are gitignored. 
> 
> To run the system from a fresh clone:
> 1. Download the raw challenge dataset and place `candidates.jsonl` into the `data/` folder.
> 2. Place or symlink the parsed `.docx` requirement files into the `data/` folder.
> 3. Generate the offline embeddings search indexes by running:
>    ```bash
>    python precompute/embed_jd.py
>    python precompute/embed_candidates.py --candidates data/candidates.jsonl
>    ```

### 1. Requirements
*   Python 3.10+
*   Dependencies: `numpy`, `sentence-transformers`, `scikit-learn`, `python-docx`, `tqdm`, `pytest`

### 2. Standard Installation
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 4. Run Ranking Pipeline
Generates the final ranked shortlist with detailed, non-templated reasoning and performs validation:
```bash
python rank.py --candidates data/candidates.jsonl --out output/submission.csv
```

### 5. Run Reasoning Audits & Tests
```bash
# Verify YOE, title, location consistency, and length limits for the reasonings
python evaluation/reasoning_audit.py

# Run all test modules
python -m pytest
```

---

## 🐳 Sandbox Reproduction (Docker & Compose)

To run the pipeline inside a sandboxed container:

```bash
# Build the optimized container (automatically executes test suite)
docker build -t fitrank-ai .

# Run the pipeline inside Docker
docker compose run --rm fitrank
```
Final outputs will be written directly to `output/submission.csv` on your host machine via volume mounts.
