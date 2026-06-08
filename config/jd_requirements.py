# FitRank AI — Job Description Requirements Configuration

JD_REQUIREMENTS = {
    "role_title": "Senior AI Engineer",
    "seniority": "senior_ic",  # Senior Individual Contributor (not manager, not junior)
    "company_stage": "Series A startup",
    "location_preferred": ["Pune", "Noida", "Hyderabad", "Mumbai", "Delhi", "NCR", "Gurgaon", "Bengaluru", "Bangalore"],
    "work_mode": "hybrid",
    "notice_period_ideal": 30,  # Preferred notice period in days (buyout up to 30 days)
    
    "experience_range": {
        "min_years": 5.0,
        "max_years": 9.0,
        "flexible": True  # Flexible range if other signals are strong
    },
    
    # Must-have technical capabilities
    "must_have_skills": [
        "embeddings", "sentence-transformers", "BGE", "E5", "openai embeddings",
        "vector databases", "Pinecone", "Weaviate", "Qdrant", "Milvus",
        "OpenSearch", "Elasticsearch", "FAISS", "hybrid search",
        "Python", "ranking systems", "NDCG", "MRR", "MAP",
        "evaluation frameworks", "A/B testing", "retrieval", "dense retrieval",
        "applied ml", "machine learning", "deep learning", "nlp"
    ],
    
    # Nice-to-have capabilities (highly valued but not strict filters)
    "nice_to_have_skills": [
        "LoRA", "QLoRA", "PEFT", "fine-tuning", "fine-tuning llms",
        "learning-to-rank", "XGBoost", "neural ranking",
        "HR-tech", "recruiting tech", "marketplace",
        "distributed systems", "inference optimization",
        "open-source contributions"
    ],
    
    # Explicit disqualifiers and anti-signals
    "anti_signals": {
        # Consulting/services firms mentioned in JD
        "consulting_firms": [
            "TCS", "Tata Consultancy Services", "Infosys", "Wipro", 
            "Accenture", "Cognizant", "Capgemini", "HCL", "Tech Mahindra"
        ],
        # Non-technical current titles or unrelated fields
        "non_technical_titles": [
            "marketing manager", "hr manager", "accountant", "sales executive", 
            "content writer", "customer support", "graphic designer", 
            "operations manager", "civil engineer", "mechanical engineer", 
            "recruiter", "talent acquisition", "finance manager"
        ],
        # Anti-pattern: Title-chasers optimizing for fast promotion (switches company very frequently)
        "job_hopping_threshold_months": 18,
        "job_hopping_count_limit": 3
    }
}
