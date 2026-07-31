from typing import List, Dict, Any
from services.repository.movie_repository import MovieRepository
from services.repository.series_repository import SeriesRepository

class QueryParser:
    @staticmethod
    def parse(query: str) -> Dict[str, Any]:
        cleaned = query.strip().lower()
        is_actor_intent = "movie with" in cleaned or "starring" in cleaned
        is_genre_intent = any(g in cleaned for g in ["sci-fi", "action", "comedy", "drama", "crime", "thriller", "horror"])
        return {
            "raw": query,
            "cleaned": cleaned,
            "is_actor_intent": is_actor_intent,
            "is_genre_intent": is_genre_intent
        }


class IntentDetector:
    @staticmethod
    def detect_format_preference(parsed_query: Dict[str, Any]) -> str:
        cleaned = parsed_query["cleaned"]
        if "series" in cleaned or "show" in cleaned or "tv" in cleaned:
            return "series"
        if "movie" in cleaned or "film" in cleaned:
            return "movie"
        return "all"


class KeywordSearch:
    def __init__(self):
        self.movie_repo = MovieRepository()
        self.series_repo = SeriesRepository()

    def search(self, parsed_query: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        term = parsed_query["cleaned"]
        results = []
        
        # Search movies
        for movie in self.movie_repo.get_top_movies(limit=100):
            title = str(movie.get("title", "")).lower()
            genres = str(movie.get("genres", "")).lower()
            if term in title or term in genres:
                results.append(movie)

        # Search series
        for series in self.series_repo.get_top_series(limit=100):
            title = str(series.get("title", "")).lower()
            genres = str(series.get("genres", "")).lower()
            if term in title or term in genres:
                results.append(series)

        return results


class SearchFusion:
    @staticmethod
    def fuse(keyword_results: List[Dict[str, Any]], format_pref: str) -> List[Dict[str, Any]]:
        if format_pref == "movie":
            filtered = [r for r in keyword_results if r.get("entity_type") == "movie"]
        elif format_pref == "series":
            filtered = [r for r in keyword_results if r.get("entity_type") == "tvseries"]
        else:
            filtered = keyword_results

        # Deduplicate results by ID
        seen = set()
        deduped = []
        for item in filtered:
            item_id = item.get("id")
            if item_id not in seen:
                seen.add(item_id)
                deduped.append(item)

        return deduped


class SearchRanker:
    @staticmethod
    def rank(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(items, key=lambda x: float(x.get("popularity", 0.0) or 0.0), reverse=True)


class ModularSearchPipeline:
    """
    Search Subsystem Pipeline:
    QueryParser ➔ IntentDetector ➔ KeywordSearch ➔ SearchFusion ➔ SearchRanker
    """
    def __init__(self):
        self.parser = QueryParser()
        self.intent_detector = IntentDetector()
        self.keyword_search = KeywordSearch()
        self.fusion = SearchFusion()
        self.ranker = SearchRanker()

    def execute_search(self, query: str) -> List[Dict[str, Any]]:
        parsed = self.parser.parse(query)
        format_pref = self.intent_detector.detect_format_preference(parsed)
        candidates = self.keyword_search.search(parsed)
        fused = self.fusion.fuse(candidates, format_pref)
        return self.ranker.rank(fused)
