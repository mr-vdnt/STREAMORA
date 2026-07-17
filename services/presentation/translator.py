class ExplanationTranslator:
    """Translates structured reason codes from the Decision Engine into human-readable snippets."""
    
    TRANSLATIONS = {
        "DIRECTOR_MATCH": "Directed by the same person",
        "FRANCHISE_MATCH": "Part of the same franchise",
        "GENRE_MATCH": "Shares similar genres",
        "THEME_MATCH": "Explores similar themes",
        "ACTOR_MATCH": "Features the same actors",
        "HIGH_SEMANTIC_SIMILARITY": "Has a very similar vibe"
    }
    
    def translate(self, reason_codes: list) -> str:
        """Translates a list of reason codes into a comma-separated string."""
        if not reason_codes:
            return "Matches your search criteria"
            
        translated = []
        for code in reason_codes:
            if code in self.TRANSLATIONS:
                translated.append(self.TRANSLATIONS[code])
                
        if not translated:
            return "Matches your search criteria"
            
        return ", ".join(translated)
