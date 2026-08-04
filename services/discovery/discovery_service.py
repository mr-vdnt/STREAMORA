from __future__ import annotations
import json
from typing import Dict, List, Optional, Any
from services.repository.catalog_db import CatalogRepository, DiscoveryCollection, FranchiseUniverse, KnowledgeFact, Content
from services.discovery.dtos import DiscoveryHubDTO, CollectionDTO

class DiscoveryPlatformService:
    """
    Workstream 1 Discovery Intelligence Platform.
    Builds genre hubs, mood hubs, franchise universes, and curated thematic collections.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def get_collections(self) -> List[CollectionDTO]:
        with self.repo.get_session() as session:
            collections = session.query(DiscoveryCollection).filter(DiscoveryCollection.is_featured == True).all()
            if not collections:
                # Seed default collection if empty
                self._seed_default_collections(session)
                collections = session.query(DiscoveryCollection).filter(DiscoveryCollection.is_featured == True).all()

            results: List[CollectionDTO] = []
            for col in collections:
                content_ids = json.loads(col.content_ids_json) if col.content_ids_json else [1, 2]
                items = [self.repo.get_by_id(cid) for cid in content_ids if self.repo.get_by_id(cid)]
                results.append(CollectionDTO(
                    id=col.id,
                    slug=col.slug,
                    title=col.title,
                    description=col.description,
                    backdrop_url=col.backdrop_url,
                    category=col.category,
                    item_count=len(items),
                    items=items
                ))
            return results

    def get_hub(self, hub_slug: str) -> DiscoveryHubDTO:
        with self.repo.get_session() as session:
            # 1. Check Franchise Universe
            uni = session.query(FranchiseUniverse).filter(FranchiseUniverse.slug == hub_slug).first()
            if uni:
                return DiscoveryHubDTO(
                    slug=uni.slug,
                    title=uni.name,
                    hub_type="franchise",
                    description=uni.description,
                    backdrop_url=uni.backdrop_url,
                    shelves=[{
                        "title": f"The {uni.name} Universe",
                        "items": [self.repo.get_by_id(1), self.repo.get_by_id(2)]
                    }]
                )

            # 2. Check Theme / Mood KnowledgeFact Hub
            facts = session.query(KnowledgeFact).filter(KnowledgeFact.state == "ACTIVE").all()
            matched_items = []
            for f in facts:
                if hub_slug in f.value.lower():
                    item = self.repo.get_by_id(f.content_id)
                    if item and item not in matched_items:
                        matched_items.append(item)

            title = hub_slug.replace("-", " ").title()
            return DiscoveryHubDTO(
                slug=hub_slug,
                title=f"{title} Hub",
                hub_type="mood",
                description=f"Explore the finest {title} movies and series on Streamora.",
                shelves=[{
                    "title": f"Top Picks in {title}",
                    "items": matched_items if matched_items else [self.repo.get_by_id(1)]
                }]
            )

    def _seed_default_collections(self, session):
        col1 = DiscoveryCollection(
            slug="christopher-nolan-spotlight",
            title="Christopher Nolan Masterpieces",
            description="Mind-bending thrillers and epic non-linear narratives.",
            backdrop_url="https://image.tmdb.org/t/p/original/s3TBrRGB1iav7ySaNx3HjuEGBh6.jpg",
            category="spotlight",
            content_ids_json=json.dumps([1]),
            is_featured=True
        )
        col2 = DiscoveryCollection(
            slug="marvel-cinematic-universe",
            title="Marvel Cinematic Universe",
            description="Explore the interconnected superhero franchise timeline.",
            backdrop_url="https://image.tmdb.org/t/p/original/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
            category="franchise",
            content_ids_json=json.dumps([2]),
            is_featured=True
        )
        session.add_all([col1, col2])
        session.commit()
