"""Search service (resolver)."""

from typing import List
from sqlalchemy.orm import Session

from src.database.repository import DocumentRepository, ContentRepository
from src.database.models import Document, ContentBlock


class SearchResolver:
    """Service for search operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.doc_repo = DocumentRepository(db_session)
        self.content_repo = ContentRepository(db_session)
    
    def search_documents(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Search documents by title or filename."""
        return self.doc_repo.search(query=query, skip=skip, limit=limit)
    
    def search_content(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ContentBlock]:
        """Full-text search in content blocks."""
        return self.content_repo.search_text(query=query, skip=skip, limit=limit)
    
    def get_tables(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ContentBlock]:
        """Get all table content blocks."""
        return self.content_repo.search_by_type(
            content_type="table",
            skip=skip,
            limit=limit
        )
    
    def get_images(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ContentBlock]:
        """Get all image content blocks."""
        return self.content_repo.search_by_type(
            content_type="image",
            skip=skip,
            limit=limit
        )
