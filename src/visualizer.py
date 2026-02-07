import json
import argparse
import os
from pathlib import Path

def json_to_html(node, level=0):
    """Recursively converts a JSON node to an HTML string."""
    
    node_type = node.get("type", "unknown")
    text = node.get("text", "")
    title = node.get("title", "")
    src = node.get("src", "")
    caption = node.get("caption", "")
    children = node.get("children", [])
    
    indent = "  " * level
    html = f'{indent}<div class="node node-{node_type}">\n'
    
    # Header for the node
    html += f'{indent}  <div class="node-header">\n'
    html += f'{indent}    <span class="badge">{node_type}</span>\n'
    
    if title:
        html += f'{indent}    <span class="title">{title}</span>\n'
    if text:
        # Truncate long text for preview
        preview = text[:100] + "..." if len(text) > 100 else text
        html += f'{indent}    <span class="text-preview">{preview}</span>\n'
        
    html += f'{indent}  </div>\n'
    
    # Content details
    html += f'{indent}  <div class="node-content">\n'
    if text and len(text) > 100:
        html += f'{indent}    <p class="full-text">{text}</p>\n'
        
    if src:
        if node_type == "image":
            html += f'{indent}    <img src="{src}" alt="Extracted Image" style="max-width: 300px;">\n'
        elif node_type == "table":
            html += f'{indent}    <p><a href="{src}" target="_blank">View Table CSV</a></p>\n'
            
    if caption:
        html += f'{indent}    <p class="caption">Caption: {caption}</p>\n'
        
    html += f'{indent}  </div>\n'
    
    # Children
    if children:
        html += f'{indent}  <div class="children">\n'
        for child in children:
            html += json_to_html(child, level + 1)
        html += f'{indent}  </div>\n'
        
    html += f'{indent}</div>\n'
    
    return html

def relational_to_html_tables(relational_data):
    """Converts relational JSON to HTML tables."""
    
    html = ""
    
    # Documents Table
    if "documents" in relational_data:
        html += '<h2>Documents</h2>\n'
        html += '<table class="relational-table">\n'
        html += '<thead><tr><th>ID</th><th>Title</th><th>Metadata</th></tr></thead>\n<tbody>\n'
        for doc in relational_data["documents"]:
            metadata_str = json.dumps(doc.get("metadata", {}), indent=2)
            html += f'<tr><td>{doc.get("id", "")[:8]}...</td><td>{doc.get("title", "")}</td><td><pre>{metadata_str}</pre></td></tr>\n'
        html += '</tbody></table>\n'
    
    # Sections Table
    if "sections" in relational_data:
        html += '<h2>Sections</h2>\n'
        html += '<table class="relational-table">\n'
        html += '<thead><tr><th>ID</th><th>Document ID</th><th>Parent ID</th><th>Title</th><th>Order</th></tr></thead>\n<tbody>\n'
        for section in relational_data["sections"][:50]:  # Limit to first 50
            parent_id = section.get("parent_id") or "None"
            if parent_id != "None":
                parent_id = parent_id[:8] + "..."
            html += f'<tr><td>{section.get("id", "")[:8]}...</td><td>{section.get("document_id", "")[:8]}...</td><td>{parent_id}</td><td>{section.get("title", "")}</td><td>{section.get("order", "")}</td></tr>\n'
        if len(relational_data["sections"]) > 50:
            html += f'<tr><td colspan="5"><em>... and {len(relational_data["sections"]) - 50} more sections</em></td></tr>\n'
        html += '</tbody></table>\n'
    
    # Content Blocks Table
    if "content_blocks" in relational_data:
        html += '<h2>Content Blocks</h2>\n'
        html += '<table class="relational-table">\n'
        html += '<thead><tr><th>ID</th><th>Section ID</th><th>Type</th><th>Text Preview</th><th>Order</th></tr></thead>\n<tbody>\n'
        for block in relational_data["content_blocks"][:100]:  # Limit to first 100
            text = block.get("text", "")
            text_preview = text[:50] + "..." if text and len(text) > 50 else text or ""
            section_id = block.get("section_id") or "None"
            if section_id != "None":
                section_id = section_id[:8] + "..."
            html += f'<tr><td>{block.get("id", "")[:8]}...</td><td>{section_id}</td><td>{block.get("type", "")}</td><td>{text_preview}</td><td>{block.get("order", "")}</td></tr>\n'
        if len(relational_data["content_blocks"]) > 100:
            html += f'<tr><td colspan="5"><em>... and {len(relational_data["content_blocks"]) - 100} more content blocks</em></td></tr>\n'
        html += '</tbody></table>\n'
    
    return html

