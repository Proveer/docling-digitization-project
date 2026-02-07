"""Make routers package importable."""

from .document_router import router as document_router
from .search_router import router as search_router
from .health_router import router as health_router
from .main import app

__all__ = ["document_router", "search_router", "health_router", "app"]
