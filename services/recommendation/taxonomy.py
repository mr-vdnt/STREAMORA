from enum import Enum

class SlateType(Enum):
    HOME_FEED = "home_feed"
    PERSONALIZED_HOME = "personalized_home"
    BECAUSE_YOU_WATCHED = "because_you_watched"
    CONTINUE_WATCHING = "continue_watching"
    TRENDING_FOR_YOU = "trending_for_you"
    NEW_RELEASES = "new_releases"
    COLD_START = "cold_start"
    GENRE_SHELF = "genre_shelf"
    MOOD_SHELF = "mood_shelf"
    EXPLORE = "explore"
    HERO_BANNER = "hero_banner"

class InteractionType(Enum):
    WATCH = "watch"
    CLICK = "click"
    RATE = "rate"
    SEARCH_FOLLOWTHROUGH = "search_followthrough"
    DISMISS = "dismiss"
    COMPLETE = "complete"
    WATCHLIST = "watchlist"

class CandidateSource(Enum):
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    SEARCH_BEHAVIORAL = "search_behavioral"
    TRENDING = "trending"
    FRESH_RELEASE = "fresh_release"
    EXPLORATION = "exploration"
    EDITORIAL = "editorial"
    CONTINUE_WATCHING = "continue_watching"
