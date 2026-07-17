import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.agent.query_intelligence import QueryIntelligenceEngine
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
    engine = QueryIntelligenceEngine(db)
    
    print("=== STREAMORA DETERMINISTIC NLP TEST SUITE ===")
    
    test_cases = [
        # Intent & Basic Extraction
        {
            "query": "Can you suggest films in the style of Inception?",
            "expected_intent": "recommendation",
            "expected_reference": "Inception"
        },
        {
            "query": "I'd love a mind-bending thriller starring Leonardo DiCaprio.",
            "expected_intent": "search",
            "expected_actors": ["Leonardo Dicaprio"],
            "expected_genres": ["Thriller"],
            "expected_themes": ["mind-bending"]
        },
        {
            "query": "Christopher Nolan sci-fi movies after 2010",
            "expected_intent": "search",
            "expected_directors": ["Christopher Nolan"],
            "expected_genres": ["Science Fiction"],
            "expected_year_min": 2010
        },
        # Negative Filters
        {
            "query": "Comedy movies but not romance",
            "expected_genres": ["Comedy"],
            "expected_exclude_genres": ["Romance"]
        },
        # Temporal Filters
        {
            "query": "Action movies under 2 hours",
            "expected_genres": ["Action"],
            "expected_runtime_max": 120
        },
        # Follow-up Memory Context
        {
            "query": "Only recent ones",
            "context": {"directors": ["Christopher Nolan"]},
            "expected_directors": ["Christopher Nolan"],
            "expected_temporal": ["recent"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for idx, tc in enumerate(test_cases):
        print(f"\n--- Test Case {idx+1}: '{tc['query']}' ---")
        context = tc.get("context", None)
        result = engine.parse(tc["query"], context=context)
        
        errors = []
        
        # Verify Intent
        if "expected_intent" in tc and result["intent"] != tc["expected_intent"]:
            errors.append(f"Intent mismatch: Expected {tc['expected_intent']}, got {result['intent']}")
            
        # Verify Reference
        if "expected_reference" in tc and result["reference_title"] != tc["expected_reference"]:
             errors.append(f"Reference mismatch: Expected {tc['expected_reference']}, got {result['reference_title']}")
             
        # Verify Actors
        if "expected_actors" in tc and result["entities"]["actors"] != tc["expected_actors"]:
            errors.append(f"Actors mismatch: Expected {tc['expected_actors']}, got {result['entities']['actors']}")
            
        # Verify Directors
        if "expected_directors" in tc and result["entities"]["directors"] != tc["expected_directors"]:
            errors.append(f"Directors mismatch: Expected {tc['expected_directors']}, got {result['entities']['directors']}")
            
        # Verify Genres
        if "expected_genres" in tc:
            if set(tc["expected_genres"]) != set(result["entities"]["genres"]):
                errors.append(f"Genres mismatch: Expected {tc['expected_genres']}, got {result['entities']['genres']}")
                
        # Verify Themes
        if "expected_themes" in tc:
            if set(tc["expected_themes"]) != set(result["entities"]["themes"]):
                errors.append(f"Themes mismatch: Expected {tc['expected_themes']}, got {result['entities']['themes']}")
                
        # Verify Filters
        if "expected_year_min" in tc and result["filters"].get("year_min") != tc["expected_year_min"]:
            errors.append(f"Year Min mismatch: Expected {tc['expected_year_min']}, got {result['filters'].get('year_min')}")
            
        if "expected_runtime_max" in tc and result["filters"].get("runtime_max") != tc["expected_runtime_max"]:
            errors.append(f"Runtime Max mismatch: Expected {tc['expected_runtime_max']}, got {result['filters'].get('runtime_max')}")
            
        if "expected_exclude_genres" in tc and set(result["filters"].get("exclude_genres", [])) != set(tc["expected_exclude_genres"]):
            errors.append(f"Exclude Genres mismatch: Expected {tc['expected_exclude_genres']}, got {result['filters'].get('exclude_genres')}")
            
        if "expected_temporal" in tc and set(result["entities"]["temporal"]) != set(tc["expected_temporal"]):
             errors.append(f"Temporal mismatch: Expected {tc['expected_temporal']}, got {result['entities']['temporal']}")
             
        if not errors:
            print("PASS")
            passed += 1
        else:
            print("FAIL")
            for e in errors:
                print(f"  - {e}")
            print(f"DEBUG OUTPUT: {json.dumps(result, indent=2)}")
            failed += 1
            
    print(f"\nTest Summary: {passed} Passed, {failed} Failed")

if __name__ == "__main__":
    run_tests()
