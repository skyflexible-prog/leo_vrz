"""
MongoDB connection and client management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from utils.logger import bot_logger


class MongoDBClient:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.MONGODB_DB_NAME]
            
            # Test connection
            await self.client.server_info()
            bot_logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            bot_logger.error(f"MongoDB connection failed: {str(e)}", exc_info=True)
            raise
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        # VRZ zones indexes
        await self.db.vrz_zones.create_index([("symbol", 1), ("status", 1)])
        await self.db.vrz_zones.create_index([("timeframe", 1)])
        await self.db.vrz_zones.create_index([("created_at", -1)])
        
        # User settings indexes
        await self.db.user_settings.create_index([("telegram_user_id", 1)], unique=True)
        
        # Trades indexes
        await self.db.trades.create_index([("telegram_user_id", 1), ("status", 1)])
        await self.db.trades.create_index([("symbol", 1)])
        await self.db.trades.create_index([("created_at", -1)])
        
        bot_logger.info("Database indexes created")
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            bot_logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """Get collection by name"""
        return self.db[collection_name]


# Global MongoDB client
mongodb_client = MongoDBClient()
