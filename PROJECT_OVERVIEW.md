# Docling Digitization Project - Complete Overview

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Core Components](#core-components)
8. [Getting Started](#getting-started)
9. [Usage Examples](#usage-examples)
10. [Configuration](#configuration)
11. [Development Guide](#development-guide)

---

## 🎯 Project Overview

The **Docling Digitization Project** is an API-driven document processing system that converts unstructured documents (PDF, DOCX, PPTX, HTML, images) into structured, searchable data with AI-powered enhancements.

### Key Features

- **Multi-Format Support**: Process PDF, DOCX, PPTX, HTML, and image files
- **Hierarchical Structure**: Maintains document structure (sections, subsections)
- **Content Extraction**: Extracts text, images, and tables
- **AI Summarization**: Uses Google Gemini AI for table and image descriptions
- **RESTful API**: FastAPI-based API for document upload, search, and retrieval
- **SQLite Database**: Lightweight, file-based database (easily upgradable to PostgreSQL/MySQL)
- **Automatic Processing**: Converts documents to structured JSON with metadata

### Use Cases

- **Document Management Systems**: Store and search large document collections
- **Data Extraction**: Extract structured data from unstructured documents
- **Content Analysis**: Analyze document structure and content
- **Knowledge Bases**: Build searchable knowledge repositories
- **Research Tools**: Process academic papers and research documents

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  (Web UI, Mobile App, CLI, External Services)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Document   │  │    Search    │  │    Health    │     │
│  │    Router    │  │    Router    │  │    Router    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                      │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  Document Resolver   │  │   Search Resolver    │        │
│  └──────────┬───────────┘  └──────────┬───────────┘        │
└─────────────┼──────────────────────────┼─────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Utilities Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Docling    │  │     File     │  │    Gemini    │     │
│  │  Processor   │  │   Handler    │  │     AI       │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │   SQLite Database    │  │   File Storage       │        │
│  │  (Documents, Sections│  │  (Uploads, Output)   │        │
│  │   ContentBlocks)     │  │                      │        │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Processing Pipeline

```
Document Upload
      │
      ▼
File Validation & Storage
      │
      ▼
Docling Processing
(Extract structure, text, images, tables)
      │
      ▼
Transform to Hierarchical JSON
      │
      ▼
AI Enhancement (Optional)
(Gemini summarizes tables/images)
      │
      ▼
Store in Database
(Documents → Sections → ContentBlocks)
      │
      ▼
Return Document ID & Metadata
```

---

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI**: Modern, high-performance web framework
- **Python 3.8+**: Core programming language
- **Uvicorn**: ASGI server for running the API

### Document Processing
- **Docling**: Document conversion library (PDF, DOCX, PPTX, etc.)
- **PIL/Pillow**: Image processing
- **CSV**: Table data handling

### Database
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Default database (file-based, zero-config)
- **PostgreSQL/MySQL**: Optional production databases

### AI/ML
- **Google Gemini AI**: Image and table summarization
- **google-generativeai**: Gemini API client

### Development Tools
- **python-dotenv**: Environment variable management
- **python-multipart**: File upload handling
- **tqdm**: Progress bars for batch processing

---

## 📁 Project Structure

```
docling-digitization-project/
│
├── .env                      # Environment variables (not in git)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # Quick start guide
├── API_README.md             # API documentation
├── PROJECT_OVERVIEW.md       # This file
├── requirements.txt          # Python dependencies
├── config.json               # Application configuration
│
├── data/                     # Input documents (place files here)
├── uploads/                  # Uploaded files via API
├── output/                   # Processed output (JSON, images, tables)
│   └── {document_id}/
│       ├── {document_id}.json
│       ├── images/
│       └── tables/
│
├── src/                      # Source code
│   ├── __init__.py
│   │
│   ├── database/             # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py     # DB connection & session management
│   │   ├── models.py         # SQLAlchemy models
│   │   └── repository.py     # Data access patterns
│   │
│   ├── routers/              # API routes (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app & configuration
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── document_router.py # Document endpoints
│   │   ├── search_router.py   # Search endpoints
│   │   └── health_router.py   # Health check endpoint
│   │
│   ├── resolvers/            # Business logic
│   │   ├── __init__.py
│   │   ├── document_resolver.py # Document processing logic
│   │   └── search_resolver.py   # Search logic
│   │
│   ├── utilities/            # Helper modules
│   │   ├── __init__.py
│   │   ├── docling_processor.py # Docling integration
│   │   └── file_handler.py      # File operations
│   │
│   ├── ai/                   # AI integration
│   │   ├── __init__.py
│   │   └── gemini_client.py  # Gemini AI client
│   │
│   ├── digitizer.py          # Standalone CLI script
│   ├── transformer.py        # JSON transformation logic
│   ├── schema_converter.py   # Schema conversion utilities
│   └── visualizer.py         # Visualization tools
│
├── tests/                    # Unit tests
│   └── test_transformer.py
│
└── docling.db                # SQLite database file
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────┐
│       Document          │
│─────────────────────────│
│ id (PK)                 │
│ title                   │
│ source_filename         │
│ file_path               │
│ doc_metadata (JSON)     │
│ created_at              │
│ updated_at              │
└───────────┬─────────────┘
            │
            │ 1:N
            │
            ▼
┌─────────────────────────┐
│       Section           │
│─────────────────────────│
│ id (PK)                 │
│ document_id (FK)        │◄────┐
│ parent_id (FK)          │─────┘ (self-referencing)
│ title                   │
│ level                   │
│ order                   │
└───────────┬─────────────┘
            │
            │ 1:N
            │
            ▼
┌─────────────────────────┐
│     ContentBlock        │
│─────────────────────────│
│ id (PK)                 │
│ section_id (FK)         │
│ type                    │
│ text                    │
│ src                     │
│ block_metadata (JSON)   │
│ order                   │
│ created_at              │
└─────────────────────────┘
```

### Table Descriptions

#### **documents**
Top-level container for processed files.

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| title | VARCHAR(500) | Document title |
| source_filename | VARCHAR(500) | Original filename |
| file_path | VARCHAR(1000) | Path to stored file |
| doc_metadata | JSON | Page headers, footers, page count |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**Indexes**: `idx_document_title`, `idx_document_created_at`

#### **sections**
Hierarchical document structure (chapters, sections, subsections).

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| document_id | VARCHAR(36) | Foreign key to documents |
| parent_id | VARCHAR(36) | Foreign key to parent section (nullable) |
| title | VARCHAR(1000) | Section heading |
| level | INTEGER | Hierarchy level (1, 2, 3...) |
| order | INTEGER | Position within parent |

**Indexes**: `idx_section_document_id`, `idx_section_parent_id`, `idx_section_order`

#### **content_blocks**
Individual content elements (text, images, tables).

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| section_id | VARCHAR(36) | Foreign key to sections (nullable) |
| type | VARCHAR(50) | Content type (text, image, table) |
| text | TEXT | Text content |
| src | VARCHAR(1000) | Path to image/table file |
| block_metadata | JSON | Type-specific metadata, AI summaries |
| order | INTEGER | Position within section |
| created_at | DATETIME | Creation timestamp |

**Indexes**: `idx_content_section_id`, `idx_content_type`, `idx_content_order`

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000
```

### Health Check

#### `GET /api/v1/health`
Check API health and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Document Management

#### `POST /api/v1/documents/upload`
Upload and process a document.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Annual Report 2024",
  "source_filename": "document.pdf",
  "created_at": "2024-01-15T10:30:00Z",
  "sections_count": 12,
  "content_blocks_count": 145
}
```

#### `GET /api/v1/documents`
List all documents with pagination.

**Parameters:**
- `skip` (int, default=0): Number of records to skip
- `limit` (int, default=100): Maximum records to return

**Response:**
```json
{
  "total": 250,
  "skip": 0,
  "limit": 100,
  "documents": [
    {
      "id": "...",
      "title": "Document 1",
      "source_filename": "doc1.pdf",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### `GET /api/v1/documents/{id}`
Get a specific document with full hierarchy.

**Response:**
```json
{
  "id": "...",
  "title": "Annual Report 2024",
  "source_filename": "report.pdf",
  "sections": [
    {
      "id": "...",
      "title": "Chapter 1",
      "level": 1,
      "content_blocks": [
        {
          "type": "text",
          "text": "Introduction paragraph..."
        },
        {
          "type": "table",
          "src": "output/.../tables/table_001.csv",
          "metadata": {
            "caption": "Sales Data",
            "ai_summary": "Revenue increased 15% YoY"
          }
        }
      ]
    }
  ]
}
```

#### `DELETE /api/v1/documents/{id}`
Delete a document and all related data.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### Search

#### `GET /api/v1/search/documents?q={query}`
Search documents by title or filename.

**Parameters:**
- `q` (string, required): Search query
- `skip` (int, default=0): Pagination offset
- `limit` (int, default=100): Results per page

**Response:**
```json
{
  "query": "annual report",
  "total": 5,
  "results": [
    {
      "id": "...",
      "title": "Annual Report 2024",
      "source_filename": "report_2024.pdf",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### `GET /api/v1/search/content?q={query}`
Search within document content (text blocks).

#### `GET /api/v1/search/tables`
Get all tables from all documents.

#### `GET /api/v1/search/images`
Get all images from all documents.

---

## 🧩 Core Components

### 1. Document Processing (`digitizer.py`)

**Purpose**: Standalone CLI tool for batch document processing.

**Features**:
- Processes documents from `data/` directory
- Supports multiple file formats
- GPU acceleration (if available)
- Progress tracking with tqdm
- Saves output to `output/` directory

**Usage**:
```bash
python src/digitizer.py
python src/digitizer.py --input data/report.pdf
python src/digitizer.py --config config.json
```

### 2. Transformation (`transformer.py`)

**Purpose**: Converts Docling output to hierarchical JSON structure.

**Key Functions**:
- `transform_to_nodes()`: Converts Docling document to node tree
- `merge_tables()`: Merges split tables across pages
- Extracts images and tables to separate files
- Maintains document hierarchy

### 3. Database Repository (`repository.py`)

**Purpose**: Data access layer using repository pattern.

**Classes**:
- `DocumentRepository`: CRUD operations for documents
  - `create_from_json()`: Create document from hierarchical JSON
  - `get_by_id()`: Retrieve document with all relationships
  - `list_all()`: Paginated document listing
  - `search()`: Search by title/filename
  - `delete()`: Remove document and cascade delete

- `ContentRepository`: Content-specific queries
  - `search_by_type()`: Find all tables, images, etc.
  - `search_text()`: Full-text search in content

### 4. API Routers

**Document Router** (`document_router.py`):
- Upload endpoint with file validation
- Document CRUD operations
- Automatic processing pipeline

**Search Router** (`search_router.py`):
- Document search
- Content search
- Type-specific queries (tables, images)

**Health Router** (`health_router.py`):
- API health check
- Database connectivity test

### 5. Gemini AI Integration (`gemini_client.py`)

**Purpose**: AI-powered summarization of tables and images.

**Features**:
- Table summarization with context
- Image description generation
- Configurable prompts
- Error handling and retries

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) Google Gemini API key for AI features

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Proveer/docling-digitization-project.git
cd docling-digitization-project
```

2. **Create virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Gemini API key (optional)
# DATABASE_URL is already set to SQLite by default
```

5. **Initialize database**
```bash
# Database will be created automatically on first run
# Or manually initialize:
python -c "from src.database import init_db; init_db()"
```

### Running the API

```bash
# Development mode (auto-reload enabled)
uvicorn src.routers.main:app --reload

# Production mode
uvicorn src.routers.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

### Running CLI Tool

```bash
# Process all documents in data/ directory
python src/digitizer.py

# Process specific file
python src/digitizer.py --input data/report.pdf

# Use custom config
python src/digitizer.py --config config.json
```

---

## 💡 Usage Examples

### Example 1: Upload and Process Document via API

```python
import requests

# Upload document
with open('report.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        files={'file': f}
    )

doc = response.json()
print(f"Document ID: {doc['id']}")
print(f"Title: {doc['title']}")
```

### Example 2: Search Documents

```python
import requests

# Search for documents
response = requests.get(
    'http://localhost:8000/api/v1/search/documents',
    params={'q': 'annual report', 'limit': 10}
)

results = response.json()
for doc in results['results']:
    print(f"{doc['title']} - {doc['created_at']}")
```

### Example 3: Retrieve Document with Full Hierarchy

```python
import requests

doc_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
response = requests.get(f'http://localhost:8000/api/v1/documents/{doc_id}')

doc = response.json()
for section in doc['sections']:
    print(f"Section: {section['title']}")
    for block in section['content_blocks']:
        if block['type'] == 'table':
            print(f"  Table: {block['metadata']['caption']}")
            print(f"  AI Summary: {block['metadata']['ai_summary']}")
```

### Example 4: Direct Database Access

```python
from src.database import get_db_session
from src.database.models import Document, Section, ContentBlock

db = get_db_session()
try:
    # Query documents
    documents = db.query(Document).all()
    
    for doc in documents:
        print(f"\nDocument: {doc.title}")
        print(f"Sections: {len(doc.sections)}")
        
        # Count tables
        table_count = sum(
            1 for section in doc.sections
            for block in section.content_blocks
            if block.type == 'table'
        )
        print(f"Tables: {table_count}")
finally:
    db.close()
```

### Example 5: Batch Processing with CLI

```bash
# Create a batch processing script
cat > process_all.sh << 'EOF'
#!/bin/bash
for file in data/*.pdf; do
    echo "Processing $file..."
    python src/digitizer.py --input "$file"
done
EOF

chmod +x process_all.sh
./process_all.sh
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database (SQLite by default)
DATABASE_URL=sqlite:///./docling.db

# Gemini AI (optional, for table/image summarization)
GEMINI_API_KEY=your_api_key_here

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true

# File Storage
UPLOAD_DIR=uploads
OUTPUT_DIR=output
MAX_FILE_SIZE_MB=100

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Application Config (config.json)

```json
{
  "input_dir": "data",
  "output_dir": "output",
  "allowed_extensions": [".pdf", ".docx", ".pptx"]
}
```

### Switching to PostgreSQL

1. Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

2. Update .env:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/docling_db
```

3. Create database:
```sql
CREATE DATABASE docling_db;
```

4. Restart the API (tables will be created automatically)

---

## 🔧 Development Guide

### Code Structure Guidelines

1. **Routers**: Handle HTTP requests/responses only
2. **Resolvers**: Contain business logic
3. **Repositories**: Handle database operations
4. **Utilities**: Reusable helper functions
5. **Models**: Database schema definitions

### Adding a New Endpoint

1. Define Pydantic schema in `routers/schemas.py`
2. Add route in appropriate router file
3. Implement business logic in resolver
4. Add database operations in repository (if needed)

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_transformer.py
```

### Database Migrations (Production)

For production, use Alembic for schema migrations:

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and returns
- Write comprehensive docstrings (Google style)
- Keep functions focused and small
- Use meaningful variable names

### Debugging

Enable SQL query logging:
```python
# In src/database/connection.py
engine = create_engine(DATABASE_URL, echo=True)
```

Enable FastAPI debug mode:
```bash
uvicorn src.routers.main:app --reload --log-level debug
```

---

## 📚 Additional Resources

- **Docling Documentation**: https://github.com/DS4SD/docling
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Google Gemini AI**: https://ai.google.dev/

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/Proveer/docling-digitization-project/issues
- Email: support@example.com

---

**Last Updated**: February 2026
**Version**: 1.0.0
