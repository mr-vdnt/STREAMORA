from __future__ import annotations
from services.repository.catalog_db import CatalogRepository
from services.recommendation.user_intelligence.behavior_profile import BehaviorProfileBuilder
from services.recommendation.user_intelligence.preference_profile import PreferenceProfileBuilder
from services.recommendation.user_intelligence.context_profile import ContextProfileBuilder
from services.recommendation.dtos import UserIntelligenceProfileDTO

class UserIntelligencePlatform:
    """
    Master User Intelligence Platform.
    Synthesizes BehaviorProfile, PreferenceProfile, and ContextProfile into unified UserIntelligenceProfileDTO.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.behavior_builder = BehaviorProfileBuilder(self.repo)
        self.preference_builder = PreferenceProfileBuilder(self.repo)
        self.context_builder = ContextProfileBuilder()

    def get_profile(self, user_id: str) -> UserIntelligenceProfileDTO:
        b = self.behavior_builder.build_behavior(user_id)
        p = self.preference_builder.build_preferences(user_id)

        return UserIntelligenceProfileDTO(
            user_id=user_id,
            genre_affinities=p["genre_affinities"],
            theme_affinities=p["theme_affinities"],
            mood_affinities=p["mood_affinities"],
            person_affinities=p["person_affinities"],
            franchise_affinities=p["franchise_affinities"],
            language_affinities=p["language_affinities"],
            runtime_preference="standard",
            freshness_preference=0.6,
            novelty_preference=0.5,
            popularity_bias=0.5,
            completion_rate=b["completion_rate"],
            total_searches=b["total_searches"],
            total_watches=b["total_watches"]
        )
