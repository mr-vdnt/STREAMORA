from __future__ import annotations
import re
from typing import Dict, List

class QueryRewriteEngine:
    """
    Layer 1 Query Rewrite Engine.
    Handles capitalization normalization, slang expansion (sci-fi -> science fiction), and common alias mapping.
    """

    SYNONYM_MAP = {
        "scifi": "science fiction",
        "sci-fi": "science fiction",
        "romcom": "romantic comedy",
        "rom-com": "romantic comedy",
        "doc": "documentary",
        "anime": "japanese animation",
        "superhero": "superheroic comic book"
    }

    ALIAS_MAP = {
        "spider man": "Spider-Man",
        "spiderman": "Spider-Man",
        "batman": "Batman",
        "harry potter": "Harry Potter",
        "starwars": "Star Wars",
        "lotr": "Lord of the Rings"
    }

    def rewrite(self, raw_query: str) -> str:
        clean = raw_query.strip().lower()

        # 1. Expand slang/abbreviations
        words = clean.split()
        rewritten_words = [self.SYNONYM_MAP.get(w, w) for w in words]
        clean_expanded = " ".join(rewritten_words)

        # 2. Normalize canonical aliases
        for alias, canonical in self.ALIAS_MAP.items():
            if alias in clean_expanded:
                clean_expanded = clean_expanded.replace(alias, canonical)

        return clean_expanded
