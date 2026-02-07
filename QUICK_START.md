# Quick Start Guide - Docling Digitization Project

## What is this project?

This is a **document digitization system** that converts unstructured documents (PDFs, Word docs, PowerPoint, etc.) into structured, searchable data stored in a database. It includes:

1. **API Server** (FastAPI) - Upload and manage documents via REST API
2. **CLI Tool** - Batch process documents from command line
3. **SQLite Database** - Stores documents in a hierarchical structure
4. **AI Integration** - Optional Gemini AI for table/image summarization

---

## Project Structure (Simplified)

```
docling-digitization-project/
│
├── .env.example          → Configuration template
├── PROJECT_OVERVIEW.md   → Complete documentation (READ THIS!)
├── README.md             → Quick start
├── API_README.md         → API documentation
│
├── data/                 → Put documents here for CLI processing
├── uploads/              → API uploads go here
├── output/               → Processed JSON, images, tables
│
├── src/
│   ├── database/         → Database models & operations
│   │   ├── models.py     → Document, Section, ContentBlock tables
│   │   ├── connection.py → Database connection (SQLite)
│   │   └── repository.py → Data access methods
│   │
│   ├── routers/          → API endpoints (FastAPI)
│   │   ├── main.py       → Main API app
│   │   ├── document_router.py → Upload, get, delete documents
│   │   └── search_router.py   → Search functionality
│   │
│   ├── resolvers/        → Business logic
│   ├── utilities/        → Helper functions
│   ├── ai/               → Gemini AI integration
│   │
│   ├── digitizer.py      → CLI tool for batch processing
│   └── transformer.py    → Converts documents to JSON
│
└── docling.db            → SQLite database file
```

---

## How It Works

### Processing Pipeline

```
1. Upload Document (PDF, DOCX, etc.)
         ↓
2. Docling extracts structure, text, images, tables
         ↓
3. Transform to hierarchical JSON
         ↓
4. (Optional) AI summarizes tables/images
         ↓
5. Store in SQLite database
         ↓
6. Return document ID for retrieval
```

### Database Structure

```
Document (e.g., "Annual Report 2024")
  ├── Section (e.g., "Chapter 1: Introduction")
  │     ├── ContentBlock (text: "This report covers...")
  │     ├── ContentBlock (table: sales_data.csv)
  │     └── ContentBlock (image: chart.png)
  │
  └── Section (e.g., "Chapter 2: Results")
        ├── Section (nested: "2.1 Revenue")
        │     └── ContentBlock (text: "Revenue increased...")
        └── ContentBlock (table: revenue_table.csv)
```

---

## Quick Start (5 Minutes)

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if you want AI features (optional)
# Add your Gemini API key to GEMINI_API_KEY=...
```

### 2. Start the API

```bash
# Make sure you're in the virtual environment
.venv\Scripts\activate  # Windows

# Start the server
uvicorn src.routers.main:app --reload
```

Visit: http://localhost:8000/docs (Interactive API documentation)

### 3. Upload a Document

**Option A: Via Web Interface**
- Go to http://localhost:8000/docs
- Click on `POST /api/v1/documents/upload`
- Click "Try it out"
- Upload a PDF file
- Click "Execute"

**Option B: Via Command Line**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@your_document.pdf"
```

**Option C: Via Python**
```python
import requests

with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        files={'file': f}
    )
    
doc = response.json()
print(f"Document ID: {doc['id']}")
```

### 4. Retrieve the Document

```bash
# Get document by ID (replace with your document ID)
curl http://localhost:8000/api/v1/documents/{document_id}
```

---

## Common Tasks

### Process Documents in Batch (CLI)

```bash
# Put PDFs in data/ folder
# Then run:
python src/digitizer.py
```

### Search Documents

```bash
# Search by title or filename
curl "http://localhost:8000/api/v1/search/documents?q=report"

# Get all tables
curl "http://localhost:8000/api/v1/search/tables"

# Get all images
curl "http://localhost:8000/api/v1/search/images"
```

### Access Database Directly

```python
from src.database import get_db_session
from src.database.models import Document

db = get_db_session()
try:
    # Get all documents
    docs = db.query(Document).all()
    for doc in docs:
        print(f"{doc.title} - {doc.created_at}")
finally:
    db.close()
```

---

## Key Files to Understand

### 1. **src/database/models.py**
Defines the database schema:
- `Document`: Top-level container
- `Section`: Hierarchical structure (chapters, sections)
- `ContentBlock`: Individual content (text, images, tables)

### 2. **src/database/repository.py**
Data access methods:
- `DocumentRepository.create_from_json()`: Create document from JSON
- `DocumentRepository.get_by_id()`: Retrieve document
- `DocumentRepository.search()`: Search documents
- `ContentRepository.search_by_type()`: Find all tables/images

### 3. **src/routers/document_router.py**
API endpoints:
- `POST /api/v1/documents/upload`: Upload document
- `GET /api/v1/documents`: List all documents
- `GET /api/v1/documents/{id}`: Get specific document
- `DELETE /api/v1/documents/{id}`: Delete document

### 4. **src/digitizer.py**
CLI tool for batch processing documents

### 5. **src/transformer.py**
Converts Docling output to hierarchical JSON

---

## Configuration (.env)

```bash
# Database (SQLite - no setup needed!)
DATABASE_URL=sqlite:///./docling.db

# AI Features (optional - get key from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_api_key_here

# API Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Troubleshooting

### Database not found?
The database is created automatically on first run. Just start the API and it will create `docling.db`.

### Can't upload files?
Check `MAX_FILE_SIZE_MB` in `.env` (default is 100MB).

### Want to use PostgreSQL instead?
1. Install: `pip install psycopg2-binary`
2. Update `.env`: `DATABASE_URL=postgresql://user:pass@localhost/dbname`
3. Restart API

---

## What's Next?

1. **Read PROJECT_OVERVIEW.md** for complete documentation
2. **Try the API** at http://localhost:8000/docs
3. **Process some documents** with the CLI tool
4. **Explore the database** structure in `docling.db`

---

## Architecture Summary

```
┌─────────────────────┐
│   Client (You)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   FastAPI Server    │  ← Handles HTTP requests
│   (src/routers/)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Business Logic     │  ← Processes documents
│  (src/resolvers/)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Utilities         │  ← Docling, file handling
│  (src/utilities/)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SQLite Database    │  ← Stores structured data
│  (docling.db)       │
└─────────────────────┘
```

---

## Need Help?

- **Full Documentation**: See `PROJECT_OVERVIEW.md`
- **API Reference**: Visit http://localhost:8000/docs
- **Database Schema**: See `src/database/models.py`
- **Examples**: See `PROJECT_OVERVIEW.md` → Usage Examples

---

**Remember**: All code now has comprehensive docstrings! Just open any Python file to see detailed explanations of what each function does.
