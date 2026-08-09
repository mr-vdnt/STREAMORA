"""Streamora orchestration core with lazy initialization.

The previous implementation loaded the entire catalog during module import. That made
Render unable to bind the HTTP port because application startup was coupled to a large
SQLite read and several recommendation dependencies. This module keeps imports cheap
and initializes the recommendation stack only when a request actually needs it.
"""
from __future__ import annotations

import json
import re
import time
from threading import Lock
from typing import Any, Iterator

try:
    import ollama
except ImportError:  # pragma: no cover - optional dependency
    ollama = None


class OrchestratorAgent:
    """Lazy, request-safe orchestration facade used by the HTTP layer."""

    def __init__(self) -> None:
        self._query_engine = None
        self._profile_store = None
        self._movies_db = None
        self._lock = Lock()
        self.conversation_memory: dict[int, dict[str, Any]] = {}
        self.model = "llama3.2"

    @property
    def movies_db(self) -> dict[int, dict[str, Any]]:
        if self._movies_db is None:
            with self._lock:
                if self._movies_db is None:
                    from services.repository.movie_repository import MovieRepository
                    self._movies_db = MovieRepository().get_all()
        return self._movies_db

    @property
    def query_engine(self):
        if self._query_engine is None:
            with self._lock:
                if self._query_engine is None:
                    from services.agent.query_intelligence import QueryIntelligenceEngine
                    self._query_engine = QueryIntelligenceEngine(self.movies_db)
        return self._query_engine

    @property
    def profile_store(self):
        if self._profile_store is None:
            with self._lock:
                if self._profile_store is None:
                    from services.user_intelligence.storage import InMemoryProfileStore
                    self._profile_store = InMemoryProfileStore()
        return self._profile_store

    def _plan(self, user_id: int, query: str) -> dict[str, Any]:
        context = self.conversation_memory.get(user_id, {}).get("last_entities", {})
        plan = self.query_engine.parse(query, context=context)
        self.conversation_memory.setdefault(user_id, {})["last_entities"] = plan.get("entities", {})
        return plan

    def _chat_fallback(self, query: str) -> str:
        if ollama is None:
            return "I'm your AI movie curator. Ask me for a movie or series recommendation."
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": query}],
                keep_alive="1h",
            )
            return response.get("message", {}).get("content", "")
        except Exception:
            return "I'm your AI movie curator. Ask me for a movie or series recommendation."

    def _recommend(self, user_id: int, query_plan: dict[str, Any]) -> dict[str, Any]:
        from services.retrieval.hybrid_engine import HybridRetrievalEngine
        from services.retrieval.registry import GeneratorRegistry
        from services.retrieval.generators.exact import ExactSearchGenerator
        from services.retrieval.generators.semantic import SemanticGenerator
        from services.retrieval.generators.metadata import MetadataGenerator
        from services.retrieval.generators.personalization import PersonalizationGenerator
        from services.retrieval.generators.knowledge_graph import KnowledgeGraphGenerator
        from services.catalog.search import DeterministicSearchEngine
        from services.user_intelligence.adapter import PersonalizationAdapter
        from services.content_intelligence.adapter import ContentIntelligenceAdapter
        from services.ranking.decision_engine import DecisionEngine
        from services.presentation.engine import PresentationEngine

        movies = self.movies_db
        user_adapter = PersonalizationAdapter(store=self.profile_store)
        content_adapter = ContentIntelligenceAdapter(movies)
        registry = GeneratorRegistry()
        registry.register(ExactSearchGenerator(DeterministicSearchEngine(movies)))
        index_path = "data/index/movies.index"
        registry.register(SemanticGenerator(index_path))
        registry.register(MetadataGenerator(movies))
        registry.register(PersonalizationGenerator(movies, user_adapter))
        registry.register(KnowledgeGraphGenerator(movies, content_adapter))

        retrieval = HybridRetrievalEngine(registry, movies).generate_candidates(query_plan)
        package = DecisionEngine(movies, user_adapter, content_adapter).process(retrieval)
        intent = query_plan.get("entities", {}).get("intent", "search")
        return PresentationEngine(movies, user_adapter, content_adapter).present(
            query_plan.get("query", ""),
            intent,
            package,
            user_id=user_id,
            query_contract=query_plan,
        )

    def process_query(
        self,
        user_id: int,
        query: str,
        exclude_ids: list[int] | None = None,
        req_id: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        exclude_ids = exclude_ids or []
        plan = self._plan(user_id, query)

        if plan.get("intent") == "chat":
            return {
                "query": query,
                "intent": "chat",
                "response": [],
                "llm_response": self._chat_fallback(query),
                "entities": plan.get("entities", {}),
                "metrics": {"total_ms": int((time.perf_counter() - started) * 1000)},
            }

        try:
            result = self._recommend(user_id, plan)
            result.setdefault("query", query)
            result.setdefault("intent", plan.get("intent", "search"))
            result.setdefault("response", [])
            result.setdefault("llm_response", "")
            result.setdefault("entities", plan.get("entities", {}))
            metrics = result.setdefault("metrics", {})
            metrics["total_ms"] = int((time.perf_counter() - started) * 1000)
            return result
        except Exception as exc:
            print(f"[Orchestrator] recommendation pipeline failed: {exc}")
            return {
                "query": query,
                "intent": "search",
                "response": [],
                "llm_response": "I couldn't complete that recommendation request right now.",
                "entities": plan.get("entities", {}),
                "metrics": {"total_ms": int((time.perf_counter() - started) * 1000)},
            }

    def process_query_stream(
        self,
        user_id: int,
        query: str,
        exclude_ids: list[int] | None = None,
        req_id: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Stream a recommendation response without performing startup work."""
        try:
            plan = self._plan(user_id, query)
            if plan.get("intent") == "chat":
                yield {"type": "data", "value": json.dumps({
                    "intent": "chat", "response": [], "entities": plan.get("entities", {})
                })}
                yield {"type": "token", "value": self._chat_fallback(query)}
                return

            result = self.process_query(user_id, query, exclude_ids, req_id)
            yield {"type": "data", "value": json.dumps({
                "intent": result.get("intent", "search"),
                "response": result.get("response", []),
                "entities": result.get("entities", {}),
            })}
            if result.get("llm_response"):
                yield {"type": "token", "value": result["llm_response"]}
        except Exception as exc:
            print(f"[Orchestrator] stream failed: {exc}")
            yield {"type": "token", "value": "I couldn't complete that request right now."}


# Cheap module-level facade. No database, FAISS, transformer, or LLM is loaded here.
agent = OrchestratorAgent()
