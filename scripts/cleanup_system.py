#!/usr/bin/env python3
"""
Script to clean up the entire system - database, files, and Qdrant collection
"""
import asyncio
import logging
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import AsyncQdrantClient
from docmind.config.settings import settings
from docmind.models.database import engine, drop_tables, create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_system():
    """Clean up the entire system"""
    
    logger.info("🧹 Starting system cleanup...")
    
    # 1. Clean up Qdrant collection
    try:
        client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        
        try:
            await client.delete_collection(settings.qdrant_collection_name)
            logger.info("🗑️  Deleted Qdrant collection")
        except:
            logger.info("ℹ️  No Qdrant collection to delete")
        
        await client.close()
        
    except Exception as e:
        logger.warning(f"⚠️  Could not clean Qdrant: {e}")
    
    # 2. Clean up database
    try:
        logger.info("🗑️  Dropping database tables...")
        drop_tables()
        
        logger.info("🔧 Creating fresh database tables...")
        create_tables()
        
        logger.info("✅ Database cleaned and recreated")
        
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")
        raise
    
    # 3. Clean up uploaded files
    try:
        uploads_dir = project_root / "uploads"
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
            logger.info("🗑️  Deleted uploads directory")
        
        uploads_dir.mkdir(exist_ok=True)
        logger.info("📁 Created fresh uploads directory")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not clean uploads: {e}")
    
    # 4. Clean up temp files
    try:
        temp_dir = project_root / "temp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info("🗑️  Deleted temp directory")
        
        temp_dir.mkdir(exist_ok=True)
        logger.info("📁 Created fresh temp directory")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not clean temp: {e}")
    
    logger.info("✅ System cleanup completed!")
    logger.info("🎉 Ready for fresh start")


if __name__ == "__main__":
    asyncio.run(cleanup_system()) 