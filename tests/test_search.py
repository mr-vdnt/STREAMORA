import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    engine = DeterministicSearchEngine(db)
    
    print("=== STREAMORA DETERMINISTIC SEARCH ENGINE TEST SUITE ===")
    
    tests = {
        "Exact Matches": ["Interstellar", "Inception", "The Boys", "Breaking Bad"],
        "Typo Handling": ["Intersteller", "Incepton", "Dark Knigth"],
        "Alias Resolution": ["LOTR", "Infinity War", "Avengers 1"],
        "Actor Searches": ["Tom Hanks", "Leonardo DiCaprio", "Adam Sandler"],
        "Director Searches": ["Christopher Nolan", "Quentin Tarantino"],
        "Genre Searches": ["Sci-Fi", "Psychological Thriller", "Comedy"],
        "Negative Cases": ["asdasdasdasd", "", "Nonexistent Title xyz"]
    }
    
    passed = 0
    failed = 0
    
    for category, queries in tests.items():
        print(f"\n--- {category} ---")
        for q in queries:
            results = engine.search(q, limit=5)
            if category == "Negative Cases":
                if len(results) == 0:
                    print(f"PASS: '{q}' -> 0 results")
                    passed += 1
                else:
                    print(f"FAIL: '{q}' -> found {len(results)} results")
                    failed += 1
            else:
                if len(results) > 0:
                    top_title = results[0]['title']
                    score = results[0]['score']
                    match_type = results[0]['match_type']
                    print(f"PASS: '{q}' -> {top_title} ({match_type}, score: {score})")
                    passed += 1
                else:
                    print(f"FAIL: '{q}' -> No results found!")
                    failed += 1
                    
    print(f"\nTest Summary: {passed} Passed, {failed} Failed")
    
if __name__ == "__main__":
    run_tests()
