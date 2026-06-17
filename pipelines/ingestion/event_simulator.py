"""
AURORA AI - Real-Time Event Simulator

Simulates thousands of user events (views, clicks, purchases) against
the event processing service to demonstrate the real-time pipeline.

Usage:
    python pipelines/ingestion/event_simulator.py [--events 500] [--users 50]
"""

import argparse
import random
import time
import requests
import pandas as pd

GENRES = [
    "Action", "Adventure", "Animation", "Childrens", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
    "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "War", "Western"
]

DEVICES = ["web", "mobile_ios", "mobile_android", "tablet", "smart_tv"]

EVENT_TYPES = ["view", "view", "view", "click", "click", "purchase"]  # weighted distribution


def simulate(base_url: str, num_events: int, num_users: int):
    print(f"Simulating {num_events} events for {num_users} users...")
    print(f"Target: {base_url}")

    # Try to load real movie IDs
    try:
        movies = pd.read_csv("data/raw/movies.csv")
        item_ids = movies['item_id'].tolist()
    except FileNotFoundError:
        item_ids = list(range(1, 1683))  # MovieLens 100k has 1682 items

    successes = 0
    failures = 0
    start = time.time()

    for i in range(num_events):
        event = {
            "user_id": random.randint(1, num_users),
            "item_id": random.choice(item_ids),
            "event_type": random.choice(EVENT_TYPES),
            "genre": random.choice(GENRES),
            "device": random.choice(DEVICES),
            "session_id": f"sess_{random.randint(1, num_users * 3)}",
        }

        try:
            resp = requests.post(f"{base_url}/events/ingest", json=event, timeout=2)
            if resp.status_code == 200:
                successes += 1
            else:
                failures += 1
        except requests.RequestException:
            failures += 1

        # Print progress every 100 events
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  [{i+1}/{num_events}] {rate:.0f} events/sec | ok={successes} err={failures}")

    elapsed = time.time() - start
    print(f"\nDone! {successes}/{num_events} events ingested in {elapsed:.1f}s ({successes/elapsed:.0f} events/sec)")

    # Show final stats
    try:
        stats = requests.get(f"{base_url}/stats", timeout=2).json()
        print(f"\nSystem Stats:")
        print(f"  Events published: {stats['event_bus']['total_published']}")
        print(f"  Events processed: {stats['stream_processor']['total_processed']}")
        print(f"  User profiles:    {stats['feature_store']['total_user_profiles']}")
    except Exception:
        pass

    # Show a sample user profile
    sample_user = random.randint(1, num_users)
    try:
        profile = requests.get(f"{base_url}/features/user/{sample_user}", timeout=2).json()
        print(f"\nSample User Profile (user_id={sample_user}):")
        print(f"  Total events:  {profile.get('total_events', 0)}")
        print(f"  Event counts:  {profile.get('event_counts', {})}")
        print(f"  Top genres:    {profile.get('top_genres', [])}")
        print(f"  Recent items:  {profile.get('recent_items', [])[:5]}")
        print(f"  Last event:    {profile.get('last_event_type', '')}")
        print(f"  Device:        {profile.get('device', '')}")
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURORA AI Event Simulator")
    parser.add_argument("--url", default="http://127.0.0.1:8002", help="Event service URL")
    parser.add_argument("--events", type=int, default=500, help="Number of events to simulate")
    parser.add_argument("--users", type=int, default=50, help="Number of unique users")
    args = parser.parse_args()

    simulate(args.url, args.events, args.users)
