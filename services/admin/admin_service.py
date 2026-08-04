from __future__ import annotations
from typing import Dict, List, Optional, Any
from services.repository.catalog_db import (
    CatalogRepository, Content, UserAccount, DiscoveryCollection, SearchEvent, RecommendationEvent
)

class AdminPlatformService:
    """
    Admin Platform Service.
    Content management, user administration, collection curation, hero banner overrides, and system health reporting.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def get_system_overview(self) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            total_content = session.query(Content).count()
            total_users = session.query(UserAccount).count()
            total_collections = session.query(DiscoveryCollection).count()
            total_searches = session.query(SearchEvent).count()
            total_recommendations = session.query(RecommendationEvent).count()

            return {
                "platform_status": "HEALTHY",
                "version": "1.0.0-launch",
                "metrics": {
                    "total_catalog_items": total_content,
                    "total_user_accounts": total_users,
                    "total_collections": total_collections,
                    "total_search_queries": total_searches,
                    "total_recommendation_events": total_recommendations
                }
            }

    def list_users(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.repo.get_session() as session:
            users = session.query(UserAccount).limit(limit).all()
            return [
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_active": u.is_active,
                    "is_admin": u.is_admin,
                    "created_at": u.created_at.isoformat()
                }
                for u in users
            ]

    def create_collection_override(
        self,
        slug: str,
        title: str,
        description: str,
        content_ids: List[int],
        category: str = "spotlight"
    ) -> Dict[str, Any]:
        import json
        with self.repo.get_session() as session:
            col = session.query(DiscoveryCollection).filter(DiscoveryCollection.slug == slug).first()
            if not col:
                col = DiscoveryCollection(
                    slug=slug,
                    title=title,
                    description=description,
                    category=category,
                    content_ids_json=json.dumps(content_ids),
                    is_featured=True
                )
                session.add(col)
            else:
                col.title = title
                col.description = description
                col.content_ids_json = json.dumps(content_ids)

            session.commit()
            session.refresh(col)

            return {
                "id": col.id,
                "slug": col.slug,
                "title": col.title,
                "content_ids": content_ids
            }
