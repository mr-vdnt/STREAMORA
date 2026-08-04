from __future__ import annotations
import time
from typing import List, Dict, Any
from services.feature_store.feature_materializer import EnterpriseFeatureMaterializer

class EnterpriseFeatureScheduler:
    """Background scheduler updating pre-computed entity feature vectors."""

    def __init__(self, materializer: EnterpriseFeatureMaterializer = None):
        self.materializer = materializer or EnterpriseFeatureMaterializer()

    def materialize_all_active_content(self, content_ids: List[int]) -> int:
        count = 0
        for cid in content_ids:
            self.materializer.materialize_content_features(cid)
            count += 1
        return count
