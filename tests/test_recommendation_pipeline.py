import pytest
from services.recommendation.pipeline import RecommendationPipeline
from services.recommendation.stages import PipelineStage

class CustomTestStage(PipelineStage):
    def name(self) -> str:
        return "CustomTestStage"

    def process(self, candidates: list, context: dict) -> list:
        for c in candidates:
            c["custom_flag"] = True
        return candidates

def test_pipeline_registration_and_execution():
    pipeline = RecommendationPipeline.build_default_7_stage_pipeline()
    assert len(pipeline.stages) == 7
    
    pipeline.register(CustomTestStage())
    assert len(pipeline.stages) == 8
    
    mock_candidates = [
        {"id": 1, "title": "Inception", "poster_url": "/p1.jpg", "popularity": 90.0, "rating": 8.8, "genres": "Sci-Fi|Action"},
        {"id": 2, "title": "Interstellar", "poster_url": "/p2.jpg", "popularity": 85.0, "rating": 8.6, "genres": "Sci-Fi|Drama"}
    ]
    
    context = {"output_limit": 10}
    output = pipeline.execute(mock_candidates, context)
    assert len(output) > 0
    assert output[0].get("custom_flag") is True
