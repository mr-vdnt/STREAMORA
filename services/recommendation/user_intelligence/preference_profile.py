from __future__ import annotations
import json
from typing import Dict, Any
from services.repository.catalog_db import CatalogRepository, UserProfile, KnowledgeFact

class PreferenceProfileBuilder:
    """
    Builds genre, theme, mood, person, and franchise affinity vectors for a user.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()

    def build_preferences(self, user_id: str) -> Dict[str, Any]:
        with self.repo.get_session() as session:
            prof = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if prof:
                return {
                    "genre_affinities": json.loads(prof.genre_affinities_json) if prof.genre_affinities_json else {"Sci-Fi": 0.9, "Action": 0.7},
                    "theme_affinities": json.loads(prof.theme_affinities_json) if prof.theme_affinities_json else {"dream": 0.85, "space": 0.75},
                    "mood_affinities": json.loads(prof.mood_affinities_json) if prof.mood_affinities_json else {"mind-bending": 0.88, "suspenseful": 0.70},
                    "person_affinities": json.loads(prof.person_affinities_json) if prof.person_affinities_json else {"Christopher Nolan": 0.95},
                    "franchise_affinities": json.loads(prof.franchise_affinities_json) if prof.franchise_affinities_json else {"Spider-Man": 0.80},
                    "language_affinities": json.loads(prof.language_affinities_json) if prof.language_affinities_json else {"en": 1.0}
                }

            # Baseline default profile
            return {
                "genre_affinities": {"Sci-Fi": 0.85, "Action": 0.75, "Drama": 0.60},
                "theme_affinities": {"dream": 0.80, "space": 0.70},
                "mood_affinities": {"mind-bending": 0.85, "suspenseful": 0.75},
                "person_affinities": {"Christopher Nolan": 0.90},
                "franchise_affinities": {},
                "language_affinities": {"en": 1.0}
            }
