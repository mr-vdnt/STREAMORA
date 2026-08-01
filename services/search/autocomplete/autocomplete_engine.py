from __future__ import annotations
import unicodedata
from typing import Any, Dict, List
from services.repository.catalog_db import CatalogRepository, Content, SearchDocument, KnowledgeFact, FranchiseUniverse
from services.search.dtos import AutocompleteResponseDTO, AutocompleteCategoryDTO

class MultiEntityAutocompleteEngine:
    """
    Multi-Entity Autocomplete Engine powering real-time search-as-you-type dropdowns across:
    - Titles (Movies & Series)
    - Persons (Actors & Directors)
    - Franchises & Universes
    - Themes & Moods
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def autocomplete(self, raw_query: str) -> AutocompleteResponseDTO:
        q = raw_query.strip().lower()
        if len(q) < 2:
            return AutocompleteResponseDTO(query=raw_query, categories=[])

        categories_map: Dict[str, List[Dict[str, Any]]] = {
            "titles": [],
            "persons": [],
            "franchises": [],
            "themes": [],
            "moods": []
        }

        with self.repo.get_session() as session:
            # 1. Title matches
            contents = session.query(Content).filter(Content.is_deleted == False).limit(50).all()
            for c in contents:
                meta = c.metadata_rel
                title = meta.title if meta else ""
                if q in title.lower():
                    categories_map["titles"].append({
                        "id": c.id,
                        "title": title,
                        "entity_type": c.entity_type,
                        "slug": c.slug,
                        "poster_url": c.artwork_rel.poster_url if c.artwork_rel else None
                    })

            # 2. Franchise matches
            franchises = session.query(FranchiseUniverse).filter(FranchiseUniverse.name.ilike(f"%{q}%")).limit(5).all()
            for f in franchises:
                categories_map["franchises"].append({
                    "id": f.id,
                    "name": f.name,
                    "slug": f.slug
                })

            # 3. Theme & Mood matches from KnowledgeFact
            facts = session.query(KnowledgeFact).filter(
                KnowledgeFact.state == "ACTIVE",
                KnowledgeFact.value.ilike(f"%{q}%")
            ).limit(10).all()

            for fact in facts:
                val_clean = fact.value.replace("genre-", "").replace("-", " ")
                item = {"value": val_clean, "category": fact.category}
                if fact.category == "theme" and item not in categories_map["themes"]:
                    categories_map["themes"].append(item)
                elif fact.category == "mood" and item not in categories_map["moods"]:
                    categories_map["moods"].append(item)

        categories_dto = [
            AutocompleteCategoryDTO(category=cat, items=items[:5])
            for cat, items in categories_map.items() if items
        ]

        return AutocompleteResponseDTO(query=raw_query, categories=categories_dto)
