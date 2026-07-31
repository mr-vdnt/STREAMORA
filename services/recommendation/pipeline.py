from typing import List, Dict, Any
from services.recommendation.stages import (
    PipelineStage,
    CandidateGenerationStage,
    EligibilityStage,
    BusinessRulesStage,
    PopularityScoringStage,
    SemanticSimilarityStage,
    DiversityStage,
    ExposureDeduplicationStage
)

class RecommendationPipeline:
    """
    Pluggable multi-stage recommendation pipeline executor.
    Supports registering stages dynamically and running candidates through the sequential lifecycle.
    """
    def __init__(self):
        self.stages: List[PipelineStage] = []

    def register(self, stage: PipelineStage) -> 'RecommendationPipeline':
        self.stages.append(stage)
        return self

    def execute(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        current_candidates = candidates
        for stage in self.stages:
            current_candidates = stage.process(current_candidates, context)
        return current_candidates

    @classmethod
    def build_default_7_stage_pipeline(cls) -> 'RecommendationPipeline':
        pipeline = cls()
        pipeline.register(CandidateGenerationStage())
        pipeline.register(EligibilityStage())
        pipeline.register(BusinessRulesStage())
        pipeline.register(PopularityScoringStage())
        pipeline.register(SemanticSimilarityStage())
        pipeline.register(DiversityStage())
        pipeline.register(ExposureDeduplicationStage())
        return pipeline
