import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.repository.catalog_db import CatalogRepository, TVSeries
from services.discovery.series_service import SeriesService

def test_series_service():
    repo = CatalogRepository()
    with repo.get_session() as session:
        series = session.query(TVSeries).first()
        if not series:
            print("No TVSeries found in DB!")
            return
        
        series_id = series.id
        print(f"Testing SeriesService for series_id={series_id} ({series.title})...")
        
        service = SeriesService()
        details = service.get_series_payload(series_id=series_id)
        
        assert details is not None, "Failed to get series details!"
        print(f"Title: {details.get('title')}")
        print(f"Seasons count: {len(details.get('seasons', []))}")
        print(f"AI Analysis: {details.get('ai_analysis', {})}")
        print(f"Episode Heatmap count: {len(details.get('heatmap', []))}")
        
        print("SeriesService test PASSED successfully!")

if __name__ == '__main__':
    test_series_service()
