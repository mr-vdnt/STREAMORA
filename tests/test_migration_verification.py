import pytest
from services.catalog.migration_pipeline import MigrationVerificationPipeline
from services.repository.catalog_db import CatalogRepository

def test_migration_verification_pipeline():
    pipeline = MigrationVerificationPipeline()
    result = pipeline.run_migration("data/catalog_v2.db")

    assert "success" in result
    assert result["success"] is True
    assert "migrated_count" in result
    assert "verification_status" in result
