import unittest
import json
import os
import shutil
from src.transformer import transform_to_nodes

class MockDoclingDoc:
    def __init__(self, data):
        self.data = data
        self.pictures = []

    def export_to_dict(self):
        return self.data

class TestTransformer(unittest.TestCase):
    def setUp(self):
        self.images_dir = "test_output/images"
        self.tables_dir = "test_output/tables"
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.tables_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")

    def test_hierarchy(self):
        # Create a mock document structure
        # Document
        #   Section 1 (H1)
        #     Text 1
        #     Section 1.1 (H2)
        #       Text 1.1
        #   Section 2 (H1)
        #     Text 2
        
        data = {
            "name": "Test Doc",
            "origin": {"filename": "test.pdf"},
            "body": {
                "children": [
                    {"$ref": "#/body/children/0"},
                    {"$ref": "#/body/children/1"},
                    {"$ref": "#/body/children/2"},
                    {"$ref": "#/body/children/3"},
                    {"$ref": "#/body/children/4"},
                    {"$ref": "#/body/children/5"},
                ]
            }
        }
        
        # We need to populate the data structure so resolve_ref works
        # This is a bit hacky but mimics the structure
        # We'll just put the elements in a list and map them
        
        elements = [
            {"label": "section_header", "text": "Section 1", "level": 1},
            {"label": "text", "text": "Text 1"},
            {"label": "section_header", "text": "Section 1.1", "level": 2},
            {"label": "text", "text": "Text 1.1"},
            {"label": "section_header", "text": "Section 2", "level": 1},
            {"label": "text", "text": "Text 2"},
        ]
        
        data["body"]["children"] = elements

        # Mock the resolve_ref logic by making the data structure match what the transformer expects
        # The transformer expects refs like #/body/children/0
        # And it resolves them by traversing the dict.
        # So we need to make sure data["body"]["children"][0] is the element.
        # Wait, the transformer iterates over body.children, which is a list of refs.
        # So I need to structure it correctly.
        
        refs = [{"$ref": f"#/body/elements/{i}"} for i in range(len(elements))]
        data["body"]["children"] = refs
        data["body"]["elements"] = elements

        doc = MockDoclingDoc(data)
        
        result = transform_to_nodes(doc, self.images_dir, self.tables_dir)
        
        # Verify structure
        self.assertEqual(result["title"], "Test Doc")
        self.assertEqual(len(result["children"]), 2) # Section 1, Section 2
        
        sec1 = result["children"][0]
        self.assertEqual(sec1["title"], "Section 1")
        self.assertEqual(len(sec1["children"]), 2) # Text 1, Section 1.1
        
        text1 = sec1["children"][0]
        self.assertEqual(text1["text"], "Text 1")
        
        sec1_1 = sec1["children"][1]
        self.assertEqual(sec1_1["title"], "Section 1.1")
        self.assertEqual(len(sec1_1["children"]), 1) # Text 1.1
        
        sec2 = result["children"][1]
        self.assertEqual(sec2["title"], "Section 2")
        self.assertEqual(len(sec2["children"]), 1) # Text 2

    def test_headers_footers(self):
        # Mock data with headers and footers
        elements = [
            {"label": "page_header", "text": "Header 1"},
            {"label": "text", "text": "Content 1"},
            {"label": "page_footer", "text": "Footer 1"},
            {"label": "page_header", "text": "Header 1"}, # Duplicate
            {"label": "text", "text": "Content 2"},
            {"label": "page_footer", "text": "Footer 2"},
        ]
        
        data = {
            "name": "Test Doc",
            "origin": {"filename": "test.pdf"},
            "body": {
                "children": [{"$ref": f"#/body/elements/{i}"} for i in range(len(elements))],
                "elements": elements
            }
        }
        
        doc = MockDoclingDoc(data)
        result = transform_to_nodes(doc, self.images_dir, self.tables_dir)
        
        # Verify headers/footers in root
        self.assertIn("page_headers", result)
        self.assertIn("page_footers", result)
        self.assertEqual(set(result["page_headers"]), {"Header 1"})
        self.assertEqual(set(result["page_footers"]), {"Footer 1", "Footer 2"})
        
        # Verify they are NOT in children
        self.assertEqual(len(result["children"]), 2) # Content 1, Content 2
        for child in result["children"]:
            self.assertNotEqual(child["type"], "page_header")
            self.assertNotEqual(child["type"], "page_footer")

    def test_table_merge(self):
        # Mock data with split tables
        # Table 1 (Page 1)
        # Table 1 (Page 2) - same columns
        
        elements = [
            {
                "label": "table", 
                "data": {
                    "grid": [
                        [{"text": "Col1"}, {"text": "Col2"}],
                        [{"text": "Val1"}, {"text": "Val2"}]
                    ]
                }
            },
            {
                "label": "page_footer", "text": "Footer 1"
            },
            {
                "label": "page_header", "text": "Header 2"
            },
            {
                "label": "table", 
                "data": {
                    "grid": [
                        [{"text": "Col1"}, {"text": "Col2"}], # Same columns
                        [{"text": "Val3"}, {"text": "Val4"}]
                    ]
                }
            }
        ]
        
        data = {
            "name": "Test Doc",
            "origin": {"filename": "test.pdf"},
            "body": {
                "children": [{"$ref": f"#/body/elements/{i}"} for i in range(len(elements))],
                "elements": elements
            }
        }
        
        doc = MockDoclingDoc(data)
        result = transform_to_nodes(doc, self.images_dir, self.tables_dir)
        
        # Verify merging
        # Should have 1 child (the merged table) - headers/footers are stripped
        self.assertEqual(len(result["children"]), 1)
        merged_table = result["children"][0]
        self.assertEqual(merged_table["type"], "table")
        
        # Verify rows: Header + Row1 + Row2
        # Note: My implementation appends rows. 
        # The first table has [Header, Row1].
        # The second table has [Header, Row2].
        # The merge logic appends the second table's rows (including header if present in grid).
        # Wait, my merge logic: last_table_node["rows"].extend(child["rows"])
        # And child["rows"] comes from table_data[1:] (excluding header).
        # So it should be fine!
        
        # Let's verify the CSV content or the node content
        # The node has "rows"
        self.assertEqual(len(merged_table["rows"]), 2) # Val1/Val2 and Val3/Val4
        self.assertEqual(merged_table["rows"][0], ["Val1", "Val2"])
        self.assertEqual(merged_table["rows"][1], ["Val3", "Val4"])

if __name__ == "__main__":
    unittest.main()
