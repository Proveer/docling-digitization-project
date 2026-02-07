"""Document management router."""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from src.database import get_db
from .schemas import DocumentResponse, DocumentListResponse, ProcessingStatus
from src.resolvers.document_resolver import DocumentResolver
from src.utilities.file_handler import validate_file_extension, get_file_size_mb

router = APIRouter()

# Configuration
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 100))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".doc", ".ppt"}


async def process_document_background(
    file_content: bytes,
    filename: str,
    db: Session
):
    """Background task to process uploaded document."""
    resolver = DocumentResolver(db)
    await resolver.process_uploaded_document(file_content, filename, UPLOAD_DIR)


@router.post("/upload", response_model=ProcessingStatus)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document.
    
    The document will be processed in the background.
    Returns a processing status with document ID.
    """
    # Validate file extension
    if not validate_file_extension(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {ALLOWED_EXTENSIONS}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB"
        )
    
    # Add background task
    background_tasks.add_task(
        process_document_background,
        file_content,
        file.filename,
        db
    )
    
    return ProcessingStatus(
        status="processing",
        message="Document uploaded successfully. Processing in background.",
        document_id=None,  # Will be set after processing
        progress=0
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Get a document by ID.
    
    Returns the complete document with all sections and content blocks.
    """
    resolver = DocumentResolver(db)
    document = resolver.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all documents with pagination.
    
    Returns a paginated list of documents.
    """
    resolver = DocumentResolver(db)
    result = resolver.list_documents(skip=skip, limit=limit)
    
    return DocumentListResponse(
        total=result["total"],
        skip=skip,
        limit=limit,
        documents=result["documents"]
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document by ID.
    
    Deletes the document and all its related data from the database.
    """
    resolver = DocumentResolver(db)
    success = resolver.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/export")
async def export_document(
    document_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Export a document in various formats.
    
    Supported formats: json, markdown
    """
    resolver = DocumentResolver(db)
    document = resolver.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if format == "json":
        return document
    elif format == "markdown":
        # TODO: Implement markdown export
        raise HTTPException(status_code=501, detail="Markdown export not yet implemented")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
