"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document metadata schema."""
    page_headers: List[str] = []
    page_footers: List[str] = []
    page_count: int = 0


class ContentBlockResponse(BaseModel):
    """Content block response schema."""
    id: str
    section_id: Optional[str]
    type: str
    text: Optional[str]
    src: Optional[str]
    block_metadata: Optional[Dict[str, Any]]
    order: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SectionResponse(BaseModel):
    """Section response schema."""
    id: str
    document_id: str
    parent_id: Optional[str]
    title: str
    level: Optional[int]
    order: int
    content_blocks: List[ContentBlockResponse] = []
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    title: str
    source_filename: str
    file_path: Optional[str]
    doc_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    sections: List[SectionResponse] = []
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated document list response."""
    total: int
    skip: int
    limit: int
    documents: List[DocumentResponse]


class SearchRequest(BaseModel):
    """Search request schema."""
    query: str = Field(..., min_length=1, max_length=500)
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ProcessingStatus(BaseModel):
    """Document processing status."""
    status: str  # "processing", "completed", "failed"
    message: Optional[str]
    document_id: Optional[str]
    progress: Optional[int] = Field(default=0, ge=0, le=100)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    version: str
