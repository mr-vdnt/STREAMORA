"""
AURORA AI - Data Enrichment for Knowledge Graph

Simulates Directors, Actors, and Tags for movies in the MovieLens dataset
to create rich connections for Graph Intelligence.
"""

import os
import sys
import random
import pandas as pd
from faker import Faker

faker = Faker()
Faker.seed(42)
random.seed(42)

def enrich_data():
    movies_path = "data/raw/movies.csv"
    if not os.path.exists(movies_path):
        print(f"Error: {movies_path} not found. Run movielens.py first.")
        sys.exit(1)

    movies_df = pd.read_csv(movies_path)
    
    # Generate mock actors (pool of 500)
    print("Generating mock actors...")
    actor_pool = [{"actor_id": i, "name": faker.name()} for i in range(1, 501)]
    actors_df = pd.DataFrame(actor_pool)
    
    # Generate mock directors (pool of 200)
    print("Generating mock directors...")
    director_pool = [{"director_id": i, "name": faker.name()} for i in range(1, 201)]
    directors_df = pd.DataFrame(director_pool)
    
    # Create relationships
    print("Creating graph relationships...")
    
    movie_actor_edges = []
    movie_director_edges = []
    
    for _, movie in movies_df.iterrows():
        movie_id = movie['item_id']
        
        # 1-3 directors per movie
        num_dirs = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
        dirs = random.sample(director_pool, num_dirs)
        for d in dirs:
            movie_director_edges.append({
                "movie_id": movie_id,
                "director_id": d["director_id"]
            })
            
        # 3-8 actors per movie
        num_acts = random.randint(3, 8)
        acts = random.sample(actor_pool, num_acts)
        for a in acts:
            movie_actor_edges.append({
                "movie_id": movie_id,
                "actor_id": a["actor_id"],
                "role": faker.job() # using job as a funny mock role
            })

    ma_df = pd.DataFrame(movie_actor_edges)
    md_df = pd.DataFrame(movie_director_edges)
    
    # Save enriched data
    os.makedirs("data/graph", exist_ok=True)
    actors_df.to_csv("data/graph/actors.csv", index=False)
    directors_df.to_csv("data/graph/directors.csv", index=False)
    ma_df.to_csv("data/graph/movie_actors.csv", index=False)
    md_df.to_csv("data/graph/movie_directors.csv", index=False)
    
    print(f"Graph enrichment complete! Generated {len(actors_df)} actors, {len(directors_df)} directors.")
    print(f"Created {len(ma_df)} ACTS_IN edges and {len(md_df)} DIRECTED edges.")

if __name__ == "__main__":
    enrich_data()
