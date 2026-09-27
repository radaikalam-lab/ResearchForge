"""Main API Router aggregating versioned sub-routers."""

from fastapi import APIRouter

from researchforge.api.v1.endpoints import router as v1_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1", tags=["v1"])
