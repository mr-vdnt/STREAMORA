from sqlalchemy.orm import Session
from services.repository.catalog_db import RecommendationFeatures, ContentGenre, Genre

class RecommendationPreparationService:
    """
    Pre-populates RecommendationFeatures table with backend-agnostic vector metadata.
    """
    def prepare_features(self, session: Session, content_id: int) -> RecommendationFeatures:
        rec_feat = session.query(RecommendationFeatures).filter(RecommendationFeatures.content_id == content_id).first()
        if not rec_feat:
            rec_feat = RecommendationFeatures(content_id=content_id)
            session.add(rec_feat)

        # Extract genres as genre vector string representation
        genres = session.query(Genre).join(ContentGenre).filter(ContentGenre.content_id == content_id).all()
        genre_str = "|".join([g.name for g in genres])

        rec_feat.genre_vector = genre_str
        rec_feat.embedding_provider = "sentence-transformers"
        rec_feat.embedding_model = "all-MiniLM-L6-v2"
        rec_feat.embedding_dimension = 384
        rec_feat.embedding_version = 1
        
        session.commit()
        return rec_feat
