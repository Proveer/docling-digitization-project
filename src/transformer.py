import uuid
import json
import os
import csv
from typing import List, Dict, Any

def transform_to_nodes(docling_doc, images_dir: str, tables_dir: str) -> Dict[str, Any]:
    """
    Transforms the docling document into a hierarchical node structure.
    
    Args:
        docling_doc: The Docling document object.
        images_dir: Directory to save extracted images.
        tables_dir: Directory to save extracted tables.
        
    Returns:
        A dictionary representing the root document node with nested children.
    """
    
    # Export to dict to access the structure and elements easily
    doc_dict = docling_doc.export_to_dict()
    
    # Helper to resolve references in the JSON structure
    def resolve_ref(ref: str) -> Any:
        parts = ref.strip('#/').split('/')
        obj = doc_dict
        for part in parts:
            if isinstance(obj, list):
                obj = obj[int(part)]
            else:
                obj = obj.get(part)
        return obj

    # Create the root document node
    root_id = str(uuid.uuid4())
    root_node = {
        "id": root_id,
        "type": "document",
        "title": doc_dict.get("name", "Untitled Document"),
        "metadata": {
            "source": doc_dict.get("origin", {}).get("filename"),
            "page_count": 0 # Placeholder, could be calculated
        },
        "children": []
    }

    # Stack to maintain hierarchy: [(node, level)]
    # Root is level 0
    stack = [(root_node, 0)]

    # Get the body elements
    body_ref = doc_dict.get("body", {})
    if not body_ref:
        return root_node

    # We need to iterate linearly through the body's children
    # Docling's body.children is a list of refs
    child_refs = body_ref.get("children", [])
    
    # Sets to collect unique headers and footers
    headers = set()
    footers = set()

    for i, child_ref in enumerate(child_refs):
        element = resolve_ref(child_ref.get("$ref"))
        if not element:
            continue

        element_type = element.get("label")
        text_content = element.get("text", "").strip()
        
        # Skip empty text elements unless they are specific types
        if not text_content and element_type not in ["picture", "table", "image"]:
            continue

        # --- Handle Headers and Footers ---
        if element_type == "page_header":
            if text_content:
                headers.add(text_content)
            continue # Skip adding to children
            
        if element_type == "page_footer":
            if text_content:
                footers.add(text_content)
            continue # Skip adding to children

        node_id = str(uuid.uuid4())
        new_node = {
            "id": node_id,
            "type": element_type,
            "metadata": {}
        }

        # Add page number if available
        if element.get("prov") and len(element.get("prov")) > 0:
            new_node["metadata"]["page_no"] = element["prov"][0].get("page_no")

        # --- Handle Section Headers (Hierarchy) ---
        if element_type == "section_header":
            new_node["type"] = "section"
            new_node["title"] = text_content
            new_node["children"] = []
            
            # Determine level. Docling usually provides 'level' for headers.
            # If not found, default to 1.
            level = element.get("level", 1)
            
            # Pop stack until we find a parent with level < current level
            while len(stack) > 1 and stack[-1][1] >= level:
                stack.pop()
            
            # Add to the current parent
            parent_node = stack[-1][0]
            parent_node["children"].append(new_node)
            
            # Push this new section to stack
            stack.append((new_node, level))

        # --- Handle Text/Code/Captions ---
        elif element_type in ["text", "code", "caption", "paragraph", "list_item"]:
            new_node["text"] = text_content
            # Add to current parent (do not push to stack)
            stack[-1][0]["children"].append(new_node)

        # --- Handle Images ---
        elif element_type == "picture":
            new_node["type"] = "image"
            
            # Try to find and save the image
            saved_image = False
            if hasattr(docling_doc, "pictures"):
                for pic in docling_doc.pictures:
                    # We compare self_ref
                    if pic.self_ref == element.get("self_ref"):
                        try:
                            image = pic.get_image(doc=docling_doc)
                            if image:
                                image_filename = f"{node_id}.png"
                                image_path = os.path.join(images_dir, image_filename)
                                image.save(image_path)
                                new_node["src"] = os.path.join("images", image_filename).replace("\\", "/")
                                saved_image = True
                        except Exception as e:
                            print(f"ERROR: Could not process image {node_id}: {e}")
                        break
            
            if not saved_image:
                print(f"WARNING: Image {node_id} was not saved (no matching picture found)")
            
            # Handle captions for images
            captions = [resolve_ref(c['$ref']).get('text') for c in element.get("captions", [])]
            if captions:
                new_node["caption"] = " ".join(captions)
                
            stack[-1][0]["children"].append(new_node)

        # --- Handle Tables ---
        elif element_type == "table":
            new_node["type"] = "table"
            
            # Handle captions for tables
            captions = [resolve_ref(c['$ref']).get('text') for c in element.get("captions", [])]
            if captions:
                new_node["caption"] = " ".join(captions)

            # Extract table data
            if "data" in element and "grid" in element["data"]:
                grid = element["data"]["grid"]
                if grid:
                    # Extract headers and rows
                    # Assuming first row is header, but this might vary. 
                    # For simplicity, we take the grid as is.
                    # Grid is list of lists of cells. Cell has 'text'.
                    
                    table_data = [[cell["text"] for cell in row] for row in grid]
                    
                    if table_data:
                        new_node["columns"] = table_data[0]
                        new_node["rows"] = table_data[1:]
                        
                        # Save as CSV
                        table_filename = f"{node_id}.csv"
                        table_path = os.path.join(tables_dir, table_filename)
                        with open(table_path, "w", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerows(table_data)
                        
                        new_node["src"] = os.path.join("tables", table_filename).replace("\\", "/")

            stack[-1][0]["children"].append(new_node)
            
        # --- Handle Other Types ---
        else:
            # Generic fallback
            new_node["text"] = text_content
            stack[-1][0]["children"].append(new_node)

    # Add collected headers and footers to root node
    root_node["page_headers"] = list(headers)
    root_node["page_footers"] = list(footers)

    # --- Post-processing: Merge split tables ---
    merge_tables(root_node, tables_dir)

    return root_node

def merge_tables(node: Dict[str, Any], tables_dir: str):
    """
    Recursively merges split tables in the node tree.
    Tables are considered split if they are adjacent (ignoring page headers/footers)
    and have identical columns.
    """
    if "children" not in node:
        return

    children = node["children"]
    if not children:
        return

    # We will rebuild the children list
    new_children = []
    last_table_node = None
    
    for child in children:
        # Recursively process children first
        merge_tables(child, tables_dir)
        
        is_merged = False
        
        if child["type"] == "table" and "columns" in child:
            if last_table_node:
                # Check if we can merge with the last table
                # We need to ensure that we haven't encountered any "content" nodes since the last table.
                # Since we removed headers/footers from children, adjacent tables should be truly adjacent now.
                
                # Check columns match
                if child.get("columns") == last_table_node.get("columns"):
                    # Merge!
                    # 1. Append rows
                    last_table_node["rows"].extend(child["rows"])
                    
                    # 2. Update CSV
                    try:
                        # Read existing CSV of last_table
                        last_csv_path = os.path.join(tables_dir, os.path.basename(last_table_node["src"]))
                        
                        # Append new rows to CSV
                        with open(last_csv_path, "a", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerows(child["rows"])
                            
                        # Delete the second table's CSV
                        child_csv_path = os.path.join(tables_dir, os.path.basename(child["src"]))
                        if os.path.exists(child_csv_path):
                            os.remove(child_csv_path)
                            
                        is_merged = True
                        
                    except Exception as e:
                        print(f"Error merging tables: {e}")
            
            if not is_merged:
                last_table_node = child
                new_children.append(child)
            
        else:
            # Other content (text, section, image, etc.) -> breaks the merge chain
            last_table_node = None
            new_children.append(child)
            
    node["children"] = new_children


