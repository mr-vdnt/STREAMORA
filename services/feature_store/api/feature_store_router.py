from fastapi import APIRouter
from services.feature_store.feature_provider import EnterpriseFeatureProvider

feature_store_router = APIRouter(prefix="/feature_store", tags=["Enterprise Feature Platform"])
provider = EnterpriseFeatureProvider()

@feature_store_router.get("/content/{content_id}")
def get_content_features(content_id: int):
    return provider.get_content_features(content_id)

@feature_store_router.get("/user/{user_id}")
def get_user_features(user_id: str):
    return provider.get_user_features(user_id)

@feature_store_router.get("/definitions")
def get_definitions():
    defs = provider.registry.list_features()
    return {"definitions": [{"name": d.name, "entity_type": d.entity_type, "type": d.value_type.value, "description": d.description} for d in defs]}
