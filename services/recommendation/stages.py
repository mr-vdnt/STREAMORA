from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import random

class PipelineStage(ABC):
    """Abstract interface for a recommendation pipeline stage."""
    
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process and transform candidates or scores."""
        pass


class CandidateGenerationStage(PipelineStage):
    """Stage 1: Dedicated Candidate Generation via Specification + QueryBuilder"""
    def name(self) -> str:
        return "CandidateGenerationStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        query_builder = context.get("query_builder")
        spec = context.get("specification")
        limit = context.get("candidate_limit", 150)
        
        if query_builder and spec:
            return query_builder.with_specification(spec).order_by_popularity(descending=True).execute(limit=limit)
        return candidates


class EligibilityStage(PipelineStage):
    """Stage 2: Eligibility Filtering (valid titles, posters, availability)"""
    def name(self) -> str:
        return "EligibilityStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        eligible = []
        for item in candidates:
            title = item.get("title", "")
            poster = item.get("poster_url", "")
            if title and poster:
                eligible.append(item)
        return eligible


class BusinessRulesStage(PipelineStage):
    """Stage 3: Business Constraints & Format Overrides"""
    def name(self) -> str:
        return "BusinessRulesStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_format = context.get("target_format", "all")
        if target_format == "movie":
            return [c for c in candidates if c.get("entity_type") == "movie"]
        elif target_format == "series":
            return [c for c in candidates if c.get("entity_type") == "tvseries"]
        return candidates


class PopularityScoringStage(PipelineStage):
    """Stage 4: Popularity & Quality Score Assignment"""
    def name(self) -> str:
        return "PopularityScoringStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        for item in candidates:
            pop = float(item.get("popularity", 0.0) or 0.0)
            rating = float(item.get("rating", 0.0) or 0.0)
            item["pipeline_score"] = (pop * 0.6) + (rating * 4.0)
        
        # Sort by computed score
        return sorted(candidates, key=lambda x: x.get("pipeline_score", 0.0), reverse=True)


class SemanticSimilarityStage(PipelineStage):
    """Stage 5: Semantic Match & Vector Ranking (Optional)"""
    def name(self) -> str:
        return "SemanticSimilarityStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        user_vector = context.get("user_vector")
        if not user_vector:
            return candidates
            
        # If user vector is present, boost candidates with genre match
        user_genres = set(context.get("preferred_genres", []))
        if user_genres:
            for item in candidates:
                item_genres = set(str(item.get("genres", "")).split("|"))
                overlap = len(user_genres.intersection(item_genres))
                item["pipeline_score"] = item.get("pipeline_score", 0.0) + (overlap * 5.0)
                
            return sorted(candidates, key=lambda x: x.get("pipeline_score", 0.0), reverse=True)
        return candidates


class DiversityStage(PipelineStage):
    """Stage 6: Genre Entropy & Intra-shelf Diversity Capping"""
    def name(self) -> str:
        return "DiversityStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        max_per_genre = context.get("max_per_genre", 3)
        genre_counts: Dict[str, int] = {}
        diversified = []

        for item in candidates:
            primary_genre = str(item.get("genres", "Other")).split("|")[0]
            count = genre_counts.get(primary_genre, 0)
            if count < max_per_genre:
                genre_counts[primary_genre] = count + 1
                diversified.append(item)
                
        # If capping trimmed too much, backfill
        if len(diversified) < context.get("output_limit", 15):
            seen_ids = {x["id"] for x in diversified}
            for item in candidates:
                if item["id"] not in seen_ids:
                    diversified.append(item)
                    seen_ids.add(item["id"])
                    if len(diversified) >= context.get("output_limit", 15):
                        break
                        
        return diversified


class ExposureDeduplicationStage(PipelineStage):
    """Stage 7: Inter-shelf Global Deduplication & Final Exposure Tracking"""
    def name(self) -> str:
        return "ExposureDeduplicationStage"

    def process(self, candidates: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        exposure_tracker = context.get("exposure_tracker")
        output_limit = context.get("output_limit", 15)
        
        if not exposure_tracker:
            return candidates[:output_limit]

        deduped = []
        for item in candidates:
            item_id = item.get("id")
            if item_id and exposure_tracker.can_show(item_id):
                deduped.append(item)
                exposure_tracker.record_exposure(item_id)
                if len(deduped) >= output_limit:
                    break
                    
        return deduped
