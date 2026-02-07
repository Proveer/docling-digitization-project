"""
Repository pattern for database operations.

This module implements the Repository pattern to abstract database operations
and provide a clean interface for data access. It separates business logic
from data access logic, making the code more maintainable and testable.

Pattern Benefits:
-----------------
- **Abstraction**: Hides complex SQLAlchemy queries behind simple methods
- **Testability**: Easy to mock repositories for unit testing
- **Maintainability**: Database logic centralized in one place
- **Flexibility**: Easy to swap database implementations

Repositories:
-------------
- DocumentRepository: CRUD operations for documents and their hierarchies
- ContentRepository: Specialized queries for content blocks

Example Usage:
--------------
    from src.database import get_db_session
    from src.database.repository import DocumentRepository
    
    # Create repository instance
    db = get_db_session()
    doc_repo = DocumentRepository(db)
    
    # Create document from JSON
    json_data = {...}  # From transformer.py
    document = doc_repo.create_from_json(json_data)
    
    # Query documents
    all_docs = doc_repo.list_all(skip=0, limit=10)
    search_results = doc_repo.search("annual report")
    
    # Clean up
    db.close()
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc

from .models import Document, Section, ContentBlock


class DocumentRepository:
    """
    Repository for document operations.
    
    Provides high-level methods for creating, reading, updating, and deleting
    documents along with their hierarchical structure (sections and content blocks).
    
    This repository handles the complexity of:
    - Creating documents from hierarchical JSON
    - Recursively processing nested sections
    - Managing relationships between documents, sections, and content
    - Eager loading related data to avoid N+1 query problems
    
    Attributes:
        db (Session): SQLAlchemy database session
    
    Example:
        >>> db = get_db_session()
        >>> repo = DocumentRepository(db)
        >>> 
        >>> # Create document
        >>> doc = repo.create_from_json(json_data)
        >>> 
        >>> # Query document
        >>> doc = repo.get_by_id(doc.id)
        >>> print(f"Sections: {len(doc.sections)}")
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_from_json(self, json_data: Dict[str, Any]) -> Document:
        """
        Create a document with all its sections and content from hierarchical JSON.
        
        This method takes the hierarchical JSON output from transformer.py and
        creates a complete document structure in the database, including:
        - The document record
        - All nested sections (with parent-child relationships)
        - All content blocks (text, images, tables)
        
        The method handles the complexity of:
        - Recursive section processing
        - Maintaining correct order of sections and content
        - Preserving hierarchical relationships
        - Extracting metadata (page headers, footers, etc.)
        
        Args:
            json_data: Hierarchical JSON structure from transformer.py containing:
                - id: Document UUID
                - title: Document title
                - metadata: {source, page_count, etc.}
                - page_headers: List of recurring headers
                - page_footers: List of recurring footers
                - children: List of sections and content blocks
        
        Returns:
            Document: The created Document instance with all relationships loaded
        
        Raises:
            SQLAlchemyError: If database operation fails
        
        Example:
            >>> json_data = {
            >>>     "id": "doc-123",
            >>>     "title": "Annual Report",
            >>>     "metadata": {"source": "report.pdf", "page_count": 50},
            >>>     "children": [
            >>>         {"type": "section", "title": "Chapter 1", "children": [...]},
            >>>         {"type": "text", "text": "Introduction..."}
            >>>     ]
            >>> }
            >>> doc = repo.create_from_json(json_data)
            >>> print(f"Created: {doc.title}")
        """
        # Create document
        document = Document(
            id=json_data.get("id"),
            title=json_data.get("title", "Untitled"),
            source_filename=json_data.get("metadata", {}).get("source", "unknown"),
            doc_metadata={
                "page_headers": json_data.get("page_headers", []),
                "page_footers": json_data.get("page_footers", []),
                "page_count": json_data.get("metadata", {}).get("page_count", 0)
            }
        )
        self.db.add(document)
        
        # Process children recursively
        self._process_children(json_data.get("children", []), document.id, None, 0)
        
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def _process_children(self, children: List[Dict], document_id: str, parent_section_id: Optional[str], order_offset: int):
        """
        Recursively process children nodes (sections and content blocks).
        
        This private method handles the recursive traversal of the document
        hierarchy, creating Section and ContentBlock records as it goes.
        
        The method:
        - Distinguishes between sections and content blocks
        - Creates sections and recursively processes their children
        - Creates content blocks with appropriate metadata
        - Maintains correct ordering within each level
        
        Args:
            children: List of child nodes (sections or content blocks)
            document_id: UUID of the parent document
            parent_section_id: UUID of the parent section (None for top-level)
            order_offset: Starting order number for this level
        
        Note:
            This is a private method called internally by create_from_json().
            It uses db.flush() to get section IDs before processing children.
        """
        for idx, child in enumerate(children):
            child_type = child.get("type")
            order = order_offset + idx
            
            if child_type == "section":
                # Create section
                section = Section(
                    id=child.get("id"),
                    document_id=document_id,
                    parent_id=parent_section_id,
                    title=child.get("title", "Untitled Section"),
                    level=child.get("level"),
                    order=order
                )
                self.db.add(section)
                self.db.flush()  # Get the section ID
                
                # Process section's children
                self._process_children(child.get("children", []), document_id, section.id, 0)
            
            else:
                # Create content block (text, image, table, etc.)
                content = ContentBlock(
                    id=child.get("id"),
                    section_id=parent_section_id,
                    type=child_type,
                    text=child.get("text"),
                    src=child.get("src"),
                    block_metadata={
                        "caption": child.get("caption"),
                        "columns": child.get("columns"),
                        "rows": child.get("rows"),
                        "page_no": child.get("metadata", {}).get("page_no")
                    },
                    order=order
                )
                self.db.add(content)
    
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID with all relationships eagerly loaded.
        
        Uses SQLAlchemy's joinedload to eagerly load all sections and their
        content blocks in a single query, avoiding N+1 query problems.
        
        Args:
            document_id: UUID of the document to retrieve
        
        Returns:
            Document instance with all relationships loaded, or None if not found
        
        Example:
            >>> doc = repo.get_by_id("doc-123")
            >>> if doc:
            >>>     for section in doc.sections:
            >>>         print(f"Section: {section.title}")
            >>>         for block in section.content_blocks:
            >>>             print(f"  - {block.type}")
        """
        return self.db.query(Document).options(
            joinedload(Document.sections).joinedload(Section.content_blocks)
        ).filter(Document.id == document_id).first()
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        List all documents with pagination, ordered by creation date (newest first).
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of Document instances
        
        Example:
            >>> # Get first page
            >>> docs = repo.list_all(skip=0, limit=10)
            >>> 
            >>> # Get second page
            >>> docs = repo.list_all(skip=10, limit=10)
        """
        return self.db.query(Document).order_by(
            desc(Document.created_at)
        ).offset(skip).limit(limit).all()
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Search documents by title or source filename (case-insensitive).
        
        Uses SQL ILIKE for case-insensitive pattern matching. Searches in:
        - Document title
        - Source filename
        
        Args:
            query: Search term (partial matches supported)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of matching Document instances
        
        Example:
            >>> # Find all documents with "report" in title or filename
            >>> results = repo.search("report")
            >>> for doc in results:
            >>>     print(f"{doc.title} ({doc.source_filename})")
        """
        search_pattern = f"%{query}%"
        return self.db.query(Document).filter(
            or_(
                Document.title.ilike(search_pattern),
                Document.source_filename.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()
    
    def delete(self, document_id: str) -> bool:
        """
        Delete a document and all its related data (cascade delete).
        
        Due to cascade delete relationships, this will automatically delete:
        - All sections belonging to the document
        - All content blocks within those sections
        
        Args:
            document_id: UUID of the document to delete
        
        Returns:
            True if document was found and deleted, False if not found
        
        Example:
            >>> if repo.delete("doc-123"):
            >>>     print("Document deleted successfully")
            >>> else:
            >>>     print("Document not found")
        """
        document = self.get_by_id(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """
        Get total number of documents in the database.
        
        Returns:
            Total document count
        
        Example:
            >>> total = repo.count()
            >>> print(f"Total documents: {total}")
        """
        return self.db.query(Document).count()


class ContentRepository:
    """
    Repository for content block operations.
    
    Provides specialized queries for searching and filtering content blocks
    by type (tables, images, etc.) or text content.
    
    Attributes:
        db (Session): SQLAlchemy database session
    
    Example:
        >>> db = get_db_session()
        >>> content_repo = ContentRepository(db)
        >>> 
        >>> # Get all tables
        >>> tables = content_repo.search_by_type("table")
        >>> for table in tables:
        >>>     print(table.block_metadata.get("caption"))
    """
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def search_by_type(self, content_type: str, skip: int = 0, limit: int = 100) -> List[ContentBlock]:
        """
        Search content blocks by type (e.g., 'table', 'image', 'text').
        
        Useful for finding all instances of a specific content type across
        all documents.
        
        Args:
            content_type: Type of content to search for ('table', 'image', 'text', etc.)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of ContentBlock instances of the specified type
        
        Example:
            >>> # Get all tables
            >>> tables = content_repo.search_by_type("table", limit=50)
            >>> print(f"Found {len(tables)} tables")
            >>> 
            >>> # Get all images
            >>> images = content_repo.search_by_type("image")
        """
        return self.db.query(ContentBlock).filter(
            ContentBlock.type == content_type
        ).offset(skip).limit(limit).all()
    
    def search_text(self, query: str, skip: int = 0, limit: int = 100) -> List[ContentBlock]:
        """
        Full-text search in content blocks (case-insensitive).
        
        Searches the text field of content blocks for matching content.
        Uses ILIKE for case-insensitive pattern matching.
        
        Args:
            query: Search term (partial matches supported)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
        
        Returns:
            List of ContentBlock instances with matching text
        
        Example:
            >>> # Find all content mentioning "revenue"
            >>> results = content_repo.search_text("revenue")
            >>> for block in results:
            >>>     print(f"{block.type}: {block.text[:100]}...")
        """
        search_pattern = f"%{query}%"
        return self.db.query(ContentBlock).filter(
            ContentBlock.text.ilike(search_pattern)
        ).offset(skip).limit(limit).all()