def generate_html_preview(json_path: str, output_path: str):
    """Generates a standalone HTML file to visualize the JSON."""
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check if this is a relational JSON
    is_relational = "documents" in data and "sections" in data and "content_blocks" in data
    
    # Try to load relational version if it exists
    relational_data = None
    relational_path = Path(json_path).parent / f"{Path(json_path).stem}_relational.json"
    if not is_relational and relational_path.exists():
        try:
            with open(relational_path, "r", encoding="utf-8") as f:
                relational_data = json.load(f)
        except:
            pass
    
    # Generate hierarchical view
    hierarchical_html = json_to_html(data) if not is_relational else "<p>No hierarchical data available.</p>"
    
    # Generate relational view
    if is_relational:
        relational_html = relational_to_html_tables(data)
    elif relational_data:
        relational_html = relational_to_html_tables(relational_data)
    else:
        relational_html = "<p>No relational data available. Run the digitizer to generate the *_relational.json file.</p>"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JSON Visualization: {Path(json_path).name}</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f4f4f9; padding: 20px; margin: 0; }}
        
        /* Tabs */
        .tabs {{ display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #ddd; }}
        .tab {{ padding: 10px 20px; cursor: pointer; background: #fff; border: 1px solid #ddd; border-bottom: none; border-radius: 4px 4px 0 0; }}
        .tab.active {{ background: #6200ea; color: white; font-weight: bold; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        /* Hierarchical View */
        .node {{ margin: 10px 0; border-left: 2px solid #ddd; padding-left: 15px; }}
        .node-header {{ display: flex; align-items: center; gap: 10px; cursor: pointer; background: #fff; padding: 5px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .badge {{ background: #6200ea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; text-transform: uppercase; }}
        .node-section > .node-header .badge {{ background: #d50000; }}
        .node-image > .node-header .badge {{ background: #00c853; }}
        .node-table > .node-header .badge {{ background: #ff6d00; }}
        .title {{ font-weight: bold; color: #333; }}
        .text-preview {{ color: #666; font-style: italic; }}
        .node-content {{ margin-top: 5px; display: none; padding: 10px; background: #fff; border: 1px solid #eee; }}
        .children {{ margin-left: 20px; }}
        .full-text {{ white-space: pre-wrap; }}
        .caption {{ font-weight: bold; color: #555; }}
        .node.expanded > .node-content {{ display: block; }}
        
        /* Relational View */
        .relational-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .relational-table th {{ background: #6200ea; color: white; padding: 10px; text-align: left; }}
        .relational-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .relational-table tr:hover {{ background: #f9f9f9; }}
        .relational-table pre {{ margin: 0; font-size: 0.85em; max-width: 300px; overflow: auto; }}
        
        button {{ padding: 8px 16px; margin: 5px; cursor: pointer; background: #6200ea; color: white; border: none; border-radius: 4px; }}
        button:hover {{ background: #4a00b0; }}
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Tab switching
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            
            tabs.forEach(tab => {{
                tab.addEventListener('click', function() {{
                    const target = this.getAttribute('data-tab');
                    
                    tabs.forEach(t => t.classList.remove('active'));
                    tabContents.forEach(tc => tc.classList.remove('active'));
                    
                    this.classList.add('active');
                    document.getElementById(target).classList.add('active');
                }});
            }});
            
            // Hierarchical tree toggle
            const headers = document.querySelectorAll('.node-header');
            headers.forEach(header => {{
                header.addEventListener('click', function() {{
                    this.parentElement.classList.toggle('expanded');
                }});
            }});
            
            // Expand root by default
            const rootNode = document.querySelector('.node');
            if (rootNode) rootNode.classList.add('expanded');
        }});
        
        function expandAll() {{
            document.querySelectorAll('.node').forEach(n => n.classList.add('expanded'));
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.node').forEach(n => n.classList.remove('expanded'));
        }}
    </script>
</head>
<body>
    <h1>Document Visualization</h1>
    <p>Source: {json_path}</p>
    
    <div class="tabs">
        <div class="tab active" data-tab="hierarchical">Hierarchical View</div>
        <div class="tab" data-tab="relational">Relational Schema</div>
    </div>
    
    <div id="hierarchical" class="tab-content active">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <hr>
        {hierarchical_html}
    </div>
    
    <div id="relational" class="tab-content">
        {relational_html}
    </div>
</body>
</html>
    """
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML preview generated at: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize JSON output as HTML.")
    parser.add_argument("input", help="Path to the JSON file.")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = input_path.with_suffix(".html")
    
    generate_html_preview(str(input_path), str(output_path))
