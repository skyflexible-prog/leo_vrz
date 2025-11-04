"""
Repository for user settings database operations
"""
from typing import Optional, Dict
from datetime import datetime
from database.mongodb_client import mongodb_client
from database.models import UserSettings
from utils.logger import bot_logger


class UserSettingsRepository:
    """User settings data access layer"""
    
    def __init__(self):
        self.collection = None
    
    async def initialize(self):
        """Initialize repository"""
        self.collection = mongodb_client.get_collection('user_settings')
    
    async def create_user_settings(self, telegram_user_id: int) -> str:
        """
        Create default user settings
        
        Args:
            telegram_user_id: Telegram user ID
        
        Returns:
            Settings ID
        """
        try:
            user_settings = UserSettings(telegram_user_id=telegram_user_id)
            settings_dict = user_settings.dict(by_alias=True, exclude={'id'})
            
            result = await self.collection.insert_one(settings_dict)
            
            bot_logger.info(f"Created default settings for user {telegram_user_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            bot_logger.error(f"Error creating user settings: {str(e)}", exc_info=True)
            raise
    
    async def get_user_settings(self, telegram_user_id: int) -> Optional[Dict]:
        """
        Get user settings by Telegram user ID
        
        Args:
            telegram_user_id: Telegram user ID
        
        Returns:
            User settings dictionary or None
        """
        try:
            settings = await self.collection.find_one({'telegram_user_id': telegram_user_id})
            
            if not settings:
                # Create default settings if not found
                await self.create_user_settings(telegram_user_id)
                settings = await self.collection.find_one({'telegram_user_id': telegram_user_id})
            
            return settings
            
        except Exception as e:
            bot_logger.error(f"Error getting user settings: {str(e)}", exc_info=True)
            return None
    
    async def update_user_settings(self, telegram_user_id: int, updates: Dict) -> bool:
        """
        Update user settings
        
        Args:
            telegram_user_id: Telegram user ID
            updates: Dictionary of fields to update
        
        Returns:
            True if successful
        """
        try:
            updates['updated_at'] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {'telegram_user_id': telegram_user_id},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                bot_logger.info(f"Updated settings for user {telegram_user_id}: {list(updates.keys())}")
                return True
            
            return False
            
        except Exception as e:
            bot_logger.error(f"Error updating user settings: {str(e)}", exc_info=True)
            return False
    
    async def update_selected_assets(self, telegram_user_id: int, assets: list) -> bool:
        """
        Update selected assets for user
        
        Args:
            telegram_user_id: Telegram user ID
            assets: List of asset symbols
        
        Returns:
            True if successful
        """
        return await self.update_user_settings(
            telegram_user_id, 
            {'selected_assets': assets}
        )
    
    async def update_asset_selection_mode(self, telegram_user_id: int, mode: str) -> bool:
        """
        Update asset selection mode
        
        Args:
            telegram_user_id: Telegram user ID
            mode: 'top_gainers', 'top_losers', 'both', 'all', 'individual'
        
        Returns:
            True if successful
        """
        return await self.update_user_settings(
            telegram_user_id, 
            {'asset_selection_mode': mode}
        )
    
    async def update_timeframes(self, telegram_user_id: int, 
                               base_timeframe: str, trading_timeframe: str) -> bool:
        """
        Update timeframe settings
        
        Args:
            telegram_user_id: Telegram user ID
            base_timeframe: Base timeframe for VRZ calculation
            trading_timeframe: Trading timeframe for entries
        
        Returns:
            True if successful
        """
        return await self.update_user_settings(
            telegram_user_id, 
            {
                'base_timeframe': base_timeframe,
                'trading_timeframe': trading_timeframe
            }
        )
    
    async def update_lot_size(self, telegram_user_id: int, lot_size: int) -> bool:
        """Update lot size"""
        return await self.update_user_settings(telegram_user_id, {'lot_size': lot_size})
    
    async def update_stop_loss_pips(self, telegram_user_id: int, pips: int) -> bool:
        """Update stop loss pips"""
        return await self.update_user_settings(telegram_user_id, {'stop_loss_pips': pips})
    
    async def update_target_settings(self, telegram_user_id: int, 
                                    target_type: str, target_levels: list) -> bool:
        """
        Update target settings
        
        Args:
            telegram_user_id: Telegram user ID
            target_type: 'zone' or 'rr'
            target_levels: List of RR levels or zone count
        
        Returns:
            True if successful
        """
        return await self.update_user_settings(
            telegram_user_id, 
            {
                'target_type': target_type,
                'target_levels': target_levels
            }
        )
    
    async def update_order_type(self, telegram_user_id: int, order_type: str) -> bool:
        """Update order type"""
        return await self.update_user_settings(telegram_user_id, {'order_type': order_type})
    
    async def toggle_active_status(self, telegram_user_id: int, is_active: bool) -> bool:
        """
        Toggle bot active status for user
        
        Args:
            telegram_user_id: Telegram user ID
            is_active: Active status
        
        Returns:
            True if successful
        """
        return await self.update_user_settings(telegram_user_id, {'is_active': is_active})
    
    async def get_all_active_users(self) -> list:
        """
        Get all users with active bot status
        
        Returns:
            List of active user settings
        """
        try:
            cursor = self.collection.find({'is_active': True})
            users = await cursor.to_list(length=1000)
            return users
            
        except Exception as e:
            bot_logger.error(f"Error getting active users: {str(e)}", exc_info=True)
            return []


# Global repository instance
user_settings_repository = UserSettingsRepository()
