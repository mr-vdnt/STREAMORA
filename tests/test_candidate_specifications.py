from services.repository.catalog_db import CatalogRepository, Content, MovieDetails, SeriesDetails
from services.recommendation.specifications import (
    TrendingIndiaSpecification,
    MovieOnlySpecification,
    SeriesOnlySpecification,
    GenreSpecification,
    MinRatingSpecification
)
from services.recommendation.query_builder import CandidateQueryBuilder
from services.recommendation.shelves import ShelfRegistry, ExposureTracker

def test_specifications_and_query_builder():
    catalog_repo = CatalogRepository()
    session = catalog_repo.get_session()
    
    qb = CandidateQueryBuilder(session)
    movie_spec = MovieOnlySpecification() & MinRatingSpecification(7.0)
    movies = qb.with_specification(movie_spec).order_by_popularity(descending=True).execute(limit=10)
    
    assert isinstance(movies, list)
    for m in movies:
        assert m.get("entity_type") == "movie"
        assert float(m.get("rating", 0)) >= 7.0
    session.close()

def test_declarative_shelves_deduplication():
    catalog_repo = CatalogRepository()
    session = catalog_repo.get_session()
    exposure = ExposureTracker()
    
    shelves = ShelfRegistry.get_home_shelves()
    generated_items = []
    
    for shelf_def in shelves:
        shelf_data = shelf_def.generate(session, exposure)
        for item in shelf_data["items"]:
            generated_items.append(item["id"])
            
    # Verify zero duplicates across all home shelves
    assert len(generated_items) == len(set(generated_items))
    session.close()
