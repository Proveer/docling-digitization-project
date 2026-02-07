"""
Database models for document storage.

This module defines the SQLAlchemy ORM models for storing digitized documents
in a hierarchical structure. The schema supports:

- **Documents**: Top-level container for processed files
- **Sections**: Hierarchical document structure (chapters, sections, subsections)
- **ContentBlocks**: Individual content elements (text, images, tables)

Schema Design:
--------------
The database uses a three-tier hierarchy:

    Document (1)
        ├── Section (N) - can be nested
        │   ├── Section (N) - child sections
        │   └── ContentBlock (N) - content within section
        └── Section (N)

Features:
---------
- UUID-based primary keys for distributed systems
- Cascade deletes to maintain referential integrity
- JSON fields for flexible metadata storage
- Indexed fields for optimized queries
- Support for hierarchical sections with parent-child relationships

Database Support:
-----------------
- SQLite: Development and small-scale deployments
- PostgreSQL: Production with high concurrency
- MySQL: Alternative production database

Example Usage:
--------------
    from src.database.models import Document, Section, ContentBlock
    from src.database.connection import get_db_session
    
    # Create a new document
    db = get_db_session()
    doc = Document(
        title="My Document",
        source_filename="document.pdf",
        doc_metadata={"page_count": 10}
    )
    db.add(doc)
    db.commit()
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    This declarative base provides the foundation for all database models
    in the application. It uses SQLAlchemy 2.0+ declarative syntax.
    """
    pass


class Document(Base):
    """
    Document model representing a processed document.
    
    This is the top-level entity in the document hierarchy. Each document
    represents a single processed file (PDF, DOCX, PPTX, etc.) and contains
    metadata about the file along with its hierarchical content structure.
    
    Attributes:
    -----------
    id : str
        UUID primary key for the document
    title : str
        Document title (extracted from content or filename)
    source_filename : str
        Original filename of the uploaded document
    file_path : str, optional
        Path to the stored file on disk
    doc_metadata : dict, optional
        JSON field containing document-level metadata:
        - page_headers: List of recurring page headers
        - page_footers: List of recurring page footers
        - page_count: Total number of pages
        - file_size: Size of the original file
        - processing_time: Time taken to process the document
    created_at : datetime
        Timestamp when the document was created
    updated_at : datetime
        Timestamp when the document was last modified
    
    Relationships:
    --------------
    sections : List[Section]
        All sections belonging to this document (cascade delete enabled)
    
    Indexes:
    --------
    - idx_document_title: For fast title-based searches
    - idx_document_created_at: For sorting by creation date
    
    Example:
    --------
        doc = Document(
            title="Annual Report 2024",
            source_filename="report_2024.pdf",
            doc_metadata={
                "page_count": 45,
                "page_headers": ["Company Confidential"],
                "page_footers": ["Page {page_no}"]
            }
        )
    """
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    source_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)
    doc_metadata = Column(JSON, nullable=True)  # Stores page_headers, page_footers, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sections = relationship("Section", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_document_title', 'title'),
        Index('idx_document_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title})>"


class Section(Base):
    """
    Section model representing hierarchical document sections.
    
    Sections represent the structural hierarchy of a document (chapters,
    sections, subsections, etc.). They support nested parent-child
    relationships for complex document structures.
    
    Attributes:
    -----------
    id : str
        UUID primary key for the section
    document_id : str
        Foreign key to the parent document
    parent_id : str, optional
        Foreign key to parent section (None for top-level sections)
    title : str
        Section heading/title
    level : int, optional
        Hierarchical level (1 for chapter, 2 for section, 3 for subsection, etc.)
    order : int
        Position within parent (for maintaining document order)
    
    Relationships:
    --------------
    document : Document
        The document this section belongs to
    parent : Section, optional
        Parent section (None for top-level sections)
    children : List[Section]
        Child sections (subsections)
    content_blocks : List[ContentBlock]
        Content elements within this section (cascade delete enabled)
    
    Indexes:
    --------
    - idx_section_document_id: For finding all sections in a document
    - idx_section_parent_id: For finding child sections
    - idx_section_order: For maintaining correct section order
    
    Example:
    --------
        # Top-level section
        chapter = Section(
            document_id=doc.id,
            title="Chapter 1: Introduction",
            level=1,
            order=0
        )
        
        # Nested subsection
        subsection = Section(
            document_id=doc.id,
            parent_id=chapter.id,
            title="1.1 Background",
            level=2,
            order=0
        )
    """
    
    __tablename__ = "sections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(1000), nullable=False)
    level = Column(Integer, nullable=True)
    order = Column(Integer, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="sections")
    parent = relationship("Section", remote_side=[id], backref="children")
    content_blocks = relationship("ContentBlock", back_populates="section", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_section_document_id', 'document_id'),
        Index('idx_section_parent_id', 'parent_id'),
        Index('idx_section_order', 'order'),
    )
    
    def __repr__(self):
        return f"<Section(id={self.id}, title={self.title}, level={self.level})>"


class ContentBlock(Base):
    """
    Content block model for text, images, tables, etc.
    
    ContentBlocks represent individual content elements within a document.
    They can be text paragraphs, images, tables, code blocks, or any other
    content type extracted from the source document.
    
    Attributes:
    -----------
    id : str
        UUID primary key for the content block
    section_id : str, optional
        Foreign key to parent section (None for document-level content)
    type : str
        Content type: 'text', 'image', 'table', 'code', 'list', etc.
    text : str, optional
        Text content (for text blocks)
    src : str, optional
        File path for images/tables (e.g., 'output/doc_123/images/img_001.png')
    block_metadata : dict, optional
        JSON field containing type-specific metadata:
        - For tables: columns, rows, caption, ai_summary
        - For images: caption, width, height, ai_description
        - For text: formatting, style
        - Common: page_no, bbox (bounding box coordinates)
    order : int
        Position within parent section (for maintaining content order)
    created_at : datetime
        Timestamp when the content block was created
    
    Relationships:
    --------------
    section : Section, optional
        The section this content belongs to
    
    Indexes:
    --------
    - idx_content_section_id: For finding all content in a section
    - idx_content_type: For filtering by content type (e.g., all tables)
    - idx_content_order: For maintaining correct content order
    
    Example:
    --------
        # Text block
        text_block = ContentBlock(
            section_id=section.id,
            type='text',
            text='This is a paragraph of text.',
            order=0
        )
        
        # Table block with AI summary
        table_block = ContentBlock(
            section_id=section.id,
            type='table',
            src='output/doc_123/tables/table_001.csv',
            block_metadata={
                'caption': 'Quarterly Sales Data',
                'columns': ['Q1', 'Q2', 'Q3', 'Q4'],
                'rows': 5,
                'ai_summary': 'Sales increased by 15% year-over-year',
                'page_no': 12
            },
            order=1
        )
    """
    
    __tablename__ = "content_blocks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id = Column(String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(50), nullable=False)  # text, image, table, etc.
    text = Column(Text, nullable=True)
    src = Column(String(1000), nullable=True)  # Path to image/table file
    block_metadata = Column(JSON, nullable=True)  # Stores columns, rows, captions, AI summaries, etc.
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    section = relationship("Section", back_populates="content_blocks")
    
    # Indexes
    __table_args__ = (
        Index('idx_content_section_id', 'section_id'),
        Index('idx_content_type', 'type'),
        Index('idx_content_order', 'order'),
    )
    
    def __repr__(self):
        return f"<ContentBlock(id={self.id}, type={self.type})>"
