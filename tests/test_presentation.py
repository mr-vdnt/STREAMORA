import pytest
from services.presentation.translator import ExplanationTranslator
from services.presentation.templates import TemplateSelector
from services.presentation.engine import PresentationEngine

def test_explanation_translator():
    translator = ExplanationTranslator()
    
    assert translator.translate([]) == "Matches your search criteria"
    assert translator.translate(["INVALID_CODE"]) == "Matches your search criteria"
    assert "Directed by the same person" in translator.translate(["DIRECTOR_MATCH", "GENRE_MATCH"])
    assert "Shares similar genres" in translator.translate(["DIRECTOR_MATCH", "GENRE_MATCH"])

def test_template_selector():
    selector = TemplateSelector()
    
    t_zero = selector.select_template("query", 0)
    assert t_zero["posture"] == "apologetic"
    
    t_one = selector.select_template("query", 1)
    assert t_one["posture"] == "confident"
    
    t_many = selector.select_template("query", 5)
    assert t_many["posture"] == "curated"

# A basic test for the Presentation Engine logic, mocking Ollama to prevent network calls in CI
def test_presentation_engine_mocked_llm(monkeypatch):
    movies_db = {
        1: {"title": "Batman Begins", "director": "Christopher Nolan"}
    }
    
    engine = PresentationEngine(movies_db)
    
    # Mock Ollama generator to just return a static string
    class MockGenerator:
        def generate(self, query, template, context_data):
            return "Mocked response"
            
    engine.generator = MockGenerator()
    
    # Create a mock recommendation package
    class MockRank:
        recommendation_score = 90.0
        confidence = 0.9
        
    class MockExplain:
        reason_codes = ["DIRECTOR_MATCH"]
        
    class MockRec:
        content_id = 1
        ranking = MockRank()
        explainability = MockExplain()
        
    class MockPackage:
        recommendations = [MockRec()]
        
    res = engine.present("nolan movies", "search", MockPackage())
    
    assert res["llm_response"] == "Mocked response"
    assert len(res["response"]) == 1
    assert res["response"][0]["title"] == "Batman Begins"
    assert "Directed by the same person" in res["response"][0]["explanation"]
