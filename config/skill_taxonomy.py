# FitRank AI — Skill Taxonomy & Groups Configuration

# Weights sum to 1.0, representing the importance of each area according to the JD
SKILL_GROUPS = {
    "embeddings_retrieval": {
        "keywords": [
            "embeddings", "sentence-transformers", "bge", "e5", "retrieval", 
            "semantic search", "vector search", "faiss", "rag", "dense retrieval",
            "hybrid search", "information retrieval", "dense search"
        ],
        "weight": 0.35,
        "name": "Embeddings & Retrieval"
    },
    "vector_db_infra": {
        "keywords": [
            "pinecone", "weaviate", "qdrant", "milvus", "opensearch", 
            "elasticsearch", "vector database", "vector databases", "vector db", 
            "chromadb", "pgvector"
        ],
        "weight": 0.20,
        "name": "Vector DB & Hybrid Infrastructure"
    },
    "ml_engineering": {
        "keywords": [
            "python", "ml", "machine learning", "deep learning", "pytorch", 
            "tensorflow", "scikit-learn", "nlp", "natural language processing",
            "applied ml", "mlops", "model training", "inference optimization"
        ],
        "weight": 0.25,
        "name": "ML Engineering Core"
    },
    "evaluation_ranking": {
        "keywords": [
            "ndcg", "mrr", "map", "ranking", "ranking systems", "evaluation", 
            "evaluation frameworks", "a/b testing", "learning-to-rank", "xgboost"
        ],
        "weight": 0.20,
        "name": "Ranking & Evaluation"
    }
}

# Nice-to-have bonus skill keywords (used to apply secondary boosts)
NICE_TO_HAVE_KEYWORDS = [
    "lora", "qlora", "peft", "fine-tuning", "fine-tuning llms", 
    "hr-tech", "recruiting tech", "marketplace", "distributed systems", 
    "inference optimization", "open-source"
]

# Normalization mapping for variations in spelling/format
SKILL_NORMALIZATION_MAP = {
    "sentence transformers": "sentence-transformers",
    "sentencetransformers": "sentence-transformers",
    "vector database": "vector databases",
    "vector db": "vector databases",
    "elastic search": "elasticsearch",
    "open search": "opensearch",
    "a/b testing": "a/b testing",
    "ab testing": "a/b testing",
    "learning to rank": "learning-to-rank",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "fine-tuning llms": "fine-tuning",
    "finetuning": "fine-tuning"
}

def normalize_skill_name(skill_name: str) -> str:
    """
    Normalizes a skill name by lowercasing, stripping extra spacing, 
    and mapping synonyms/variants to a canonical spelling.
    """
    if not skill_name:
        return ""
    name_clean = " ".join(skill_name.lower().strip().split())
    return SKILL_NORMALIZATION_MAP.get(name_clean, name_clean)
