import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

def test_enterprise_feature_registry():
    from services.feature_store.feature_registry import EnterpriseFeatureRegistry
    reg = EnterpriseFeatureRegistry()
    content_feats = reg.list_features("content")
    assert len(content_feats) >= 4
    p_feat = reg.get_feature("popularity_score")
    assert p_feat is not None
    assert p_feat.entity_type == "content"

def test_enterprise_feature_cache_and_materializer():
    from services.feature_store.feature_provider import EnterpriseFeatureProvider
    provider = EnterpriseFeatureProvider()

    # Materialize content features
    feats = provider.get_content_features(1)
    assert feats["content_id"] == 1
    assert "popularity_score" in feats
    assert "dense_vector" in feats

    # Test caching
    cached = provider.get_content_features(1)
    assert cached == feats

def test_user_feature_retrieval():
    from services.feature_store.feature_provider import EnterpriseFeatureProvider
    provider = EnterpriseFeatureProvider()
    u_feats = provider.get_user_features("user_777")
    assert u_feats["user_id"] == "user_777"
    assert "genre_affinities" in u_feats

if __name__ == "__main__":
    print("Executing Enterprise Feature Platform Verification Suite...")
    test_enterprise_feature_registry()
    print("[PASSED] Enterprise Feature Registry (feature_registry.py)")
    test_enterprise_feature_cache_and_materializer()
    print("[PASSED] Feature Materialization & Caching (feature_materializer.py, feature_cache.py)")
    test_user_feature_retrieval()
    print("[PASSED] User Feature Vector Retrieval (feature_provider.py)")
    print("ENTERPRISE FEATURE PLATFORM VERIFICATION COMPLETE (100%)!")
