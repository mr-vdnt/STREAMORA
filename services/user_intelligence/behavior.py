from .models import UserProfile, UserEvent, UserEventType

class BehaviorAnalyticsEngine:
    """Tracks broad user behavioral metrics."""
    
    def process_event(self, profile: UserProfile, event: UserEvent) -> None:
        """Update behavior metrics based on the event."""
        metrics = profile.behavior
        
        if event.event_type == UserEventType.SEARCH:
            metrics.total_searches += 1
        elif event.event_type == UserEventType.CLICK:
            metrics.total_clicks += 1
        elif event.event_type == UserEventType.SAVE:
            metrics.total_saves += 1
        elif event.event_type == UserEventType.HIDE or event.event_type == UserEventType.DISMISS:
            metrics.total_hides += 1
            
        # Recalculate skip rate (simplified: hides / (clicks + saves + hides))
        total_interactions = metrics.total_clicks + metrics.total_saves + metrics.total_hides
        if total_interactions > 0:
            metrics.skip_rate = metrics.total_hides / float(total_interactions)
