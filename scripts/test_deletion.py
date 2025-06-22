#!/usr/bin/env python3
"""
Test script for Qdrant deletion functionality
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from docmind.core.vector_store.qdrant_store import async_vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_deletion():
    """Test deletion functionality"""
    try:
        # Get current stats
        stats = await async_vector_store.get_stats_async()
        logger.info(f"Current collection stats: {stats}")
        
        # Test with a known chat ID (replace with actual ID from your system)
        test_chat_id = "89d62bed-ff3e-4a0a-b8e6-07f806966428"
        
        logger.info(f"Testing deletion for chat: {test_chat_id}")
        result = await async_vector_store.delete_chat_chunks_async(test_chat_id)
        
        if result:
            logger.info("✅ Deletion completed successfully")
        else:
            logger.warning("⚠️ Deletion returned False")
            
        # Get stats after deletion
        stats_after = await async_vector_store.get_stats_async()
        logger.info(f"Stats after deletion: {stats_after}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
    finally:
        await async_vector_store.close()


if __name__ == "__main__":
    asyncio.run(test_deletion()) 