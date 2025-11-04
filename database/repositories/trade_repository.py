"""
Repository for trade database operations
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database.mongodb_client import mongodb_client
from config.settings import settings
from utils.logger import bot_logger


class TradeRepository:
    """Trade data access layer"""
    
    def __init__(self):
        self.collection = None
    
    async def initialize(self):
        """Initialize repository"""
        self.collection = mongodb_client.get_collection('trades')
    
    async def create_trade(self, trade_data: Dict) -> str:
        """
        Create new trade record
        
        Args:
            trade_data: Trade dictionary
        
        Returns:
            Trade ID
        """
        try:
            result = await self.collection.insert_one(trade_data)
            trade_id = str(result.inserted_id)
            
            bot_logger.info(f"Trade created: {trade_id} - {trade_data.get('symbol')}")
            return trade_id
            
        except Exception as e:
            bot_logger.error(f"Error creating trade: {str(e)}", exc_info=True)
            raise
    
    async def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get trade by ID"""
        try:
            from bson import ObjectId
            trade = await self.collection.find_one({'_id': ObjectId(trade_id)})
            return trade
            
        except Exception as e:
            bot_logger.error(f"Error getting trade: {str(e)}", exc_info=True)
            return None
    
    async def get_open_trades(self, telegram_user_id: Optional[int] = None) -> List[Dict]:
        """
        Get all open trades
        
        Args:
            telegram_user_id: Filter by user (None for all users)
        
        Returns:
            List of open trades
        """
        try:
            query = {'status': 'open'}
            if telegram_user_id:
                query['telegram_user_id'] = telegram_user_id
            
            cursor = self.collection.find(query)
            trades = await cursor.to_list(length=100)
            return trades
            
        except Exception as e:
            bot_logger.error(f"Error getting open trades: {str(e)}", exc_info=True)
            return []
    
    async def get_closed_trades(self, telegram_user_id: int, limit: int = 50) -> List[Dict]:
        """Get closed trades for user"""
        try:
            cursor = self.collection.find({
                'telegram_user_id': telegram_user_id,
                'status': 'closed'
            }).sort('exit_time', -1).limit(limit)
            
            trades = await cursor.to_list(length=limit)
            return trades
            
        except Exception as e:
            bot_logger.error(f"Error getting closed trades: {str(e)}", exc_info=True)
            return []
    
    async def update_trade(self, trade_id: str, updates: Dict) -> bool:
        """Update trade"""
        try:
            from bson import ObjectId
            
            result = await self.collection.update_one(
                {'_id': ObjectId(trade_id)},
                {'$set': updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            bot_logger.error(f"Error updating trade: {str(e)}", exc_info=True)
            return False
    
    async def get_trade_statistics(self, telegram_user_id: int, days: int = 30) -> Dict:
        """
        Get trade statistics for user
        
        Args:
            telegram_user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Statistics dictionary
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get closed trades in period
            trades = await self.collection.find({
                'telegram_user_id': telegram_user_id,
                'status': 'closed',
                'exit_time': {'$gte': cutoff_date}
            }).to_list(length=1000)
            
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'profit_factor': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0
                }
            
            # Calculate statistics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
            
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            total_wins = sum(t.get('pnl', 0) for t in winning_trades)
            total_losses = abs(sum(t.get('pnl', 0) for t in losing_trades))
            
            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            avg_win = total_wins / len(winning_trades) if winning_trades else 0
            avg_loss = total_losses / len(losing_trades) if losing_trades else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0
            
            best_trade = max((t.get('pnl', 0) for t in trades), default=0)
            worst_trade = min((t.get('pnl', 0) for t in trades), default=0)
            
            return {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'best_trade': best_trade,
                'worst_trade': worst_trade
            }
            
        except Exception as e:
            bot_logger.error(f"Error calculating trade statistics: {str(e)}", exc_info=True)
            return {}
    
    async def cleanup_old_trades(self):
        """Remove old closed trades beyond retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.TRADE_RETENTION_DAYS)
            
            result = await self.collection.delete_many({
                'status': 'closed',
                'exit_time': {'$lt': cutoff_date}
            })
            
            if result.deleted_count > 0:
                bot_logger.info(f"Cleaned up {result.deleted_count} old trades")
            
        except Exception as e:
            bot_logger.error(f"Error cleaning up old trades: {str(e)}", exc_info=True)


# Global repository instance
trade_repository = TradeRepository()
