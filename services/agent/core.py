import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.agent.tools import get_explanation
import ollama

from services.repository.movie_repository import MovieRepository

repo = MovieRepository()
movies_db = repo.get_all()

def _get_movie_metadata(row):
    title = row.get('title', 'Unknown')
    
    # Extract year if present in title (e.g. 'Inception (2010)')
    year = ""
    if '(' in title:
        year = title.split('(')[-1].strip(')')
        
    # Rating logic
    try:
        rating = float(row.get('rating', 8.0))
    except ValueError:
        rating = 8.0
        
    is_adult = str(row.get('is_adult', 'False')).lower() == 'true'
    
    return {
        "title": title,
        "year": year,
        "match_percentage": int(rating * 10),
        "runtime": f"{row.get('runtime', 120)} min",
        "audience_type": "Adult" if is_adult else "Family/General",
        "tags": str(row.get('genres', '')).split('|'),
        "story_summary": row.get('overview', 'No summary available.'),
        "why_recommended": "Recommended by Streamora AI",
        "director": row.get('director', 'Unknown'),
        "tmdb_id": int(float(row.get('tmdb_id', 0))) if row.get('tmdb_id') else 0,
        "trailer_url": row.get('trailer_url', '')
    }

class ExtractionSchema(BaseModel):
    intent: str
    target_genres: List[str]
    target_moods: List[str]
    target_actors: List[str]
    target_director: str
    target_content_type: str

class OrchestratorAgent:
    def __init__(self):
        print("Loading Query Intelligence Engine...")
        self.conversation_memory = {}
        self.model = 'llama3'
        from services.agent.query_intelligence import QueryIntelligenceEngine
        self.query_engine = QueryIntelligenceEngine(movies_db)

    def process_query(self, user_id: int, query: str, exclude_ids: list[int] = None) -> dict:
        if exclude_ids is None:
            exclude_ids = []
            
        lower_q = query.lower()
        if "why" in lower_q or "explain" in lower_q:
            match = re.search(r'\b\d+\b', query)
            item_id = int(match.group(0)) if match else 1
            tool_resp = get_explanation(user_id, item_id)
            return {
                "query": query,
                "intent": "explanation",
                "response": [],
                "llm_response": tool_resp["data"]["explanation"] if tool_resp["status"] == "success" else "High relevance based on semantic matching.",
                "entities": {}
            }

        # Use Deterministic NLP Pipeline (No LLM)
        context = self.conversation_memory.get(user_id, {}).get("last_entities", {})
        query_plan = self.query_engine.parse(query, context=context)
        
        # Save session context
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = {}
        self.conversation_memory[user_id]["last_entities"] = query_plan["entities"]
        
        # If it's pure chat, bypass search engine completely
        if query_plan["intent"] == "chat":
            try:
                resp = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': query}])
                llm_text = resp['message']['content']
            except:
                llm_text = "I'm your AI movie curator! Ask me for recommendations."
            return {
                "query": query,
                "intent": "chat",
                "response": [],
                "llm_response": llm_text,
                "entities": query_plan["entities"]
            }
        
        # PHASE 4: HYBRID CANDIDATE GENERATION ENGINE
        response_data = []
        try:
            from services.retrieval.hybrid_engine import HybridRetrievalEngine
            from services.retrieval.registry import GeneratorRegistry
            from services.retrieval.generators.exact import ExactSearchGenerator
            from services.retrieval.generators.semantic import SemanticGenerator
            from services.retrieval.generators.metadata import MetadataGenerator
            from services.retrieval.generators.personalization import PersonalizationGenerator
            from services.retrieval.generators.knowledge_graph import KnowledgeGraphGenerator
            from services.catalog.search import DeterministicSearchEngine
            from services.catalog.ingestion import ingest_from_tmdb
            from services.user_intelligence.adapter import PersonalizationAdapter
            from services.content_intelligence.adapter import ContentIntelligenceAdapter
            
            # Use global profile_store to maintain state between requests
            global profile_store
            if 'profile_store' not in globals():
                from services.user_intelligence.storage import InMemoryProfileStore
                profile_store = InMemoryProfileStore()
            
            # Setup Adapters
            user_adapter = PersonalizationAdapter(store=profile_store)
            content_adapter = ContentIntelligenceAdapter(movies_db)
            
            # Setup Registry
            registry = GeneratorRegistry()
            exact_engine = DeterministicSearchEngine(movies_db)
            registry.register(ExactSearchGenerator(exact_engine))
            registry.register(SemanticGenerator("data/index/movies.index"))
            registry.register(MetadataGenerator(movies_db))
            registry.register(PersonalizationGenerator(movies_db, user_adapter))
            registry.register(KnowledgeGraphGenerator(movies_db, content_adapter))
            
            # Execute Hybrid Retrieval
            hybrid_engine = HybridRetrievalEngine(registry, movies_db)
            retrieval_output = hybrid_engine.generate_candidates(query_plan)
            
            # If nothing found locally, blast TMDB live INGESTION!
            if not retrieval_output["candidates"]:
                print("Missing locally, triggering TMDB Ingestion...")
                new_iid = ingest_from_tmdb(query)
                if new_iid:
                    print(f"Ingested ID {new_iid}. Re-running search.")
                    retrieval_output = hybrid_engine.generate_candidates(query_plan)
            
            # PHASE 5: DECISION ENGINE & RECOMMENDATION RANKING
            from services.ranking.decision_engine import DecisionEngine
            decision_engine = DecisionEngine(movies_db, user_adapter, content_adapter)
            recommendation_package = decision_engine.process(retrieval_output)
            
            # PHASE 6: CONVERSATIONAL PRESENTATION LAYER
            from services.presentation.engine import PresentationEngine
            presentation_engine = PresentationEngine(movies_db, user_adapter, content_adapter)
            intent = query_plan.get("entities", {}).get("intent", "search")
            
            final_response = presentation_engine.present(query, intent, recommendation_package, user_id="anonymous", query_contract=query_plan)
            final_response["entities"] = query_plan.get("entities", {})
            return final_response
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Pipeline Failed: {e}")
            return {
                "query": query,
                "intent": "search",
                "response": [],
                "llm_response": "I encountered an error trying to process that request.",
                "entities": query_plan.get("entities", {})
            }

agent = OrchestratorAgent()
