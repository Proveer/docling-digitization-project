"""
Database connection and session management.

This module handles database connectivity and session lifecycle management
using SQLAlchemy. It supports multiple database backends (SQLite, PostgreSQL,
MySQL) with appropriate connection pooling and configuration.

Configuration:
--------------
Database connection is configured via the DATABASE_URL environment variable:

- SQLite (Development):
    DATABASE_URL=sqlite:///./docling.db
    
- PostgreSQL (Production):
    DATABASE_URL=postgresql://user:password@localhost:5432/docling_db
    
- MySQL (Production):
    DATABASE_URL=mysql+pymysql://user:password@localhost:3306/docling_db

Features:
---------
- Automatic database initialization on startup
- Connection pooling for production databases
- Thread-safe session management
- FastAPI dependency injection support
- Graceful connection cleanup

Session Management:
-------------------
Sessions are managed using the context manager pattern to ensure proper
cleanup and transaction handling:

    # In FastAPI endpoints
    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
    
    # In standalone scripts
    db = get_db_session()
    try:
        # Your database operations
        db.add(item)
        db.commit()
    finally:
        db.close()

Connection Pooling:
-------------------
- SQLite: Uses StaticPool (single connection, thread-safe)
- PostgreSQL/MySQL: Uses QueuePool with configurable pool size
    - pool_size: 10 (normal connections)
    - max_overflow: 20 (additional connections under load)
    - pool_pre_ping: True (validates connections before use)
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

from .models import Base

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
# Default to SQLite for development if not specified
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./docling.db")

# Create database engine with appropriate configuration
# SQLite configuration (for development and small-scale deployments)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Allow multi-threaded access
        poolclass=StaticPool,  # Single connection pool for SQLite
        echo=False  # Set to True for SQL query debugging
    )
else:
    # PostgreSQL/MySQL configuration (for production deployments)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using (handles stale connections)
        pool_size=10,  # Number of connections to maintain in the pool
        max_overflow=20,  # Maximum additional connections under load
        echo=False  # Set to True for SQL query debugging
    )

# Create session factory
# Sessions are used for all database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in the models if they don't already exist.
    This function is idempotent - it's safe to call multiple times.
    
    The function uses SQLAlchemy's metadata.create_all() which:
    - Creates tables that don't exist
    - Skips tables that already exist
    - Does NOT modify existing table schemas
    
    Note:
        For schema migrations in production, use Alembic instead of
        calling this function repeatedly.
    
    Raises:
        SQLAlchemyError: If database connection or table creation fails
    
    Example:
        >>> from src.database import init_db
        >>> init_db()
        Database tables created successfully!
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for FastAPI dependency injection.
    
    This is a generator function that yields a database session and ensures
    proper cleanup after the request is complete. It's designed to be used
    with FastAPI's Depends() for automatic session management.
    
    The session lifecycle:
    1. Create a new session
    2. Yield it to the endpoint
    3. Close it after the endpoint completes (even if an exception occurs)
    
    Yields:
        Session: SQLAlchemy database session
    
    Example:
        >>> from fastapi import Depends
        >>> from src.database import get_db
        >>> 
        >>> @app.get("/items")
        >>> def read_items(db: Session = Depends(get_db)):
        >>>     return db.query(Item).all()
    
    Note:
        Do not call db.close() manually when using this with Depends().
        The cleanup is handled automatically in the finally block.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for non-FastAPI contexts.
    
    Use this function when you need a database session outside of FastAPI
    endpoints (e.g., in standalone scripts, background tasks, or CLI tools).
    
    Important:
        You are responsible for closing the session when done. Use a
        try-finally block to ensure proper cleanup.
    
    Returns:
        Session: SQLAlchemy database session
    
    Example:
        >>> from src.database import get_db_session
        >>> 
        >>> # In a standalone script
        >>> db = get_db_session()
        >>> try:
        >>>     documents = db.query(Document).all()
        >>>     for doc in documents:
        >>>         print(doc.title)
        >>> finally:
        >>>     db.close()
    
    See Also:
        get_db(): For use with FastAPI dependency injection
    """
    return SessionLocal()
