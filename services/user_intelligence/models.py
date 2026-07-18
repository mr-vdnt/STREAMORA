from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum
import datetime

class UserEventType(str, Enum):
    SEARCH = "SEARCH"
    CLICK = "CLICK"
    SAVE = "SAVE"
    HIDE = "HIDE"
    RATE = "RATE"
    WATCH = "WATCH"
    DISMISS = "DISMISS"
    FILTER = "FILTER"
    SHOW_MORE = "SHOW_MORE"

class UserEvent(BaseModel):
    event_type: UserEventType
    user_id: str
    content_id: Optional[int] = None
    query: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    session_id: Optional[str] = None

class PreferenceEntry(BaseModel):
    weight: float = 0.0
    confidence: float = 0.0

class Preferences(BaseModel):
    genres: Dict[str, PreferenceEntry] = Field(default_factory=dict)
    directors: Dict[str, PreferenceEntry] = Field(default_factory=dict)
    actors: Dict[str, PreferenceEntry] = Field(default_factory=dict)
    themes: Dict[str, PreferenceEntry] = Field(default_factory=dict)
    languages: Dict[str, PreferenceEntry] = Field(default_factory=dict)
    decades: Dict[str, PreferenceEntry] = Field(default_factory=dict)

class BehaviorMetrics(BaseModel):
    total_searches: int = 0
    total_clicks: int = 0
    total_saves: int = 0
    total_hides: int = 0
    skip_rate: float = 0.0
    average_session_length_seconds: float = 0.0

class InteractionHistory(BaseModel):
    recent_queries: List[str] = Field(default_factory=list)
    recent_recommendations: List[int] = Field(default_factory=list)
    clicked_movies: List[int] = Field(default_factory=list)
    dismissed_movies: List[int] = Field(default_factory=list)
    saved_movies: List[int] = Field(default_factory=list)

class UserProfile(BaseModel):
    schema_version: str = "1.0"
    revision: int = 1
    user_id: str
    preferences: Preferences = Field(default_factory=Preferences)
    behavior: BehaviorMetrics = Field(default_factory=BehaviorMetrics)
    history: InteractionHistory = Field(default_factory=InteractionHistory)
    last_updated: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class PersonalizationSignal(BaseModel):
    genre_affinity: float = 0.0
    director_affinity: float = 0.0
    actor_affinity: float = 0.0
    theme_affinity: float = 0.0
    recent_interest: float = 0.0
    is_cold_start: bool = True
