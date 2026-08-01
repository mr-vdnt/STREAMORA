"""
STREAMORA - Milestone 5 Regression Test Suite
Validates Recommendation Engine, Hero Selector, Personalized Home Shelves, and Explanation Signals.
"""
import pytest
from fastapi.testclient import TestClient
from services.agent.main import app
from services.recommendation.explanation_engine import ExplanationEngine

client = TestClient(app)

def test_home_payload_structure():
    response = client.get("/api/v2/home")
    assert response.status_code == 200
    data = response.json()
    assert "hero" in data
    assert "sections" in data
    assert len(data["sections"]) > 0

def test_recommendation_explanation_generator():
    engine = ExplanationEngine()
    item = {"title": "Arrival", "rating": 8.9, "genres": "Sci-Fi|Drama|Mystery"}
    seed = {"title": "Interstellar"}
    
    explanation = engine.generate_detailed_explanation(item, seed_item=seed)
    assert explanation["reason"] == "Because you watched Interstellar"
    assert explanation["match_score"] == 94
    assert "Sci-Fi" in explanation["shared_themes"]
