from typing import Dict, Any, List
from .models import FeatureVector

class CandidateNormalizer:
    """Normalizes candidate metadata and queries before feature extraction."""
    @staticmethod
    def normalize_list(items: List[str]) -> set:
        if not items: return set()
        return {str(item).strip().lower() for item in items if item}

class FeatureExtractor:
    """Extracts atomic features for a candidate."""
    
    def __init__(self, movies_db: dict, user_adapter=None, content_adapter=None):
        self.movies_db = movies_db
        self.user_adapter = user_adapter
        self.content_adapter = content_adapter
        
    def extract(self, candidate_dict: dict, query_contract: dict) -> FeatureVector:
        cid = candidate_dict["content_id"]
        movie = self.movies_db.get(cid, {})
        
        fv = FeatureVector()
        
        # 1. Retrieval Features
        retrieval = candidate_dict.get("retrieval", {})
        fv.retrieval_fusion_score = retrieval.get("fusion_score", 0.0)
        
        # 2. Extract Query Entities
        entities = query_contract.get("entities", {})
        target_genres = CandidateNormalizer.normalize_list(entities.get("genres", []))
        target_themes = CandidateNormalizer.normalize_list(entities.get("themes", []))
        target_directors = CandidateNormalizer.normalize_list(entities.get("directors", []))
        target_actors = CandidateNormalizer.normalize_list(entities.get("actors", []))
        
        # 3. Extract Movie Metadata
        movie_genres = CandidateNormalizer.normalize_list(str(movie.get("genres", "")).split("|"))
        movie_themes = CandidateNormalizer.normalize_list(str(movie.get("themes", "")).split("|"))
        movie_directors = CandidateNormalizer.normalize_list(str(movie.get("director", "")).split(","))
        movie_actors = CandidateNormalizer.normalize_list(str(movie.get("cast", "")).split(","))
        
        # 4. Overlap Calculations
        if target_genres:
            overlap = len(target_genres.intersection(movie_genres))
            fv.genre_overlap_pct = overlap / len(target_genres)
            
        if target_themes:
            overlap = len(target_themes.intersection(movie_themes))
            fv.theme_overlap_pct = overlap / len(target_themes)
            
        if target_directors:
            fv.director_match = len(target_directors.intersection(movie_directors)) > 0
            
        if target_actors:
            fv.actor_match_count = len(target_actors.intersection(movie_actors))
            
        # 5. Metadata Quality / Popularity
        try: fv.popularity = float(movie.get("popularity", 0.0))
        except: pass
        
        try: fv.vote_average = float(movie.get("rating", 0.0))
        except: pass
        
        try: fv.vote_count = int(movie.get("vote_count", 0))
        except: pass
        
        # 6. Franchise & Collection logic (Simulated for Phase 5)
        franchise = movie.get("franchise")
        ref_id = None
        if query_contract.get("reference_title"):
            ref_title = query_contract["reference_title"].lower()
            for iid, m in self.movies_db.items():
                if str(m.get("title", "")).lower() == ref_title:
                    ref_id = iid
                    ref_franchise = m.get("franchise")
                    if franchise and ref_franchise and ref_franchise == franchise:
                        fv.franchise_match = True
                    break
                    
        # Phase 7: Personalization Features
        if self.user_adapter and "user_id" in query_contract:
            user_id = query_contract["user_id"]
            # Extract basic affinity (mock implementation based on what's available in adapter)
            # We would typically call get_ranking_signals here.
            # To avoid tight coupling we use a placeholder or adapter call:
            signals = self.user_adapter.get_ranking_signals(user_id, {"director": movie_directors[0] if movie_directors else ""})
            if hasattr(signals, 'director_affinity'):
                fv.personalization_score = signals.director_affinity
                
        # Phase 8: Content Intelligence / Graph Features
        if self.content_adapter and ref_id is not None:
            graph_features = self.content_adapter.get_relationship_features(ref_id, cid)
            fv.graph_similarity = graph_features.get("graph_similarity", 0.0)
            fv.shared_theme_score = graph_features.get("shared_theme_score", 0.0)
            fv.shared_actor_score = graph_features.get("shared_actor_score", 0.0)
            fv.shared_director_score = graph_features.get("shared_director_score", 0.0)
            
        return fv
