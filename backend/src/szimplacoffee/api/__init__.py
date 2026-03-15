from fastapi import APIRouter

from .merchants import router as merchants_router
from .products import router as products_router
from .recommendations import router as recommendations_router
from .discovery import router as discovery_router
from .dashboard import router as dashboard_router
from .crawl import router as crawl_router
from .history import router as history_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(merchants_router)
api_router.include_router(products_router)
api_router.include_router(recommendations_router)
api_router.include_router(discovery_router)
api_router.include_router(dashboard_router)
api_router.include_router(crawl_router)
api_router.include_router(history_router)
