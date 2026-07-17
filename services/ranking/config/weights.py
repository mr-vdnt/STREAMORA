# Scoring Weights Configuration
# Adjust these values to tune the recommendation engine's behavior

WEIGHTS = {
    # Base retrieval strength
    "retrieval_fusion_score": 0.30,
    
    # Metadata overlaps
    "genre_overlap": 0.20,
    "theme_overlap": 0.15,
    "director_match": 0.10,
    "actor_match": 0.05,
    
    # Additional ranking signals
    "popularity_boost": 0.10,
    "vote_average_boost": 0.10
}
