from typing import Dict, Any, List, Optional
from .storage import ProfileStore
from .models import PersonalizationSignal, UserProfile
from .preference_engine import PreferenceEngine
import datetime

class PersonalizationAdapter:
    """The only module exposed to Phases 3-6. Provides structured personalization signals."""
    
    def __init__(self, store: ProfileStore):
        self.store = store
        self.preference_engine = PreferenceEngine()
        
    def _get_and_decay_profile(self, user_id: str) -> Optional[UserProfile]:
        profile = self.store.get_profile(user_id)
        if not profile:
            return None
            
        # Apply time decay before returning signals
        last_updated = datetime.datetime.fromisoformat(profile.last_updated)
        now = datetime.datetime.utcnow()
        days_elapsed = (now - last_updated).total_seconds() / 86400.0
        
        if days_elapsed > 1.0:
            self.preference_engine.decay_preferences(profile, days_elapsed)
            # We don't save it back immediately here to avoid write amplification on every read, 
            # but we use the decayed values for the current request.
            
        return profile
        
    def get_query_bias(self, user_id: str) -> Dict[str, float]:
        """Phase 3: Returns the top 3 genre preferences to bias ambiguous queries."""
        profile = self._get_and_decay_profile(user_id)
        if not profile:
            return {}
            
        genres = profile.preferences.genres
        # Sort by weight * confidence
        sorted_genres = sorted(genres.items(), key=lambda item: item[1].weight * item[1].confidence, reverse=True)
        
        # Return top 3 with positive weight
        return {k: v.weight for k, v in sorted_genres[:3] if v.weight > 0}
        
    def get_preferred_directors_and_actors(self, user_id: str) -> Dict[str, List[str]]:
        """Phase 4: Returns top directors and actors for the PersonalizationGenerator."""
        profile = self._get_and_decay_profile(user_id)
        if not profile:
            return {"directors": [], "actors": []}
            
        directors = profile.preferences.directors
        actors = profile.preferences.actors
        
        top_dirs = [k for k, v in sorted(directors.items(), key=lambda i: i[1].weight, reverse=True) if v.weight > 0.5][:2]
        top_acts = [k for k, v in sorted(actors.items(), key=lambda i: i[1].weight, reverse=True) if v.weight > 0.5][:2]
        
        return {"directors": top_dirs, "actors": top_acts}
        
    def get_ranking_signals(self, user_id: str, movie_meta: Dict[str, Any]) -> PersonalizationSignal:
        """Phase 5: Returns feature vector components for ranking."""
        profile = self._get_and_decay_profile(user_id)
        if not profile:
            return PersonalizationSignal(is_cold_start=True)
            
        signal = PersonalizationSignal(is_cold_start=False)
        
        # Calculate affinity based on movie metadata
        genres = movie_meta.get("genres", "").split("|")
        for g in genres:
            if g in profile.preferences.genres:
                pref = profile.preferences.genres[g]
                signal.genre_affinity += (pref.weight * pref.confidence)
                
        directors = movie_meta.get("director", "").split(", ")
        for d in directors:
            if d in profile.preferences.directors:
                pref = profile.preferences.directors[d]
                signal.director_affinity += (pref.weight * pref.confidence)
                
        actors = movie_meta.get("cast", "").split(", ")
        for a in actors:
            if a in profile.preferences.actors:
                pref = profile.preferences.actors[a]
                signal.actor_affinity += (pref.weight * pref.confidence)
                
        # Normalize roughly (just cap at 1.0 for now)
        signal.genre_affinity = max(-1.0, min(1.0, signal.genre_affinity))
        signal.director_affinity = max(-1.0, min(1.0, signal.director_affinity))
        signal.actor_affinity = max(-1.0, min(1.0, signal.actor_affinity))
        
        return signal
        
    def get_presentation_profile(self, user_id: str) -> str:
        """Phase 6: Suggests a presentation profile based on behavior."""
        profile = self._get_and_decay_profile(user_id)
        if not profile:
            return "concise" # Default for cold start
            
        behavior = profile.behavior
        
        # If they skip a lot or don't spend much time, keep it concise
        if behavior.skip_rate > 0.6 or behavior.total_clicks == 0:
            return "concise"
            
        # If they engage deeply (saves, lots of clicks), maybe detailed
        if behavior.total_saves > 5 or behavior.total_clicks > 20:
            return "detailed"
            
        return "concise"
        
    def get_diagnostics(self, user_id: str) -> Dict[str, Any]:
        """Exposes platform health metrics."""
        profile = self.store.get_profile(user_id)
        if not profile:
            return {"cold_start": True}
            
        prefs_count = len(profile.preferences.genres) + len(profile.preferences.directors) + len(profile.preferences.actors)
        
        return {
            "profile_version": profile.schema_version,
            "profile_revision": profile.revision,
            "preferences_updated": prefs_count,
            "cold_start": False
        }
