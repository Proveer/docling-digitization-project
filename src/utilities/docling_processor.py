"""Docling document processor utility."""

import os
from pathlib import Path
from typing import Dict, Any
import logging

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

from src.transformer import transform_to_nodes

logger = logging.getLogger(__name__)

# Base output directory
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))


class DoclingProcessor:
    """Utility class for processing documents with Docling."""
    
    def __init__(self):
        """Initialize Docling converter."""
        self.converter = self._initialize_converter()
        
        # Ensure base output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _initialize_converter(self) -> DocumentConverter:
        """Initialize DocumentConverter with proper configuration."""
        try:
            # Configure PDF pipeline to generate images
            pipeline_options = PdfPipelineOptions()
            pipeline_options.generate_picture_images = True
            
            return DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize DocumentConverter: {e}")
            raise
    
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a document file and return hierarchical JSON.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Hierarchical JSON structure with document-specific output paths
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Create document-specific output folder
            doc_name = file_path.stem  # Filename without extension
            doc_output_dir = OUTPUT_DIR / doc_name
            images_dir = doc_output_dir / "images"
            tables_dir = doc_output_dir / "tables"
            
            # Create directories
            images_dir.mkdir(parents=True, exist_ok=True)
            tables_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Output directory: {doc_output_dir}")
            
            # Convert document
            result = self.converter.convert(str(file_path))
            
            # Transform to hierarchical JSON
            hierarchical_json = transform_to_nodes(
                result.document,
                str(images_dir),
                str(tables_dir)
            )
            
            # Update paths in JSON to be relative to output root
            # (images/file.png -> document_name/images/file.png)
            self._update_asset_paths(hierarchical_json, doc_name)
            
            logger.info(f"Document processed successfully: {hierarchical_json.get('id')}")
            return hierarchical_json
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    def _update_asset_paths(self, json_data: Dict[str, Any], doc_name: str):
        """Update asset paths to include document folder."""
        
        def update_children(children):
            for child in children:
                # Update image/table src paths
                if child.get("src"):
                    # Convert: images/abc.png -> doc_name/images/abc.png
                    src = child["src"]
                    if not src.startswith(doc_name):
                        child["src"] = f"{doc_name}/{src}"
                
                # Recursively process nested children
                if "children" in child:
                    update_children(child["children"])
        
        if "children" in json_data:
            update_children(json_data["children"])

