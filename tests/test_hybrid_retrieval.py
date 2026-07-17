import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.retrieval.registry import GeneratorRegistry
from services.retrieval.generators.exact import ExactSearchGenerator
from services.retrieval.generators.semantic import SemanticGenerator
from services.retrieval.generators.metadata import MetadataGenerator
from services.retrieval.hybrid_engine import HybridRetrievalEngine
from services.catalog.search import DeterministicSearchEngine
import csv

def load_movies():
    movies_db = {}
    if os.path.exists("data/raw/movies.csv"):
        with open("data/raw/movies.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    iid = int(row.get('item_id', 0))
                    movies_db[iid] = row
                except ValueError:
                    pass
    return movies_db

def run_tests():
    db = load_movies()
    registry = GeneratorRegistry()
    exact_engine = DeterministicSearchEngine(db)
    registry.register(ExactSearchGenerator(exact_engine))
    registry.register(SemanticGenerator("data/index/movies.index"))
    registry.register(MetadataGenerator(db))
    
    hybrid = HybridRetrievalEngine(registry, db)
    
    print("=== STREAMORA HYBRID RETRIEVAL TEST SUITE ===")
    
    test_cases = [
        # Deterministic / Actor focus
        {
            "query_contract": {
                "schema_version": "1.0",
                "fingerprint": "SEARCH_ACT_GEN",
                "entities": {
                    "actors": ["Leonardo Dicaprio"],
                    "directors": [],
                    "genres": ["Science Fiction"],
                    "themes": [],
                    "temporal": []
                },
                "filters": {}
            },
            "desc": "Actor + Genre Search"
        },
        # Semantic / Vague thematic focus
        {
            "query_contract": {
                "schema_version": "1.0",
                "fingerprint": "REC_THEME",
                "entities": {
                    "actors": [],
                    "directors": [],
                    "genres": [],
                    "themes": ["mind-bending", "psychological"],
                    "temporal": []
                },
                "filters": {}
            },
            "desc": "Thematic Semantic Search"
        },
        # Hybrid Fusion / Reference + Year filter
        {
            "query_contract": {
                "schema_version": "1.0",
                "fingerprint": "REC_REF_YEAR",
                "reference_title": "Inception",
                "entities": {
                    "actors": [],
                    "directors": [],
                    "genres": [],
                    "themes": [],
                    "temporal": []
                },
                "filters": {
                    "year_min": 2012
                }
            },
            "desc": "Reference + Filter"
        }
    ]
    
    for idx, tc in enumerate(test_cases):
        print(f"\n--- Test Case {idx+1}: {tc['desc']} ---")
        result = hybrid.generate_candidates(tc["query_contract"])
        
        print(f"Fingerprint: {result['query_fingerprint']}")
        print(f"Latency: {result['retrieval_metadata']['retrieval_time_ms']}ms")
        for diag in result['diagnostics']:
            print(f"  Generator: {diag['generator']} | Latency: {diag['latency_ms']}ms | Candidates: {diag['candidate_count']}")
            
        print("Top 3 Candidates:")
        for c in result['candidates'][:3]:
            title = db[c['content_id']]['title']
            gens = ", ".join([g['name'] for g in c['retrieval']['generators']])
            score = c['retrieval']['fusion_score']
            print(f"  - {title} (ID: {c['content_id']}) | Score: {score:.3f} | Found via: {gens}")

if __name__ == "__main__":
    run_tests()
