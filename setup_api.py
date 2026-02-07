"""Quick setup script to initialize the API."""

import os
import sys
from pathlib import Path

def main():
    """Run setup steps."""
    print("=" * 60)
    print("Docling Digitization API - Setup")
    print("=" * 60)
    print()
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("   Creating from .env.example...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ .env file created")
            print()
            print("⚠️  IMPORTANT: Edit .env and add your credentials:")
            print("   - DATABASE_URL (PostgreSQL/MySQL connection string)")
            print("   - GEMINI_API_KEY (your Gemini API key)")
            print()
        else:
            print("❌ .env.example not found!")
            return 1
    else:
        print("✅ .env file found")
        print()
    
    # Install dependencies
    print("Installing API dependencies...")
    print("Run: pip install -r requirements-api.txt")
    print()
    
    # Initialize database
    print("Initializing database...")
    try:
        from src.database import init_db
        init_db()
        print("✅ Database initialized successfully")
        print()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("   Make sure DATABASE_URL in .env is correct")
        print()
        return 1
    
    # Create directories
    print("Creating directories...")
    dirs = ["uploads", "output", "output/images", "output/tables"]
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")
    print()
    
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Edit .env and add your credentials")
    print("2. Run the API: python src/api/main.py")
    print("3. Open http://localhost:8000/docs for API documentation")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
