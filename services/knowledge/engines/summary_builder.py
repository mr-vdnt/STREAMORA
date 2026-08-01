from __future__ import annotations
from typing import Any, Dict, List
from services.knowledge.dtos import KnowledgeFactDTO

class SummaryBuilder:
    """
    Synthesizes atomic facts into 4 tiers of summaries:
    1. summary_short: High-impact 1-sentence hook
    2. summary_medium: 3-bullet structured synopsis
    3. summary_deep: In-depth thematic breakdown
    4. summary_spoiler_free: Clean synopsis
    """

    def build_summaries(self, content_data: Dict[str, Any], facts: List[KnowledgeFactDTO]) -> Dict[str, str]:
        title = content_data.get("title") or "Featured Title"
        overview = content_data.get("overview") or "A compelling story unfolding across space and time."
        entity_type = str(content_data.get("entity_type") or "content").capitalize()

        themes = [f.value.replace("genre-", "").replace("-", " ") for f in facts if f.category == "theme"]
        moods = [f.value.replace("-", " ") for f in facts if f.category == "mood"]
        characters = [f.value for f in facts if f.category == "character" and "archetype-protagonist:" in f.value]

        lead_char = characters[0].replace("archetype-protagonist:", "") if characters else "The protagonist"
        theme_str = ", ".join(themes[:3]) if themes else "action and drama"
        mood_str = ", ".join(moods[:2]) if moods else "thrilling"

        # 1. Short Hook
        short_hook = f"A {mood_str} {entity_type.lower()} following {lead_char} through themes of {theme_str}."

        # 2. Medium 3-Bullet Synopsis
        medium_synopsis = (
            f"• Premise: {overview[:120]}...\n"
            f"• Key Themes: Explores {theme_str} with a {mood_str} emotional tone.\n"
            f"• Core Focus: Centers on {lead_char} navigating pivotal narrative conflicts."
        )

        # 3. Deep Breakdown
        deep_breakdown = (
            f"Streamora Deep Analysis of '{title}':\n"
            f"Overview: {overview}\n"
            f"Thematic Pillars: {theme_str.title()}.\n"
            f"Emotional Resonance: Characterized by {mood_str} narrative elements.\n"
            f"Audience Impact: High engagement designed for fans of {theme_str}."
        )

        # 4. Spoiler-Free Synopsis
        spoiler_free = overview

        return {
            "summary_short": short_hook,
            "summary_medium": medium_synopsis,
            "summary_deep": deep_breakdown,
            "summary_spoiler_free": spoiler_free
        }
