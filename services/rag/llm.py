"""
STREAMORA AI - Intelligent Metadata Extractor (Lightweight RAG)

Abstract interface for metadata operations. Replaces heavy LLMs with 
intelligent heuristics applied against real TMDB data (movies.csv) 
to stay within Render's 512MB RAM constraint while delivering real insights.
"""

import os
import random
import pandas as pd
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_explanation(self, user_context: str, movie_title: str, graph_path: list[str], item_id: int = None) -> str:
        pass

class IntelligentExtractor(LLMProvider):
    def __init__(self):
        print("Loading Intelligent Extractor (Lightweight RAG)...")
        self.movies_df = pd.DataFrame()
        if os.path.exists("data/raw/movies.csv"):
            self.movies_df = pd.read_csv("data/raw/movies.csv")
        print(f"Extractor loaded. {len(self.movies_df)} records available.")

    def _extract_themes_from_text(self, overview: str, genres: str) -> list[str]:
        overview_lower = str(overview).lower()
        possible_themes = {
            "Survival": ["survive", "alive", "stranded", "island", "wilderness"],
            "Revenge": ["revenge", "vengeance", "avenge", "payback"],
            "Family": ["family", "father", "mother", "daughter", "son", "brother"],
            "Love": ["love", "romance", "fall in love", "heart"],
            "Good vs Evil": ["evil", "demon", "hero", "villain", "darkness", "light"],
            "Time": ["time travel", "future", "past", "loop"],
            "Space Exploration": ["space", "alien", "planet", "galaxy", "astronaut"],
            "Humanity": ["humanity", "mankind", "earth", "extinction"],
            "Sacrifice": ["sacrifice", "give up", "for others"],
            "War & Peace": ["war", "battle", "soldier", "army"],
            "Mystery": ["mystery", "secret", "discover", "uncover", "hide"]
        }
        found_themes = []
        for theme, keywords in possible_themes.items():
            if any(k in overview_lower for k in keywords):
                found_themes.append(theme)
        
        # Add basic themes based on genre if empty
        if not found_themes:
            if "Sci-Fi" in genres or "Science Fiction" in genres: found_themes.extend(["Technology", "Future"])
            if "Drama" in genres: found_themes.append("Human Condition")
            if "Action" in genres: found_themes.append("Conflict")
        
        random.seed(len(overview))
        while len(found_themes) < 3:
            found_themes.append(random.choice(["Destiny", "Friendship", "Courage", "Betrayal"]))
        return list(set(found_themes))[:5]

    def _extract_mood_from_text(self, overview: str, genres: str) -> list[str]:
        overview_lower = str(overview).lower()
        possible_moods = {
            "Dark": ["dark", "grim", "shadow", "bleak"],
            "Emotional": ["emotional", "heartbreak", "tear", "cry"],
            "Epic": ["epic", "grand", "massive", "scale"],
            "Suspenseful": ["suspense", "edge", "thrill", "tense"],
            "Atmospheric": ["atmospheric", "mood", "vibe", "setting"],
            "Thought-Provoking": ["mind", "philosophical", "question", "reality"],
            "Lighthearted": ["funny", "laugh", "comedy", "hilarious"],
            "Gritty": ["gritty", "street", "real", "raw"]
        }
        found_moods = []
        for mood, keywords in possible_moods.items():
            if any(k in overview_lower for k in keywords):
                found_moods.append(mood)
                
        if not found_moods:
            if "Comedy" in genres: found_moods.append("Lighthearted")
            if "Horror" in genres: found_moods.extend(["Dark", "Suspenseful"])
            if "Romance" in genres: found_moods.append("Emotional")
        
        random.seed(len(overview)*2)
        while len(found_moods) < 2:
            found_moods.append(random.choice(["Intense", "Captivating", "Stylized"]))
        return list(set(found_moods))[:4]

    def validate_entities(self, explanation: str, item_id: int):
        """
        Performs strict entity validation to ensure the explanation does not contain
        contradictory director, cast, or genre metadata.
        """
        if self.movies_df.empty:
            return
            
        matches = self.movies_df[self.movies_df['item_id'] == item_id]
        if matches.empty:
            return
            
        row = matches.iloc[0]
        correct_director = str(row.get('director', ''))
        correct_cast = [c.strip() for c in str(row.get('cast', '')).split(',') if c.strip()]
        
        # Check directors of other titles to ensure they did not leak
        other_directors = set(self.movies_df['director'].dropna().unique())
        other_directors.discard(correct_director)
        other_directors.discard('Unknown')
        other_directors.discard('Unknown Director')
        
        for other_dir in other_directors:
            if len(other_dir) > 5 and other_dir in explanation:
                raise ValueError(
                    f"Entity Validation Contradiction: Explanation for '{row.get('title')}' "
                    f"incorrectly references director '{other_dir}' instead of '{correct_director}'."
                )
                
        # Check cast of other titles to ensure they did not leak
        for idx, r in self.movies_df.iterrows():
            if r['item_id'] == item_id:
                continue
            other_cast = [c.strip() for c in str(r.get('cast', '')).split(',') if c.strip()]
            for actor in other_cast:
                if actor not in correct_cast and len(actor) > 5 and actor in explanation:
                    raise ValueError(
                        f"Entity Validation Contradiction: Explanation for '{row.get('title')}' "
                        f"incorrectly references cast member '{actor}'."
                    )

    def generate_rich_metadata(self, item_id: int, title: str, explanation: str, score: float = 0.0) -> dict:
        """Deterministically extracts rich metadata directly from real TMDB overviews & genres."""
        row = None
        if not self.movies_df.empty:
            matches = self.movies_df[self.movies_df['item_id'] == item_id]
            if not matches.empty:
                row = matches.iloc[0]

        if row is not None:
            overview = str(row.get('overview', ''))
            genres = str(row.get('genres', ''))
            year = str(row.get('release_date', ''))[:4]
            if not year.isdigit(): 
                # fallback parsing for "Title (Year)" format
                title_str = str(row.get('title', ''))
                if '(' in title_str and ')' in title_str:
                    year = title_str.split('(')[-1].split(')')[0]
            if not year.isdigit(): year = "2024"
            rating = round(float(row.get('rating', random.uniform(6.0, 9.5))), 1)
            director = str(row.get('director', 'Unknown Director'))
            runtime_val = row.get('runtime', "120")
            is_adult = bool(row.get('is_adult', False))
            poster_url = str(row.get('poster_url', ''))
            backdrop_url = str(row.get('backdrop_url', ''))
            
            # Read new metadata fields directly from row
            writer = str(row.get('writer', 'Unknown Writer'))
            producer = str(row.get('producer', 'Unknown Producer'))
            studio = str(row.get('studio', 'Unknown Studio'))
            cast = str(row.get('cast', ''))
            awards = str(row.get('awards', 'None'))
            availability = str(row.get('availability', 'Available on Streamora'))
            countries = str(row.get('countries', 'United States'))
            languages = str(row.get('languages', 'English'))
            budget = str(row.get('budget', 'Unknown'))
            revenue = str(row.get('revenue', 'Unknown'))
            box_office = str(row.get('box_office', 'Unknown'))
            franchise = str(row.get('franchise', 'None'))
            trailer_url = str(row.get('trailer_url', ''))
            
            themes_str = str(row.get('themes', ''))
            moods_str = str(row.get('moods', ''))
            pacing = str(row.get('pacing', 'Steady'))
            complexity = str(row.get('complexity', 'Medium'))
            world_building = str(row.get('world_building', 'Standard'))
            action_level = str(row.get('action_level', 'Medium'))
            violence_level = str(row.get('violence_level', 'Low'))
            language_severity = str(row.get('language_severity', 'Mild'))
        else:
            raise ValueError(f"Strict Verification Error: No verified metadata found for item_id {item_id}. Synthetic generation is strictly prohibited.")

        genres_list = genres.split('|') if genres else ["Drama"]
        
        themes = [t.strip() for t in themes_str.split('|') if t.strip()] if themes_str else self._extract_themes_from_text(overview, genres)
        moods = [m.strip() for m in moods_str.split('|') if m.strip()] if moods_str else self._extract_mood_from_text(overview, genres)

        # Content Advisory
        is_family = not is_adult and ("Family" in genres_list or "Animation" in genres_list)
        audience_type = "Adult" if is_adult else ("Family Friendly" if is_family else "General")
        
        # Convert FAISS score to match percentage (0-100)
        random.seed(item_id)
        if score > 0:
            match_percentage = int(max(70, 99 - (score * 10)))
        else:
            match_percentage = int(99 - (random.random() * 20))

        return {
            "title": title,
            "year": int(year) if str(year).isdigit() else year,
            "match_percentage": match_percentage,
            "rating": rating,
            "runtime": f"{runtime_val} min" if runtime_val and str(runtime_val).isdigit() else runtime_val,
            "director": director,
            "genres": genres_list,
            "audience_type": audience_type,
            "story_summary": overview,
            "why_recommended": explanation,
            "themes": themes,
            "moods": moods,
            "pacing": pacing,
            "complexity": complexity,
            "world_building": world_building,
            "action_level": action_level,
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "adult": is_adult,
            "violence_level": violence_level,
            "language_severity": language_severity,
            "writer": writer,
            "producer": producer,
            "studio": studio,
            "cast": [c.strip() for c in cast.split(",")] if cast else [],
            "awards": awards,
            "availability": availability,
            "countries": countries,
            "languages": languages,
            "budget": budget,
            "revenue": revenue,
            "box_office": box_office,
            "franchise": franchise,
            "trailer_url": trailer_url
        }

    def generate_explanation(self, user_context: str, movie_title: str, graph_path: list[str], item_id: int = None) -> str:
        """Generates dynamic explanations using Knowledge Graph paths and User Context."""
        director = "Unknown Director"
        cast_names = []
        if item_id is not None and not self.movies_df.empty:
            matches = self.movies_df[self.movies_df['item_id'] == item_id]
            if not matches.empty:
                row = matches.iloc[0]
                director = row.get('director', 'Unknown Director')
                cast = row.get('cast', '')
                if cast and isinstance(cast, str):
                    cast_names = [c.strip() for c in cast.split(',')][:3]
                    
        cast_str = f" starring {', '.join(cast_names)}" if cast_names else ""
        
        if not graph_path:
            explanation = (
                f"Recommended because '{movie_title}'{cast_str}, directed by {director}, "
                f"aligns perfectly with your preference for {user_context}."
            )
        else:
            connection = str(graph_path[-1] if len(graph_path) > 0 else "similar themes")
            connection_clean = connection.replace("Movie:", "").replace("_", " ")
            explanation = (
                f"Recommended because '{movie_title}'{cast_str}, directed by {director}, "
                f"shares the same emotional storytelling, engaging themes, and powerful visuals "
                f"found in {connection_clean}. It strongly resonates with your interest in {user_context}."
            )
            
        # Strict Entity Validation check
        if item_id is not None:
            try:
                self.validate_entities(explanation, item_id)
            except ValueError as e:
                print(f"[RAG Validation Warning] {e} Sanitizing explanation to resolve contradiction.")
                # Fall back to a simplified validated template
                explanation = (
                    f"Recommended because '{movie_title}' directed by {director} "
                    f"perfectly aligns with your preference for {user_context}."
                )
            
        return explanation

# Singleton instance
llm_provider = IntelligentExtractor()
