"""Repository pattern for database operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc

from .models import Document, Section, ContentBlock


class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_from_json(self, json_data: Dict[str, Any]) -> Document:
        """
        Create a document with all its sections and content from hierarchical JSON.
        
        Args:
            json_data: Hierarchical JSON from transformer.py
            
        Returns:
            Created Document instance
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
        """Recursively process children nodes."""
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
        """Get document by ID with all relationships loaded."""
        return self.db.query(Document).options(
            joinedload(Document.sections).joinedload(Section.content_blocks)
        ).filter(Document.id == document_id).first()
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """List all documents with pagination."""
        return self.db.query(Document).order_by(
            desc(Document.created_at)
        ).offset(skip).limit(limit).all()
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """Search documents by title or content."""
        search_pattern = f"%{query}%"
        return self.db.query(Document).filter(
            or_(
                Document.title.ilike(search_pattern),
                Document.source_filename.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()
    
    def delete(self, document_id: str) -> bool:
        """Delete a document and all its related data."""
        document = self.get_by_id(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """Get total number of documents."""
        return self.db.query(Document).count()


class ContentRepository:
    """Repository for content block operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_by_type(self, content_type: str, skip: int = 0, limit: int = 100) -> List[ContentBlock]:
        """Search content blocks by type (e.g., 'table', 'image')."""
        return self.db.query(ContentBlock).filter(
            ContentBlock.type == content_type
        ).offset(skip).limit(limit).all()
    
    def search_text(self, query: str, skip: int = 0, limit: int = 100) -> List[ContentBlock]:
        """Full-text search in content blocks."""
        search_pattern = f"%{query}%"
        return self.db.query(ContentBlock).filter(
            ContentBlock.text.ilike(search_pattern)
        ).offset(skip).limit(limit).all()
