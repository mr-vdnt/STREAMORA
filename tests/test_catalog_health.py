import pytest
from services.catalog.catalog_health import CatalogHealthService
from services.repository.catalog_db import CatalogRepository

def test_catalog_health_audit():
    service = CatalogHealthService()
    health_report = service.audit_catalog_health()
    
    assert "health_score" in health_report
    assert "total_items" in health_report
    assert "metrics" in health_report
    assert health_report["health_score"] >= 0.0
