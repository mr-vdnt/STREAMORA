import pytest
from services.presentation.translator import ExplanationTranslator
from services.presentation.templates import TemplateSelector
from services.presentation.engine import PresentationEngine
from services.presentation.planner import ResponsePlanner
from services.presentation.validator import ResponseValidator

def test_explanation_translator():
    translator = ExplanationTranslator()
    
    assert translator.translate([]) == "Matches your search criteria"
    assert translator.translate(["INVALID_CODE"]) == "Matches your search criteria"
    assert "Directed by the same person" in translator.translate(["DIRECTOR_MATCH", "GENRE_MATCH"])
    assert "Shares similar genres" in translator.translate(["DIRECTOR_MATCH", "GENRE_MATCH"])

def test_response_planner():
    planner = ResponsePlanner(max_recommendations_in_text=2)
    
    # 0 results
    plan_zero = planner.plan("query", "search", [])
    assert plan_zero["strategy"] == "deterministic"
    assert plan_zero["response_type"] == "no_results"
    assert "Try a broader search" in [a["label"] for a in plan_zero["actions"]]
    
    # 1 result
    ui_data_one = [{"title": "Inception", "explanation": "Reason: Director (Score: 1, Confidence: 1)"}]
    plan_one = planner.plan("query", "search", ui_data_one)
    assert plan_one["strategy"] == "deterministic"
    assert plan_one["response_type"] == "single_recommendation"
    assert "Show Similar" in [a["label"] for a in plan_one["actions"]]
    
    # Multiple results
    ui_data_many = [
        {"title": "Inception", "explanation": "Reason: Director (Score: 1, Confidence: 1)"},
        {"title": "Interstellar", "explanation": "Reason: Genre (Score: 1, Confidence: 1)"},
        {"title": "Tenet", "explanation": "Reason: Vibe (Score: 1, Confidence: 1)"}
    ]
    plan_many = planner.plan("query", "search", ui_data_many, profile="enthusiastic")
    assert plan_many["strategy"] == "llm"
    assert plan_many["profile"] == "enthusiastic"
    assert len(plan_many["items"]) == 2 # Testing max_recommendations_in_text

def test_response_validator():
    validator = ResponseValidator()
    
    render_plan = {
        "items": [{"title": "Batman Begins"}]
    }
    
    # Valid
    assert validator.validate("I recommend Batman Begins because it's great.", render_plan) == True
    assert validator.validate("BATMAN BEGINS is a good choice.", render_plan) == True
    
    # Hallucination (doesn't mention the recommended title)
    assert validator.validate("I recommend The Dark Knight.", render_plan) == False
    
    # Empty string
    assert validator.validate("", render_plan) == False

def test_template_selector_profiles():
    selector = TemplateSelector()
    
    render_plan_concise = {"profile": "concise"}
    t_concise = selector.select_template(render_plan_concise)
    assert "Keep it to 2 sentences." in t_concise["system_prompt"]
    
    render_plan_enthusiastic = {"profile": "enthusiastic"}
    t_enthusiastic = selector.select_template(render_plan_enthusiastic)
    assert "extremely enthusiastic" in t_enthusiastic["system_prompt"]

# A basic test for the Presentation Engine logic, mocking Ollama to prevent network calls in CI
def test_presentation_engine_mocked_llm(monkeypatch):
    movies_db = {
        1: {"title": "Batman Begins", "director": "Christopher Nolan"},
        2: {"title": "The Dark Knight", "director": "Christopher Nolan"}
    }
    
    engine = PresentationEngine(movies_db)
    
    # Mock Ollama generator to return a valid string that passes validation
    class MockGenerator:
        def generate(self, query, template, render_plan):
            return "Mocked response mentioning Batman Begins and The Dark Knight."
            
    engine.generator = MockGenerator()
    
    # Create a mock recommendation package
    class MockRank:
        recommendation_score = 90.0
        confidence = 0.9
        
    class MockExplain:
        reason_codes = ["DIRECTOR_MATCH"]
        
    class MockRec1:
        content_id = 1
        ranking = MockRank()
        explainability = MockExplain()
        
    class MockRec2:
        content_id = 2
        ranking = MockRank()
        explainability = MockExplain()
        
    class MockPackage:
        recommendations = [MockRec1(), MockRec2()]
        
    res = engine.present("nolan movies", "search", MockPackage(), profile="detailed")
    
    assert "Mocked response" in res["llm_response"]
    assert len(res["response"]) == 2
    assert res["response"][0]["title"] == "Batman Begins"
    assert "Directed by the same person" in res["response"][0]["explanation"]
    assert "actions" in res
    assert res["diagnostics"]["profile"] == "detailed"
