import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.discovery.home_service import HomeService
from services.repository.catalog_db import CatalogRepository

def run_test():
    print("Initializing HomeService (and ShelfEngine)...")
    service = HomeService()
    
    print("Testing get_home_payload...")
    home_payload = service.get_home_payload(format="all", user_id=123)
    
    sections = home_payload.get("sections", [])
    print(f"Generated {len(sections)} home sections.")
    
    # Check for duplicates across sections
    seen_ids = set()
    duplicates = 0
    
    for section in sections:
        items = section.get("items", [])
        for item in items:
            iid = item.get("id")
            if iid in seen_ids:
                duplicates += 1
            seen_ids.add(iid)
            
    print(f"Found {duplicates} duplicate items across home sections.")
    assert duplicates == 0, "Duplicate items found across home shelves! Exposure policy failed."
    
    hero = home_payload.get("hero")
    print(f"Selected Contextual Hero: {hero.get('title') if hero else 'None'}")
    assert hero is not None, "Hero was not selected."
    
    print("Testing get_genre_payload('comedy')...")
    genre_payload = service.get_genre_payload(genre="comedy", user_id=123)
    g_sections = genre_payload.get("sections", [])
    print(f"Generated {len(g_sections)} genre sections.")
    
    g_hero = genre_payload.get("hero")
    print(f"Selected Contextual Genre Hero: {g_hero.get('title') if g_hero else 'None'}")
    
    print("All recommendation pipeline tests passed!")

if __name__ == "__main__":
    run_test()
