import pytest
import datetime
from services.user_intelligence.models import UserEvent, UserEventType, UserProfile
from services.user_intelligence.storage import InMemoryProfileStore
from services.user_intelligence.bus import EventBus
from services.user_intelligence.adapter import PersonalizationAdapter

@pytest.fixture
def store():
    return InMemoryProfileStore()

@pytest.fixture
def mock_db():
    return {
        1: {"title": "Inception", "director": "Christopher Nolan", "genres": "Sci-Fi|Action", "cast": "Leonardo DiCaprio, Joseph Gordon-Levitt"},
        2: {"title": "The Dark Knight", "director": "Christopher Nolan", "genres": "Action|Crime", "cast": "Christian Bale, Heath Ledger"}
    }

@pytest.fixture
def event_bus(store, mock_db):
    return EventBus(store, mock_db)
    
@pytest.fixture
def adapter(store):
    return PersonalizationAdapter(store)

def test_preference_evolution(store, event_bus):
    # Process a click on Inception
    event = UserEvent(event_type=UserEventType.CLICK, user_id="user123", content_id=1)
    event_bus.dispatch(event)
    
    profile = store.get_profile("user123")
    assert profile is not None
    assert profile.revision == 2 # 1 initially, then saved +1
    
    # Check preferences
    nolan_pref = profile.preferences.directors.get("Christopher Nolan")
    assert nolan_pref is not None
    assert nolan_pref.weight > 0.0 # CLICK weight is positive
    
    sci_fi_pref = profile.preferences.genres.get("Sci-Fi")
    assert sci_fi_pref.weight > 0.0
    
    leo_pref = profile.preferences.actors.get("Leonardo DiCaprio")
    assert leo_pref.weight > 0.0
    
    # Check history
    assert 1 in profile.history.clicked_movies
    
    # Check behavior
    assert profile.behavior.total_clicks == 1

def test_negative_feedback(store, event_bus):
    # Hide Inception
    event = UserEvent(event_type=UserEventType.HIDE, user_id="user123", content_id=1)
    event_bus.dispatch(event)
    
    profile = store.get_profile("user123")
    assert profile.preferences.directors["Christopher Nolan"].weight < 0.0
    assert 1 in profile.history.dismissed_movies
    assert profile.behavior.total_hides == 1
    assert profile.behavior.skip_rate == 1.0 # 1 hide / 1 total interactions

def test_preference_decay(store, event_bus, adapter):
    event = UserEvent(event_type=UserEventType.SAVE, user_id="user123", content_id=1)
    event_bus.dispatch(event)
    
    profile = store.get_profile("user123")
    initial_weight = profile.preferences.directors["Christopher Nolan"].weight
    initial_conf = profile.preferences.directors["Christopher Nolan"].confidence
    
    # Artificially age the profile by 10 days by directly modifying the store 
    # to bypass save_profile()'s automatic timestamp update
    old_time = (datetime.datetime.utcnow() - datetime.timedelta(days=10)).isoformat()
    store._store["user123"].last_updated = old_time
    
    # Reading via adapter triggers decay
    signals = adapter.get_ranking_signals("user123", {"director": "Christopher Nolan"})
    
    # 10 days = ~10% decay (factor = 0.9)
    assert signals.director_affinity < (initial_weight * initial_conf)

def test_adapter_cold_start(adapter):
    # User does not exist
    signals = adapter.get_ranking_signals("unknown_user", {"director": "Nolan"})
    assert signals.is_cold_start is True
    assert signals.director_affinity == 0.0
    
    bias = adapter.get_query_bias("unknown_user")
    assert bias == {}
    
    presentation = adapter.get_presentation_profile("unknown_user")
    assert presentation == "concise"

def test_adapter_signals(store, event_bus, adapter):
    # Two positive events for Nolan / Action
    event_bus.dispatch(UserEvent(event_type=UserEventType.WATCH, user_id="user1", content_id=1))
    event_bus.dispatch(UserEvent(event_type=UserEventType.WATCH, user_id="user1", content_id=2))
    
    bias = adapter.get_query_bias("user1")
    assert "Action" in bias # Present in both movies
    assert bias["Action"] > 0
    
    prefs = adapter.get_preferred_directors_and_actors("user1")
    assert "Christopher Nolan" in prefs["directors"]
    
    signals = adapter.get_ranking_signals("user1", {"director": "Christopher Nolan", "genres": "Action"})
    assert signals.is_cold_start is False
    assert signals.director_affinity > 0.0
    assert signals.genre_affinity > 0.0
    
    presentation = adapter.get_presentation_profile("user1")
    assert presentation == "concise" # They only watched, didn't click/save 20+ times
