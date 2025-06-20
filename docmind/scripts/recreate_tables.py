"""
Script to recreate database tables with new structure
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from docmind.models.database import drop_tables, create_tables, engine
from docmind.config.settings import settings
from sqlalchemy import text

def recreate_tables():
    """Drop and recreate all tables"""
    print("🗑️ Dropping existing tables...")
    
    try:
        # Drop all tables
        drop_tables()
        print("✅ Tables dropped successfully")
        
        print("🔧 Creating new tables...")
        
        # Create tables with new structure
        create_tables()
        print("✅ Tables created successfully")
        
        print(f"📊 Database URL: {settings.database_url}")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"📋 Tables in database: {tables}")
            
    except Exception as e:
        print(f"❌ Failed to recreate tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    recreate_tables() 