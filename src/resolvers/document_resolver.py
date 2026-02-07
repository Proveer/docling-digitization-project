"""Document processing service (resolver)."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from src.database.models import Document
from src.database.repository import DocumentRepository
from src.utilities.docling_processor import DoclingProcessor
from src.utilities.file_handler import save_uploaded_file, cleanup_file
from src.ai.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


class DocumentResolver:
    """Service for document processing operations."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.repo = DocumentRepository(db_session)
        self.processor = DoclingProcessor()
        self.ai_client = get_gemini_client()
    
    async def process_uploaded_document(
        self,
        file_content: bytes,
        filename: str,
        upload_dir: Path
    ) -> Dict[str, Any]:
        """
        Process an uploaded document file.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            upload_dir: Directory to save uploaded file
            
        Returns:
            Processing status dict
        """
        file_path = None
        try:
            # Save uploaded file
            file_path = await save_uploaded_file(file_content, filename, upload_dir)
            logger.info(f"File saved to {file_path}")
            
            # Process document with Docling
            hierarchical_json = self.processor.process_document(file_path)
            
            # Enhance with AI summaries if enabled
            if self.ai_client.enabled:
                hierarchical_json = await self._add_ai_summaries(hierarchical_json)
            
            # Save to database
            document = self.repo.create_from_json(hierarchical_json)
            logger.info(f"Document {document.id} saved to database")
            
            return {
                "status": "completed",
                "message": "Document processed successfully",
                "document_id": document.id,
                "progress": 100
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            return {
                "status": "failed",
                "message": str(e),
                "document_id": None,
                "progress": 0
            }
        finally:
            # Cleanup uploaded file
            if file_path:
                cleanup_file(file_path)
    
    async def _add_ai_summaries(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add AI-generated summaries to content blocks."""
        
        def process_children(children):
            """Recursively process children and add AI summaries."""
            for child in children:
                child_type = child.get("type")
                
                # Process tables
                if child_type == "table" and child.get("src"):
                    try:
                        # Read CSV file (src already includes document folder)
                        csv_path = Path("output") / child["src"]
                        if csv_path.exists():
                            csv_data = csv_path.read_text(encoding="utf-8")
                            summary = self.ai_client.summarize_table(
                                csv_data,
                                caption=child.get("caption")
                            )
                            if summary:
                                if "metadata" not in child:
                                    child["metadata"] = {}
                                child["metadata"]["ai_summary"] = summary
                    except Exception as e:
                        logger.error(f"Failed to summarize table: {e}")
                
                # Process images
                elif child_type == "image" and child.get("src"):
                    try:
                        # Image path (src already includes document folder)
                        image_path = Path("output") / child["src"]
                        if image_path.exists():
                            description = self.ai_client.describe_image(
                                str(image_path),
                                caption=child.get("caption")
                            )
                            if description:
                                if "metadata" not in child:
                                    child["metadata"] = {}
                                child["metadata"]["ai_description"] = description
                    except Exception as e:
                        logger.error(f"Failed to describe image: {e}")
                
                # Recursively process nested children
                if "children" in child:
                    process_children(child["children"])
        
        # Process all children
        if "children" in json_data:
            process_children(json_data["children"])
        
        return json_data
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.repo.get_by_id(document_id)
    
    def list_documents(self, skip: int = 0, limit: int = 100):
        """List documents with pagination."""
        documents = self.repo.list_all(skip=skip, limit=limit)
        total = self.repo.count()
        return {"documents": documents, "total": total}
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document by ID."""
        return self.repo.delete(document_id)
    
    def search_documents(self, query: str, skip: int = 0, limit: int = 100):
        """Search documents."""
        return self.repo.search(query=query, skip=skip, limit=limit)
