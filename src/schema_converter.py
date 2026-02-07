import json
from typing import Dict, Any, List, Optional

def convert_to_relational(json_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Converts the hierarchical JSON output into a flat, relational structure.
    
    Returns:
        A dictionary with keys: 'documents', 'sections', 'content_blocks'.
    """
    documents = []
    sections = []
    content_blocks = []
    
    # 1. Process Document
    doc_id = json_data.get("id")
    
    # Add headers/footers to metadata
    doc_metadata = json_data.get("metadata", {})
    doc_metadata["headers"] = json_data.get("page_headers", [])
    doc_metadata["footers"] = json_data.get("page_footers", [])
    
    documents.append({
        "id": doc_id,
        "title": json_data.get("title"),
        "metadata": doc_metadata
    })
    
    # Helper for recursive traversal
    def traverse(node: Dict[str, Any], parent_section_id: Optional[str], current_section_id: Optional[str]):
        nonlocal sections, content_blocks
        
        children = node.get("children", [])
        
        for i, child in enumerate(children):
            child_type = child.get("type")
            child_id = child.get("id")
            
            if child_type == "section":
                # Create new section entry
                sections.append({
                    "id": child_id,
                    "document_id": doc_id,
                    "parent_id": parent_section_id, # Parent section (hierarchy)
                    "title": child.get("title"),
                    "order": i,
                    "metadata": child.get("metadata", {})
                })
                
                # Recurse with this section as the new parent
                traverse(child, child_id, child_id)
                
            else:
                # Content block (text, image, table, etc.)
                # It belongs to the current_section_id (which might be None if at root)
                content_blocks.append({
                    "id": child_id,
                    "document_id": doc_id,
                    "section_id": current_section_id,
                    "type": child_type,
                    "text": child.get("text"),
                    "src": child.get("src"),
                    "caption": child.get("caption"),
                    "metadata": child.get("metadata", {}),
                    "order": i
                })
                
                # Recurse (though content blocks usually don't have children in this model, 
                # but our transformer might nest them if we change logic later. 
                # Currently transformer puts children only in sections or root).
                if "children" in child:
                    traverse(child, parent_section_id, current_section_id)

    # Start traversal from root
    # Root is not a section, so parent_section_id is None, current_section_id is None
    traverse(json_data, None, None)
    
    return {
        "documents": documents,
        "sections": sections,
        "content_blocks": content_blocks
    }

def save_relational_json(data: Dict[str, List[Dict[str, Any]]], output_path: str):
    """Saves the relational data to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
