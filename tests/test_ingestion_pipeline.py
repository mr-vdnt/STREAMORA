import unittest
import os
import pandas as pd
import faiss
import json

class TestIngestionPipeline(unittest.TestCase):
    def test_movies_database_scale(self):
        movies_path = "data/raw/movies.csv"
        self.assertTrue(os.path.exists(movies_path), "movies.csv should exist")
        df = pd.read_csv(movies_path)
        
        self.assertGreaterEqual(len(df), 50, "Catalog should be scaled to at least 50 items")
        self.assertEqual(df['item_id'].min(), 1, "item_id should start at 1")
        self.assertEqual(df['item_id'].max(), len(df), "item_id should be contiguous and end at len(df)")

    def test_poster_url_validity(self):
        movies_path = "data/raw/movies.csv"
        df = pd.read_csv(movies_path)
        
        for idx, row in df.iterrows():
            poster = str(row['poster_url'])
            backdrop = str(row['backdrop_url'])
            title = row['title']
            
            # Assert they point to official TMDB CDN
            self.assertTrue(poster.startswith("https://image.tmdb.org/t/p/"), f"Poster for {title} must point to TMDB CDN")
            self.assertTrue(backdrop.startswith("https://image.tmdb.org/t/p/"), f"Backdrop for {title} must point to TMDB CDN")

    def test_faiss_index_integrity(self):
        index_path = "data/index/semantic_items.index"
        self.assertTrue(os.path.exists(index_path), "FAISS semantic index should exist")
        
        faiss_index = faiss.read_index(index_path)
        movies_df = pd.read_csv("data/raw/movies.csv")
        
        self.assertEqual(faiss_index.ntotal, len(movies_df), "FAISS index size must match movies database size")

    def test_knowledge_graph_alignment(self):
        movies_df = pd.read_csv("data/raw/movies.csv")
        actors_df = pd.read_csv("data/graph/actors.csv")
        directors_df = pd.read_csv("data/graph/directors.csv")
        ma_df = pd.read_csv("data/graph/movie_actors.csv")
        md_df = pd.read_csv("data/graph/movie_directors.csv")
        
        self.assertFalse(actors_df.empty, "Actors table should not be empty")
        self.assertFalse(directors_df.empty, "Directors table should not be empty")
        
        # Verify foreign keys in movie_actors and movie_directors point to valid IDs
        valid_movie_ids = set(movies_df['item_id'])
        valid_actor_ids = set(actors_df['actor_id'])
        valid_director_ids = set(directors_df['director_id'])
        
        for idx, row in ma_df.iterrows():
            self.assertIn(row['movie_id'], valid_movie_ids, f"movie_actors entry at index {idx} has invalid movie_id")
            self.assertIn(row['actor_id'], valid_actor_ids, f"movie_actors entry at index {idx} has invalid actor_id")
            
        for idx, row in md_df.iterrows():
            self.assertIn(row['movie_id'], valid_movie_ids, f"movie_directors entry at index {idx} has invalid movie_id")
            self.assertIn(row['director_id'], valid_director_ids, f"movie_directors entry at index {idx} has invalid director_id")

    def test_multimodal_embeddings_alignment(self):
        movies_df = pd.read_csv("data/raw/movies.csv")
        embeddings_path = "data/multimodal/visual_embeddings.json"
        self.assertTrue(os.path.exists(embeddings_path), "multimodal visual embeddings JSON should exist")
        
        count = 0
        with open(embeddings_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    self.assertIn("item_id", obj)
                    self.assertIn("visual_embedding", obj)
                    self.assertEqual(len(obj["visual_embedding"]), 64, "Visual embedding vector should have length 64")
                    count += 1
                    
        self.assertEqual(count, len(movies_df), "Number of visual embeddings should match catalog length")

if __name__ == "__main__":
    unittest.main()
