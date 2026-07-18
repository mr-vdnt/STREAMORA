import copy
from abc import ABC, abstractmethod
from typing import Optional
from .models import UserProfile

class ProfileStore(ABC):
    """Abstract interface for User Profile persistence."""
    
    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        pass
        
    @abstractmethod
    def save_profile(self, profile: UserProfile) -> None:
        pass

class InMemoryProfileStore(ProfileStore):
    """In-memory storage for Phase 7 validation."""
    
    def __init__(self):
        self._store = {}
        
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        profile = self._store.get(user_id)
        if profile:
            # Return a deep copy so engines can't mutate without calling save_profile
            return copy.deepcopy(profile)
        return None
        
    def save_profile(self, profile: UserProfile) -> None:
        # Increment revision and update timestamp
        profile.revision += 1
        import datetime
        profile.last_updated = datetime.datetime.utcnow().isoformat()
        
        self._store[profile.user_id] = copy.deepcopy(profile)
