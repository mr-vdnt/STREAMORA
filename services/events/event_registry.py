from enum import Enum

class EventTopic(Enum):
    USER_REGISTERED = "user.registered"
    WATCH_PROGRESS_LOGGED = "watch.progress_logged"
    WATCH_COMPLETED = "watch.completed"
    SEARCH_EXECUTED = "search.executed"
    RECOMMENDATION_GENERATED = "recommendation.generated"
    CATALOG_ITEM_UPDATED = "catalog.item_updated"
    HERO_BANNER_REFRESHED = "hero.banner_refreshed"
