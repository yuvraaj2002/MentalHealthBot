from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB connection with connection pooling
class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Global database instance
mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection with connection pooling"""
    try:
        # Connection pool configuration
        mongodb.client = AsyncIOMotorClient(
            settings.mongodb_url,
            # Connection pool settings
            maxPoolSize=50,          # Maximum number of connections in the pool
            minPoolSize=5,           # Minimum number of connections in the pool
            maxIdleTimeMS=30000,     # Close connections after 30 seconds of inactivity
            waitQueueTimeoutMS=5000, # Wait up to 5 seconds for a connection
            serverSelectionTimeoutMS=5000,  # Wait up to 5 seconds to select a server
            connectTimeoutMS=10000,  # Wait up to 10 seconds to establish a connection
            socketTimeoutMS=20000,   # Wait up to 20 seconds for a socket operation
            retryWrites=True,        # Retry write operations
            retryReads=True,         # Retry read operations
            # Heartbeat settings
            heartbeatFrequencyMS=10000,  # Send heartbeat every 10 seconds
        )
        
        mongodb.database = mongodb.client[settings.mongodb_database]
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        
        # Log connection pool info
        server_info = await mongodb.client.server_info()
        logger.info(f"Successfully connected to MongoDB with connection pooling")
        logger.info(f"MongoDB version: {server_info.get('version', 'Unknown')}")
        logger.info(f"Connection pool configured: max={50}, min={5}")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection and connection pool"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB and closed connection pool")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance with connection pooling"""
    if mongodb.database is None:
        raise Exception("Database not initialized. Call connect_to_mongo() first.")
    return mongodb.database

# Database dependency for FastAPI (async version)
async def get_db():
    """Database dependency for FastAPI with connection pooling"""
    return get_database()

# Connection pool monitoring
async def get_connection_pool_stats():
    """Get connection pool statistics for monitoring"""
    try:
        if mongodb.client:
            # Try to get basic connection info without admin privileges
            try:
                # Get server info (requires less privileges than serverStatus)
                server_info = await mongodb.client.server_info()
                stats = {
                    'server_version': server_info.get('version', 'Unknown'),
                    'connection_pool_configured': True,
                    'max_pool_size': 50,
                    'min_pool_size': 5,
                    'status': 'connected'
                }
            except Exception as admin_error:
                # If admin commands fail, return basic connection status
                logger.warning(f"Admin commands not available: {admin_error}")
                stats = {
                    'connection_pool_configured': True,
                    'max_pool_size': 50,
                    'min_pool_size': 5,
                    'status': 'connected',
                    'note': 'Limited stats due to user permissions'
                }
            
            logger.info(f"Connection pool stats: {stats}")
            return stats
        else:
            return {"error": "Database not connected"}
    except Exception as e:
        logger.error(f"Error getting connection pool stats: {e}")
        return {"error": str(e)}