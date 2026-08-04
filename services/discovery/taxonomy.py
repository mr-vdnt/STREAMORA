from enum import Enum

class HubType(Enum):
    GENRE = "genre"
    MOOD = "mood"
    FRANCHISE = "franchise"
    COLLECTION = "collection"
    SPOTLIGHT = "spotlight"

class CollectionCategory(Enum):
    SPOTLIGHT = "spotlight"
    FRANCHISE = "franchise"
    THEMATIC = "thematic"
    DISCOVERY = "discovery"
