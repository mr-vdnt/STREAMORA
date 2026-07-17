from typing import Dict, Any, List
from .translator import ExplanationTranslator
from .templates import TemplateSelector
from .generator import ResponseGenerator
from .planner import ResponsePlanner
from .validator import ResponseValidator

class PresentationEngine:
    """Orchestrates the conversion of Phase 5 Recommendation Packages into UI-ready responses."""
    
    def __init__(self, movies_db: dict):
        self.movies_db = movies_db
        self.translator = ExplanationTranslator()
        self.template_selector = TemplateSelector()
        self.generator = ResponseGenerator()
        self.planner = ResponsePlanner()
        self.validator = ResponseValidator()
        
    def _get_movie_metadata(self, row: dict) -> dict:
        """Helper to safely extract movie metadata from DB row"""
        return {
            "director": str(row.get('director', '')),
            "cast": str(row.get('cast', '')),
            "genres": str(row.get('genres', '')),
            "themes": str(row.get('themes', '')),
            "runtime": str(row.get('runtime', '')),
            "year": str(row.get('year', '')),
            "rating": str(row.get('rating', ''))
        }
        
    def present(self, query: str, intent: str, recommendation_package: Any, profile: str = "concise") -> Dict[str, Any]:
        """
        Takes the Phase 5 output and formats it for Phase 6 presentation.
        """
        recs = recommendation_package.recommendations
        
        # 1. Format the UI Response Data
        response_data = []
        for rec in recs:
            iid = rec.content_id
            if iid not in self.movies_db:
                continue
                
            movie = self.movies_db[iid]
            rich_meta = self._get_movie_metadata(movie)
            
            # Translate structured reasons to natural text
            human_reasons = self.translator.translate(rec.explainability.reason_codes)
            
            ui_explanation = f"Reason: {human_reasons} (Score: {rec.ranking.recommendation_score:.1f}, Confidence: {rec.ranking.confidence:.2f})"
            
            response_data.append({
                "item_id": iid,
                "title": movie.get('title', ''),
                "poster_url": movie.get('poster_url', ''),
                "backdrop_url": movie.get('backdrop_url', ''),
                "overview": movie.get('overview', ''),
                "rich_metadata": rich_meta,
                "explanation": ui_explanation
            })
            
        # 2. Plan Response Strategy
        render_plan = self.planner.plan(query, intent, response_data, profile)
        
        # 3. Select Template
        template = self.template_selector.select_template(render_plan)
        
        # 4. Generate Natural Language
        llm_text = self.generator.generate(query, template, render_plan)
        
        # 5. Validate LLM Response
        if render_plan["strategy"] != "deterministic":
            is_valid = self.validator.validate(llm_text, render_plan)
            if not is_valid:
                # Fallback to deterministic intro if validation fails
                llm_text = render_plan.get("intro", "I found some movies you might enjoy!")
        
        # 6. Return Final Package for the API
        return {
            "query": query,
            "intent": intent,
            "response": response_data,
            "llm_response": llm_text,
            "actions": render_plan.get("actions", []),
            "diagnostics": {
                "strategy": render_plan["strategy"],
                "profile": profile
            }
        }
