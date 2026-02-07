"""Search router."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from .schemas import DocumentResponse, ContentBlockResponse
from src.resolvers.search_resolver import SearchResolver

router = APIRouter()


@router.get("/documents", response_model=List[DocumentResponse])
async def search_documents(
    q: str = Query(..., min_length=1, max_length=500),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Search documents by title or filename.
    
    Returns a list of matching documents.
    """
    resolver = SearchResolver(db)
    return resolver.search_documents(query=q, skip=skip, limit=limit)


@router.get("/content", response_model=List[ContentBlockResponse])
async def search_content(
    q: str = Query(..., min_length=1, max_length=500),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Full-text search across all content blocks.
    
    Returns matching content blocks.
    """
    resolver = SearchResolver(db)
    return resolver.search_content(query=q, skip=skip, limit=limit)


@router.get("/tables", response_model=List[ContentBlockResponse])
async def search_tables(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get all table content blocks.
    
    Returns a list of tables.
    """
    resolver = SearchResolver(db)
    return resolver.get_tables(skip=skip, limit=limit)


@router.get("/images", response_model=List[ContentBlockResponse])
async def search_images(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get all image content blocks.
    
    Returns a list of images.
    """
    resolver = SearchResolver(db)
    return resolver.get_images(skip=skip, limit=limit)
