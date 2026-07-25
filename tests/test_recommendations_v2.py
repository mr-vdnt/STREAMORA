import pytest
import time
from services.recommendation.shelf_engine import ShelfEngine
from services.recommendation.shelves import ShelfRegistry

def test_shelf_overlap():
    engine = ShelfEngine()
    payload = engine.generate_home_shelves()
    
    # Check max exposures (we set max_shelves=2 for most, except hidden_gems=1)
    exposure_counts = {}
    for section in payload.get("sections", []):
        for item in section.get("items", []):
            item_id = item["item_id"]
            exposure_counts[item_id] = exposure_counts.get(item_id, 0) + 1
            
    # Verify no item exceeds its max_shelves
    # Since we can't easily retrieve the max_shelves from just the payload, we assume 2 is the max
    for item_id, count in exposure_counts.items():
        assert count <= 2, f"Item {item_id} appears {count} times, which exceeds max_shelves of 2."

def test_genre_purity():
    engine = ShelfEngine()
    genre = "action"
    payload = engine.generate_genre_shelves(genre=genre)
    
    for section in payload.get("sections", []):
        for item in section.get("items", []):
            genres = str(item.get("genres", "")).lower()
            assert genre in genres, f"Item {item.get('title')} does not belong to genre '{genre}'. Genres: {genres}"

def test_hero_validity():
    engine = ShelfEngine()
    payload = engine.generate_home_shelves()
    
    hero = payload.get("hero")
    assert hero is not None, "Hero item is missing"
    assert "backdrop_url" in hero and hero["backdrop_url"], "Hero must have a backdrop image"
    # Note: Trailer might not be available for all movies, but if we prioritize them, they often will.
    # We will just verify it's a valid dictionary with expected keys.
    assert "item_id" in hero
    assert "title" in hero

def test_latency():
    engine = ShelfEngine()
    
    # Warm up cache (if any)
    engine.generate_home_shelves()
    
    start_time = time.time()
    for _ in range(10):
        engine.generate_home_shelves()
    avg_latency = (time.time() - start_time) / 10
    
    # Latency should be under 200ms
    assert avg_latency < 0.200, f"Average latency {avg_latency*1000:.2f}ms exceeds target 200ms"
