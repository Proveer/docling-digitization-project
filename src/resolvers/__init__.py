"""Make resolvers package importable."""

from .document_resolver import DocumentResolver
from .search_resolver import SearchResolver

__all__ = ["DocumentResolver", "SearchResolver"]
