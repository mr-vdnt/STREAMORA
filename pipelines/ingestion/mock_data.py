import pandas as pd
import json
import os

def generate_mock_movies():
    movies = [
        {"id": 1, "title": "The Quantum Paradox", "genre": "Sci-Fi", "description": "A brilliant physicist discovers a way to alter past decisions, but each change fractures reality."},
        {"id": 2, "title": "Neon Horizons", "genre": "Sci-Fi/Action", "description": "In a cyberpunk future, a rogue AI hunter teams up with her target to stop a corporate conspiracy."},
        {"id": 3, "title": "Whispers of the Old Gods", "genre": "Horror/Fantasy", "description": "An expedition to Antarctica uncovers ancient ruins and awakens entities that feed on human fears."},
        {"id": 4, "title": "The Last Barista", "genre": "Comedy/Drama", "description": "In a world where coffee is outlawed, one man runs an underground speakeasy serving espresso."},
        {"id": 5, "title": "Midnight in Neo-Tokyo", "genre": "Thriller", "description": "A detective must solve a series of murders where the victims' memories have been entirely erased."},
        {"id": 6, "title": "Galactic Pioneers", "genre": "Sci-Fi", "description": "The crew of humanity's first interstellar ship must survive sabotage while crossing the void."},
        {"id": 7, "title": "Heartstrings", "genre": "Romance", "description": "Two rival musicians find themselves reluctantly collaborating, only to compose a masterpiece together."},
        {"id": 8, "title": "The Silent King", "genre": "Fantasy", "description": "A mute prince must reclaim his throne from his tyrannical uncle using ancient magic."},
        {"id": 9, "title": "Operation: Firewall", "genre": "Action", "description": "An elite hacker squad is recruited by the government to stop a cyber-terrorist from crashing the global economy."},
        {"id": 10, "title": "Echoes of Eternity", "genre": "Drama", "description": "An immortal reflects on the rise and fall of civilizations while searching for the only person they ever loved."}
    ]
    df = pd.DataFrame(movies)
    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/movies.csv", index=False)
    print("Mock movies generated and saved to data/raw/movies.csv")
    return df

def generate_mock_users():
    users = [
        {"id": 101, "age": 25, "preferences": "Sci-Fi, Action, Thriller"},
        {"id": 102, "age": 34, "preferences": "Romance, Drama, Comedy"},
        {"id": 103, "age": 19, "preferences": "Horror, Fantasy"},
        {"id": 104, "age": 42, "preferences": "Sci-Fi, Documentary"},
        {"id": 105, "age": 28, "preferences": "Action, Thriller"}
    ]
    df = pd.DataFrame(users)
    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/users.csv", index=False)
    print("Mock users generated and saved to data/raw/users.csv")
    return df

if __name__ == "__main__":
    generate_mock_movies()
    generate_mock_users()
