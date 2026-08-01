from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Tuple
from services.knowledge.contracts import BaseInferenceEngine
from services.knowledge.dtos import KnowledgeFactDTO, InferenceRunDTO

logger = logging.getLogger("streamora.knowledge.registry")

class InferenceEngineRegistry:
    """
    Registry for discovering, managing, and executing pluggable KIP inference engines.
    """

    def __init__(self):
        self._engines: Dict[str, BaseInferenceEngine] = {}

    def register(self, engine: BaseInferenceEngine) -> None:
        name = engine.engine_name
        self._engines[name] = engine
        logger.info(f"Registered KIP Inference Engine: '{name}' (v{engine.model_version})")

    def unregister(self, engine_name: str) -> None:
        if engine_name in self._engines:
            del self._engines[engine_name]
            logger.info(f"Unregistered KIP Inference Engine: '{engine_name}'")

    def list_engines(self) -> List[str]:
        return list(self._engines.keys())

    async def run_all(
        self, 
        content_id: int, 
        content_data: Dict[str, Any], 
        existing_facts: List[KnowledgeFactDTO]
    ) -> Tuple[List[KnowledgeFactDTO], List[InferenceRunDTO]]:
        new_facts: List[KnowledgeFactDTO] = []
        runs: List[InferenceRunDTO] = []

        all_facts = list(existing_facts)

        for name, engine in self._engines.items():
            start_time = time.time()
            try:
                produced = await engine.infer(content_id, content_data, all_facts)
                elapsed_ms = (time.time() - start_time) * 1000.0

                new_facts.extend(produced)
                all_facts.extend(produced)

                runs.append(InferenceRunDTO(
                    content_id=content_id,
                    engine_name=name,
                    model_name=name,
                    model_version=engine.model_version,
                    execution_time_ms=round(elapsed_ms, 2),
                    facts_produced=len(produced)
                ))
            except Exception as e:
                logger.exception(f"Inference engine '{name}' failed for content_id {content_id}: {e}")

        return new_facts, runs
