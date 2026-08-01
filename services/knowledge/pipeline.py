from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from services.repository.catalog_db import (
    CatalogRepository, KnowledgeFact, KnowledgeSnapshot, IntelligenceProfile, InferenceRun, OutboxEvent
)
from services.knowledge.extractor import KnowledgeExtractor
from services.knowledge.registry import InferenceEngineRegistry
from services.knowledge.engines.mood_engine import MoodEngine
from services.knowledge.engines.theme_engine import ThemeEngine
from services.knowledge.engines.narrative_engine import NarrativeEngine
from services.knowledge.engines.audience_engine import AudienceEngine
from services.knowledge.engines.franchise_engine import FranchiseEngine
from services.knowledge.materializer import ProfileMaterializer
from services.knowledge.dtos import KnowledgeFactDTO, IntelligenceProfileDTO

logger = logging.getLogger("streamora.knowledge.pipeline")

class KnowledgePipeline:
    """
    Master Knowledge & Intelligence Pipeline Orchestrator.
    Executes: Catalog Data -> Extraction -> Knowledge Store -> Inference Engines -> Snapshot -> Intelligence Profile Materializer -> Outbox Event.
    """

    def __init__(self, repo: CatalogRepository = None):
        self.repo = repo or CatalogRepository()
        self.extractor = KnowledgeExtractor()
        self.materializer = ProfileMaterializer()

        # Initialize and register default inference engines
        self.registry = InferenceEngineRegistry()
        self.registry.register(MoodEngine())
        self.registry.register(ThemeEngine())
        self.registry.register(NarrativeEngine())
        self.registry.register(AudienceEngine())
        self.registry.register(FranchiseEngine())

    async def process_content(self, content_id: int) -> IntelligenceProfileDTO:
        logger.info(f"Starting KIP Pipeline execution for content_id {content_id}")
        content_data = self.repo.get_by_id(content_id)
        if not content_data:
            raise ValueError(f"Content ID {content_id} not found in catalog database.")

        session = self.repo.get_session()
        try:
            # 1. Baseline Fact Extraction
            baseline_facts = self.extractor.extract_baseline_facts(content_id, content_data)

            # 2. Run Inference Engines via Registry
            inferred_facts, runs = await self.registry.run_all(content_id, content_data, baseline_facts)
            all_facts_dto = baseline_facts + inferred_facts

            # 3. Persist Atomic Facts to Database (Knowledge Store)
            for f in all_facts_dto:
                fact_record = KnowledgeFact(
                    content_id=f.content_id,
                    category=f.category,
                    predicate=f.predicate,
                    value=f.value,
                    confidence=f.confidence,
                    source_weight=f.source_weight,
                    state=f.state,
                    source_provider=f.source_provider,
                    inference_model=f.inference_model,
                    model_version=f.model_version
                )
                session.add(fact_record)

            # 4. Log Inference Runs
            for r in runs:
                run_record = InferenceRun(
                    content_id=r.content_id,
                    engine_name=r.engine_name,
                    model_name=r.model_name,
                    model_version=r.model_version,
                    execution_time_ms=r.execution_time_ms,
                    facts_produced=r.facts_produced
                )
                session.add(run_record)

            session.flush()

            # 5. Create Knowledge Snapshot
            k_hash = self.materializer.generate_snapshot_hash(all_facts_dto)
            snapshot = KnowledgeSnapshot(
                content_id=content_id,
                fact_count=len(all_facts_dto),
                knowledge_hash=k_hash
            )
            session.add(snapshot)
            session.flush()

            # 6. Materialize Intelligence Profile
            profile_dto = self.materializer.materialize(content_id, content_data, all_facts_dto)

            # Upsert IntelligenceProfile in database
            existing_profile = session.query(IntelligenceProfile).filter(IntelligenceProfile.content_id == content_id).first()
            if existing_profile:
                existing_profile.snapshot_id = snapshot.id
                existing_profile.profile_version = profile_dto.profile_version
                existing_profile.dominant_themes_json = json.dumps(profile_dto.dominant_themes)
                existing_profile.dominant_moods_json = json.dumps(profile_dto.dominant_moods)
                existing_profile.pacing = profile_dto.pacing
                existing_profile.narrative_structure = profile_dto.narrative_structure
                existing_profile.audience_rating = profile_dto.audience_rating
                existing_profile.content_warnings_json = json.dumps(profile_dto.content_warnings)
                existing_profile.summary_short = profile_dto.summary_short
                existing_profile.summary_medium = profile_dto.summary_medium
                existing_profile.summary_deep = profile_dto.summary_deep
                existing_profile.summary_spoiler_free = profile_dto.summary_spoiler_free
                existing_profile.overall_confidence = profile_dto.overall_confidence
                existing_profile.fact_count = profile_dto.fact_count
                existing_profile.generated_at = datetime.utcnow()
            else:
                db_profile = IntelligenceProfile(
                    content_id=content_id,
                    snapshot_id=snapshot.id,
                    profile_version=profile_dto.profile_version,
                    dominant_themes_json=json.dumps(profile_dto.dominant_themes),
                    dominant_moods_json=json.dumps(profile_dto.dominant_moods),
                    pacing=profile_dto.pacing,
                    narrative_structure=profile_dto.narrative_structure,
                    audience_rating=profile_dto.audience_rating,
                    content_warnings_json=json.dumps(profile_dto.content_warnings),
                    summary_short=profile_dto.summary_short,
                    summary_medium=profile_dto.summary_medium,
                    summary_deep=profile_dto.summary_deep,
                    summary_spoiler_free=profile_dto.summary_spoiler_free,
                    overall_confidence=profile_dto.overall_confidence,
                    fact_count=profile_dto.fact_count
                )
                session.add(db_profile)

            # 7. Emit Outbox Event for Downstream Services (Search, Recs, Hero)
            outbox_evt = OutboxEvent(
                aggregate_type="KnowledgeProfile",
                aggregate_id=str(content_id),
                event_type="knowledge.enriched",
                payload=json.dumps({
                    "content_id": content_id,
                    "snapshot_hash": k_hash,
                    "fact_count": len(all_facts_dto),
                    "confidence": profile_dto.overall_confidence
                })
            )
            session.add(outbox_evt)

            session.commit()
            logger.info(f"Successfully processed KIP Pipeline for content_id {content_id} ({len(all_facts_dto)} facts)")
            return profile_dto

        except Exception as e:
            session.rollback()
            logger.exception(f"KIP Pipeline failed for content_id {content_id}: {e}")
            raise e
        finally:
            session.close()
