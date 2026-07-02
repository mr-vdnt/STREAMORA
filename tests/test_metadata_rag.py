import unittest
import pandas as pd
import os
from services.rag.llm import llm_provider

class TestRAGMetadata(unittest.TestCase):
    def test_complete_metadata_fields(self):
        # Verify that movies.csv exists and is loaded
        df = llm_provider.movies_df
        self.assertFalse(df.empty, "movies.csv should not be empty")
        self.assertGreaterEqual(len(df), 50, "Should contain at least 50 items")
        
        # Test a movie item (ID 1)
        movie_row = df[df['item_id'] == 1].iloc[0]
        movie_meta = llm_provider.generate_rich_metadata(1, movie_row['title'], "test explanation")
        self.assertEqual(movie_meta["director"], movie_row['director'])
        
        expected_runtime_1 = f"{movie_row['runtime']} min" if str(movie_row['runtime']).isdigit() else str(movie_row['runtime'])
        self.assertEqual(movie_meta["runtime"], expected_runtime_1)
        
        # Test a TV show item dynamically
        tv_matches = df[df['content_type'] == 'series']
        self.assertFalse(tv_matches.empty, "Should contain TV series items")
        tv_row = tv_matches.iloc[0]
        tv_id = int(tv_row['item_id'])
        tv_meta = llm_provider.generate_rich_metadata(tv_id, tv_row['title'], "test explanation")
        self.assertEqual(tv_meta["director"], tv_row['director'])
        
        expected_runtime_tv = f"{tv_row['runtime']} min" if str(tv_row['runtime']).isdigit() else str(tv_row['runtime'])
        self.assertEqual(tv_meta["runtime"], expected_runtime_tv)
        
        # Verify strict entity validation works dynamically
        # Directing explanation with actual director should pass
        ok_explanation = f"This is a great movie directed by {movie_row['director']}"
        llm_provider.validate_entities(ok_explanation, 1)
        
        # Directing explanation with a director of a different title should raise ValueError
        other_row = df[df['director'] != movie_row['director']].iloc[0]
        other_director = other_row['director']
        
        bad_explanation = f"This is a great movie directed by {other_director}"
        with self.assertRaises(ValueError):
            llm_provider.validate_entities(bad_explanation, 1)

if __name__ == "__main__":
    unittest.main()
