"""Health check router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from .schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns API status, database connectivity, and version.
    """
    # Test database connection
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        version="1.0.0"
    )
