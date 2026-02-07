# Docling Digitization API - Quick Start

## New Simplified Structure

```
src/
├── routers/           # All API code
│   ├── main.py       # FastAPI app
│   ├── schemas.py    # Pydantic models
│   ├── document_router.py
│   ├── search_router.py
│   └── health_router.py
├── resolvers/         # Business logic
├── utilities/         # Helper functions
└── database/          # Data access
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update:
```env
DATABASE_URL=sqlite:///./docling.db
GEMINI_API_KEY=your_api_key_here
```

### 3. Run the API
```bash
uvicorn src.routers.main:app --reload
```

### 4. Access API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## API Endpoints

### Documents
- `POST /api/v1/documents/upload` - Upload and process document
- `GET /api/v1/documents` - List all documents
- `GET /api/v1/documents/{id}` - Get document by ID
- `DELETE /api/v1/documents/{id}` - Delete document

### Search
- `GET /api/v1/search/documents?q=query` - Search documents
- `GET /api/v1/search/content?q=query` - Search content
- `GET /api/v1/search/tables` - Get all tables
- `GET /api/v1/search/images` - Get all images

## Example Usage

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"

# List documents
curl "http://localhost:8000/api/v1/documents"

# Search
curl "http://localhost:8000/api/v1/search/documents?q=protocol"
```

## What Changed

- ✅ Removed `src/api/` directory
- ✅ Consolidated everything into `src/routers/`
- ✅ Cleaner, simpler structure
- ✅ Updated command: `uvicorn src.routers.main:app --reload`
