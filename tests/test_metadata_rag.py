import unittest
import pandas as pd
from services.rag.llm import llm_provider

class TestRAGMetadata(unittest.TestCase):
    def test_complete_metadata_fields(self):
        # Verify that llm_provider correctly loads the 1100 items from movies.csv
        df = llm_provider.movies_df
        self.assertFalse(df.empty, "movies.csv should not be empty")
        self.assertEqual(len(df), 1100, "Should contain exactly 1100 items")
        
        # Test a movie item
        movie_meta = llm_provider.generate_rich_metadata(1, "Inception (2010)", "test explanation")
        self.assertEqual(movie_meta["director"], "Christopher Nolan")
        self.assertEqual(movie_meta["runtime"], "148 min")
        self.assertEqual(movie_meta["languages"], "English")
        
        # Test a TV show item (ID 501, since movies are 1-500, TV shows are 501-800)
        tv_meta = llm_provider.generate_rich_metadata(501, "Breaking Bad (2008)", "test explanation")
        self.assertEqual(tv_meta["director"], "Vince Gilligan")
        self.assertEqual(tv_meta["runtime"], "62 Episodes")
        
        # Test an Anime item (ID 801, since anime are 801-900)
        anime_meta = llm_provider.generate_rich_metadata(801, "Attack on Titan (2013)", "test explanation")
        self.assertEqual(anime_meta["director"], "Tetsurō Araki")
        self.assertEqual(anime_meta["runtime"], "87 Episodes")
        
        # Verify strict entity validation works
        explanation = "This is a great movie directed by Christopher Nolan"
        # Inception (ID 1) is directed by Christopher Nolan, so this should pass validation
        llm_provider.validate_entities(explanation, 1)
        
        # Free Solo (ID 902 is Free Solo, directed by Elizabeth Chai Vasarhelyi). If we validate Christopher Nolan for it, it should raise ValueError
        with self.assertRaises(ValueError):
            llm_provider.validate_entities(explanation, 902)

if __name__ == "__main__":
    unittest.main()
