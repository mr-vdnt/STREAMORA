from typing import Dict, Any
from .models import UserProfile, UserEvent, UserEventType, PreferenceEntry
import datetime

class PreferenceEngine:
    """Updates user preferences and applies time decay."""
    
    # Weight applied based on the strength of the interaction
    EVENT_WEIGHTS = {
        UserEventType.SEARCH: 0.1,
        UserEventType.CLICK: 0.2,
        UserEventType.SAVE: 0.5,
        UserEventType.WATCH: 0.8,
        UserEventType.RATE: 0.5, # Positive rating
        UserEventType.HIDE: -0.5,
        UserEventType.DISMISS: -0.2,
    }
    
    def process_event(self, profile: UserProfile, event: UserEvent, movie_meta: Dict[str, Any]) -> None:
        """Update preferences based on an event interacting with a movie."""
        weight_delta = self.EVENT_WEIGHTS.get(event.event_type, 0.0)
        
        if weight_delta == 0.0:
            return
            
        # Update genres
        for genre in movie_meta.get("genres", "").split("|"):
            if genre:
                self._update_entry(profile.preferences.genres, genre, weight_delta)
                
        # Update directors
        for director in movie_meta.get("director", "").split(", "):
            if director:
                self._update_entry(profile.preferences.directors, director, weight_delta)
                
        # Update actors
        for actor in movie_meta.get("cast", "").split(", "):
            if actor:
                self._update_entry(profile.preferences.actors, actor, weight_delta * 0.5) # Actors usually less weighted than directors
                
    def _update_entry(self, category_dict: Dict[str, PreferenceEntry], key: str, delta: float) -> None:
        if key not in category_dict:
            category_dict[key] = PreferenceEntry(weight=0.0, confidence=0.0)
            
        entry = category_dict[key]
        
        # Simple update rule: add delta, bound between -1.0 and 1.0
        entry.weight = max(-1.0, min(1.0, entry.weight + delta))
        
        # Increase confidence with every interaction (up to 1.0)
        entry.confidence = min(1.0, entry.confidence + 0.1)
        
    def decay_preferences(self, profile: UserProfile, days_elapsed: float) -> None:
        """Gradually decays preferences over time to favor recent interests."""
        decay_factor = max(0.0, 1.0 - (days_elapsed * 0.01)) # Lose 1% weight per day
        
        def _decay(category_dict: Dict[str, PreferenceEntry]):
            for key, entry in category_dict.items():
                entry.weight *= decay_factor
                entry.confidence *= decay_factor
                
        _decay(profile.preferences.genres)
        _decay(profile.preferences.directors)
        _decay(profile.preferences.actors)
        _decay(profile.preferences.themes)
        _decay(profile.preferences.languages)
        _decay(profile.preferences.decades)
