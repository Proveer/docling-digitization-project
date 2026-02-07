"""Database models for document storage."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Document(Base):
    """Document model representing a processed document."""
    
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
    """Section model representing hierarchical document sections."""
    
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
    """Content block model for text, images, tables, etc."""
    
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
