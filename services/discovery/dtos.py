from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class CollectionDTO:
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    backdrop_url: Optional[str] = None
    category: str = "spotlight"
    item_count: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DiscoveryHubDTO:
    slug: str
    title: str
    hub_type: str  # genre, mood, franchise, collection
    description: Optional[str] = None
    backdrop_url: Optional[str] = None
    shelves: List[Dict[str, Any]] = field(default_factory=list)
