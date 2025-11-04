"""
Repository for VRZ zone database operations
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from database.mongodb_client import mongodb_client
from database.models import VRZZone
from config.settings import settings
from utils.logger import bot_logger


class VRZRepository:
    """VRZ zone data access layer"""
    
    def __init__(self):
        self.collection = None
    
    async def initialize(self):
        """Initialize repository"""
        self.collection = mongodb_client.get_collection('vrz_zones')
    
    async def create_zone(self, zone: VRZZone) -> str:
        """Insert new VRZ zone"""
        zone_dict = zone.dict(by_alias=True, exclude={'id'})
        result = await self.collection.insert_one(zone_dict)
        bot_logger.log_vrz_detection(zone.type, zone.price_level, zone.timeframe, zone.symbol)
        return str(result.inserted_id)
    
    async def get_active_zones(self, symbol: str, timeframe: str, 
                               zone_type: Optional[str] = None) -> List[Dict]:
        """Get active VRZ zones for symbol and timeframe"""
        query = {'symbol': symbol, 'timeframe': timeframe, 'status': 'active'}
        if zone_type:
            query['type'] = zone_type
        cursor = self.collection.find(query).sort('created_at', -1)
        zones = await cursor.to_list(length=100)
        return zones
    
    async def get_nearest_zones(self, symbol: str, timeframe: str, 
                               current_price: float, zone_type: str, 
                               limit: int = 3) -> List[Dict]:
        """Get nearest VRZ zones to current price"""
        query = {'symbol': symbol, 'timeframe': timeframe, 'status': 'active', 'type': zone_type}
        zones = await self.collection.find(query).to_list(length=100)
        
        for zone in zones:
            zone['distance'] = abs(zone['price_level'] - current_price)
        
        sorted_zones = sorted(zones, key=lambda x: x['distance'])
        return sorted_zones[:limit]
    
    async def invalidate_zone(self, zone_id: str, breach_details: Dict):
        """Mark zone as invalidated"""
        await self.collection.update_one(
            {'_id': zone_id},
            {'$set': {'status': 'invalidated', 'breach_details': breach_details}}
        )
        bot_logger.info(f"VRZ zone invalidated: {zone_id}")
    
    async def check_and_invalidate(self, symbol: str, current_candle: Dict):
        """Check active zones and invalidate if breached"""
        active_zones = await self.collection.find({'symbol': symbol, 'status': 'active'}).to_list(length=None)
        
        for zone in active_zones:
            breached = False
            
            if zone['type'] == 'resistance':
                if current_candle['high'] > zone['zone_upper']:
                    breached = True
            else:
                if current_candle['low'] < zone['zone_lower']:
                    breached = True
            
            if breached:
                breach_details = {
                    'breach_price': current_candle['close'],
                    'breach_time': datetime.utcnow(),
                    'breach_timeframe': zone['timeframe']
                }
                await self.invalidate_zone(str(zone['_id']), breach_details)
    
    async def cleanup_old_zones(self):
        """Remove old invalidated zones beyond retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.VRZ_RETENTION_DAYS)
        result = await self.collection.delete_many({
            'status': 'invalidated',
            'created_at': {'$lt': cutoff_date}
        })
        if result.deleted_count > 0:
            bot_logger.info(f"Cleaned up {result.deleted_count} old VRZ zones")


# Global repository instance
vrz_repository = VRZRepository()
