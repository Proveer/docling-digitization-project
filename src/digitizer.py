"""Minimal document digitization script with GPU support."""

import argparse
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        return iterable

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat
except ImportError:
    DocumentConverter = None
    PdfFormatOption = None
    PdfPipelineOptions = None
    InputFormat = None

# Import the transformer logic
from transformer import transform_to_nodes
from schema_converter import convert_to_relational, save_relational_json

DEFAULT_INPUT_DIR = Path("data")
DEFAULT_OUTPUT_DIR = Path("output")
ALLOWED_EXTS = {
    ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".txt", ".md",
    ".html", ".htm", ".jpg", ".jpeg", ".png", ".tif", ".tiff"
}

def create_argument_parser() -> argparse.ArgumentParser:
    """Creates and configures the argument parser for the script."""
    parser = argparse.ArgumentParser(description="Digitize documents using DocumentConverter.")
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Paths to input files or directories. Overrides config.json."
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to the configuration file."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Path to the output directory."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process all files in input directories, regardless of extension."
    )
    return parser

def load_config(config_path: str) -> dict:
    """Loads the configuration from a JSON file."""
    path = Path(config_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def discover_input_files(
    cli_inputs: list[str],
    config: dict,
    force: bool
) -> list[Path]:
    """
    Discovers input files from CLI arguments, config file, or the default data directory.
    """
    paths_to_process = []
    if cli_inputs:
        for path_str in cli_inputs:
            path = Path(path_str).expanduser()
            if path.is_dir():
                paths_to_process.extend(
                    p for p in path.iterdir()
                    if force or p.suffix.lower() in ALLOWED_EXTS
                )
            elif force or path.suffix.lower() in ALLOWED_EXTS:
                paths_to_process.append(path)
    else:
        config_files = config.get("input_files", [])
        if config_files:
            for file_str in config_files:
                path = Path(file_str)
                if force or path.suffix.lower() in ALLOWED_EXTS:
                    paths_to_process.append(path)
        elif DEFAULT_INPUT_DIR.exists():
            paths_to_process.extend(
                p for p in DEFAULT_INPUT_DIR.iterdir()
                if force or p.suffix.lower() in ALLOWED_EXTS
            )
    return sorted(list(set(paths_to_process)))

def print_diagnostics():
    """Prints diagnostic information about the environment."""
    try:
        import torch
        logger.info(f"PyTorch Version: {torch.__version__}")
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            logger.info(f"CUDA Available: YES ({device_count} devices)")
            logger.info(f"Current Device: {device_name}")
        else:
            logger.warning("CUDA Available: NO (Using CPU)")
            logger.warning("To enable GPU, please install PyTorch with CUDA support.")
    except ImportError:
        logger.error("PyTorch is not installed.")
    except Exception as e:
        logger.error(f"Error getting CUDA info: {e}")

def initialize_converter() -> Optional["DocumentConverter"]:
    """Initializes and returns the DocumentConverter."""
    if DocumentConverter is None:
        logger.error("`docling` library not found. Please install it to run the digitizer.")
        return None
    try:
        # Configure PDF pipeline to generate images
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = True
        
        # Docling automatically detects the best available device (CUDA/MPS/CPU).
        # We rely on its internal logic, which checks torch.cuda.is_available().
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize DocumentConverter: {e}")
        return None

def process_file(
    file_path: Path,
    converter: DocumentConverter,
    output_dir: Path
):
    """Processes a single file and saves the output."""
    start_time = time.time()
    try:
        # 1. Convert using Docling
        result = converter.convert(str(file_path))
        
        # 2. Create document-specific output folder
        doc_name = file_path.stem
        doc_output_dir = output_dir / doc_name
        images_dir = doc_output_dir / "images"
        tables_dir = doc_output_dir / "tables"
        
        # Create directories
        images_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. Transform to hierarchical JSON
        hierarchical_json = transform_to_nodes(
            result.document,
            str(images_dir),
            str(tables_dir)
        )
        
        # 4. Update asset paths to include document folder
        _update_asset_paths(hierarchical_json, doc_name)
        
        # 5. Save hierarchical JSON
        json_output_path = doc_output_dir / f"{doc_name}.json"
        with json_output_path.open("w", encoding="utf-8") as f:
            json.dump(hierarchical_json, f, indent=2, ensure_ascii=False)
        
        # 6. Convert to relational schema
        relational_json = convert_to_relational(hierarchical_json)
        
        # 7. Save relational JSON
        relational_output_path = doc_output_dir / f"{doc_name}_relational.json"
        save_relational_json(relational_json, str(relational_output_path))
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Processed {file_path.name} in {elapsed:.2f}s")
        logger.info(f"  → Output: {doc_output_dir}")
        
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {e}")


def _update_asset_paths(json_data: dict, doc_name: str):
    """Update asset paths to include document folder."""
    
    def update_children(children):
        for child in children:
            if child.get("src"):
                src = child["src"]
                if not src.startswith(doc_name):
                    child["src"] = f"{doc_name}/{src}"
            
            if "children" in child:
                update_children(child["children"])
    
    if "children" in json_data:
        update_children(json_data["children"])
        # import traceback
        # traceback.print_exc()

def main():
    """Main function to run the digitization process."""
    parser = create_argument_parser()
    args = parser.parse_args()

    config = load_config(args.config)
    input_files = discover_input_files(args.inputs, config, args.force)

    if not input_files:
        logger.warning("No input files found. Exiting.")
        return

    print_diagnostics()

    logger.info("Initializing DocumentConverter...")
    converter = initialize_converter()
    if converter is None:
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting processing of {len(input_files)} files...")
    
    # Use tqdm for progress bar
    for file_path in tqdm(input_files, desc="Processing Files", unit="file"):
        process_file(file_path, converter, output_dir)
        
    logger.info("All tasks completed.")

if __name__ == "__main__":
    main()