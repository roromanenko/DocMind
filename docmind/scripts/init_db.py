"""
Database initialization script
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from docmind.models.database import create_tables, engine
from docmind.config.settings import settings
from sqlalchemy import text

def init_database():
    """Initialize database tables"""
    print("🔧 Initializing database...")
    
    try:
        # Create tables
        create_tables()
        print(f"✅ Database tables created successfully")
        print(f"📊 Database URL: {settings.database_url}")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 