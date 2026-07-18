from .models import UserProfile, UserEvent, UserEventType

class InteractionHistoryEngine:
    """Maintains structured interaction history and recommendation memory."""
    
    def __init__(self, max_history_size: int = 50):
        self.max_history_size = max_history_size
        
    def process_event(self, profile: UserProfile, event: UserEvent) -> None:
        """Records the event into the user's history."""
        history = profile.history
        
        if event.event_type == UserEventType.SEARCH and event.query:
            self._append_bounded(history.recent_queries, event.query)
            
        elif event.event_type == UserEventType.CLICK and event.content_id:
            self._append_bounded(history.clicked_movies, event.content_id)
            
        elif event.event_type == UserEventType.SAVE and event.content_id:
            self._append_bounded(history.saved_movies, event.content_id)
            
        elif (event.event_type == UserEventType.HIDE or event.event_type == UserEventType.DISMISS) and event.content_id:
            self._append_bounded(history.dismissed_movies, event.content_id)
            
    def record_recommendations(self, profile: UserProfile, content_ids: list[int]) -> None:
        """Records recently recommended items so we don't repeat them too soon."""
        for cid in content_ids:
            self._append_bounded(profile.history.recent_recommendations, cid)
            
    def _append_bounded(self, lst: list, item: any) -> None:
        if item in lst:
            lst.remove(item) # Move to front/end to update recency
        lst.append(item)
        
        if len(lst) > self.max_history_size:
            lst.pop(0)
