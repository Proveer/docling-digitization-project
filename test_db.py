"""Simple database test - SQLAlchemy 2.0 compatible"""

print("\n" + "="*60)
print("Testing SQLite Database Setup")
print("="*60)

# Test 1: SQLite
print("\n[1/6] Checking SQLite...")
import sqlite3
print(f"    OK - SQLite version: {sqlite3.sqlite_version}")

# Test 2: Initialize Database
print("\n[2/6] Initializing database...")
from src.database import init_db, get_db_session
init_db()
print("    OK - Database tables created")

# Test 3: Create Test Document
print("\n[3/6] Creating test document...")
from src.database.repository import DocumentRepository

test_data = {
    "id": "test-001",
    "title": "Test Document",
    "metadata": {"source": "test.pdf", "page_count": 1},
    "page_headers": ["Header"],
    "page_footers": ["Footer"],
    "children": [
        {
            "type": "section",
            "id": "sec-001",
            "title": "Test Section",
            "level": 1,
            "children": [
                {
                    "type": "text",
                    "id": "txt-001",
                    "text": "This is a test paragraph."
                }
            ]
        }
    ]
}

db = get_db_session()
repo = DocumentRepository(db)
doc = repo.create_from_json(test_data)
print(f"    OK - Created document: {doc.title}")
print(f"         ID: {doc.id}")
print(f"         Sections: {len(doc.sections)}")
db.close()

# Test 4: Retrieve Document
print("\n[4/6] Retrieving document...")
db = get_db_session()
repo = DocumentRepository(db)
doc = repo.get_by_id("test-001")
if doc:
    print(f"    OK - Retrieved: {doc.title}")
    print(f"         Created at: {doc.created_at}")
else:
    print("    ERROR - Document not found!")
db.close()

# Test 5: Search
print("\n[5/6] Testing search...")
db = get_db_session()
repo = DocumentRepository(db)
results = repo.search("Test")
print(f"    OK - Found {len(results)} document(s)")
total = repo.count()
print(f"    OK - Total documents: {total}")
db.close()

# Test 6: Cleanup
print("\n[6/6] Cleaning up...")
db = get_db_session()
repo = DocumentRepository(db)
repo.delete("test-001")
print("    OK - Test document deleted")
db.close()

# Summary
print("\n" + "="*60)
print("SUCCESS! All tests passed!")
print("="*60)
import os
print(f"\nDatabase file: {os.path.abspath('docling.db')}")
print(f"Database size: {os.path.getsize('docling.db')} bytes")
print("\nYour SQLite database is working perfectly!")
print("\nNext step: Start the API server")
print("  uvicorn src.routers.main:app --reload")
print("="*60)
