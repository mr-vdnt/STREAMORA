from typing import Dict, Any, List
from .models import UserEvent
from .storage import ProfileStore
from .preference_engine import PreferenceEngine
from .behavior import BehaviorAnalyticsEngine
from .history import InteractionHistoryEngine

class EventBus:
    """Routes events to the appropriate engines."""
    
    def __init__(self, store: ProfileStore, movies_db: Dict[int, Any]):
        self.store = store
        self.movies_db = movies_db
        self.preference_engine = PreferenceEngine()
        self.behavior_engine = BehaviorAnalyticsEngine()
        self.history_engine = InteractionHistoryEngine()
        
    def dispatch(self, event: UserEvent) -> None:
        """Processes an event by fetching the profile, routing to engines, and saving."""
        profile = self.store.get_profile(event.user_id)
        if not profile:
            # Cold start user creation
            from .models import UserProfile
            profile = UserProfile(user_id=event.user_id)
            
        # Get movie metadata if applicable
        movie_meta = {}
        if event.content_id and event.content_id in self.movies_db:
            movie_meta = self.movies_db[event.content_id]
            
        # 1. Update Preferences
        self.preference_engine.process_event(profile, event, movie_meta)
        
        # 2. Update Behavior
        self.behavior_engine.process_event(profile, event)
        
        # 3. Update History
        self.history_engine.process_event(profile, event)
        
        # Save back to store
        self.store.save_profile(profile)
        
    def record_recommendations(self, user_id: str, content_ids: List[int]) -> None:
        """Records recommendations directly to history."""
        profile = self.store.get_profile(user_id)
        if profile:
            self.history_engine.record_recommendations(profile, content_ids)
            self.store.save_profile(profile)
