"""
Position Manager - Tracks and manages open positions
"""
from typing import Dict, List, Optional
from datetime import datetime
from api.delta_client import delta_client
from database.models import Trade
from database.mongodb_client import mongodb_client
from utils.logger import bot_logger


class PositionManager:
    """
    Manages trading positions - tracking, updates, and synchronization
    """
    
    def __init__(self):
        self.positions_collection = None
        bot_logger.info("Position Manager initialized")
    
    async def initialize(self):
        """Initialize position manager with database connection"""
        self.positions_collection = mongodb_client.get_collection('trades')
    
    async def create_position(self, entry_signal: Dict, order_response: Dict) -> Optional[str]:
        """
        Create new position record in database
        
        Args:
            entry_signal: Entry signal dictionary
            order_response: Order execution response
        
        Returns:
            Position ID or None
        """
        try:
            order = order_response.get('result', {})
            
            trade = Trade(
                telegram_user_id=entry_signal.get('telegram_user_id'),
                symbol=entry_signal['symbol'],
                product_id=entry_signal['product_id'],
                order_id=order.get('id'),
                entry_price=entry_signal['entry_price'],
                stop_loss=entry_signal['stop_loss'],
                targets=entry_signal['targets'],
                position_size=entry_signal['lot_size'],
                remaining_size=entry_signal['lot_size'],
                side=entry_signal['side'],
                entry_pattern=entry_signal['pattern'],
                entry_vrz_zone=entry_signal['entry_zone'],
                entry_time=datetime.utcnow(),
                status='open',
                exit_details=[]
            )
            
            trade_dict = trade.dict(by_alias=True, exclude={'id'})
            result = await self.positions_collection.insert_one(trade_dict)
            
            position_id = str(result.inserted_id)
            bot_logger.info(f"Position created: {position_id} - {entry_signal['symbol']}")
            
            return position_id
            
        except Exception as e:
            bot_logger.error(f"Error creating position: {str(e)}", exc_info=True)
            return None
    
    async def get_position(self, position_id: str) -> Optional[Dict]:
        """
        Get position by ID
        
        Args:
            position_id: Position ID
        
        Returns:
            Position dictionary or None
        """
        try:
            from bson import ObjectId
            position = await self.positions_collection.find_one({'_id': ObjectId(position_id)})
            return position
            
        except Exception as e:
            bot_logger.error(f"Error getting position: {str(e)}", exc_info=True)
            return None
    
    async def get_open_positions(self, telegram_user_id: Optional[int] = None) -> List[Dict]:
        """
        Get all open positions
        
        Args:
            telegram_user_id: Filter by user ID (None for all users)
        
        Returns:
            List of open positions
        """
        try:
            query = {'status': 'open'}
            if telegram_user_id:
                query['telegram_user_id'] = telegram_user_id
            
            cursor = self.positions_collection.find(query)
            positions = await cursor.to_list(length=100)
            
            return positions
            
        except Exception as e:
            bot_logger.error(f"Error getting open positions: {str(e)}", exc_info=True)
            return []
    
    async def update_position_exit(self, position_id: str, exit_action: Dict) -> bool:
        """
        Update position with exit details
        
        Args:
            position_id: Position ID
            exit_action: Exit action dictionary
        
        Returns:
            True if successful
        """
        try:
            from bson import ObjectId
            
            position = await self.get_position(position_id)
            if not position:
                return False
            
            # Update exit details
            exit_details = position.get('exit_details', [])
            exit_details.append(exit_action)
            
            # Update remaining size
            remaining_size = exit_action.get('remaining_quantity', 0)
            
            # Calculate total PnL
            total_pnl = position.get('pnl', 0) + exit_action.get('pnl', 0)
            
            # Determine if position is fully closed
            status = 'closed' if remaining_size == 0 else 'open'
            
            update_fields = {
                'exit_details': exit_details,
                'remaining_size': remaining_size,
                'pnl': total_pnl
            }
            
            if status == 'closed':
                update_fields['status'] = 'closed'
                update_fields['exit_time'] = datetime.utcnow()
            
            await self.positions_collection.update_one(
                {'_id': ObjectId(position_id)},
                {'$set': update_fields}
            )
            
            bot_logger.info(
                f"Position updated: {position_id} - "
                f"Remaining: {remaining_size}, PnL: {total_pnl:.2f}, Status: {status}"
            )
            
            return True
            
        except Exception as e:
            bot_logger.error(f"Error updating position exit: {str(e)}", exc_info=True)
            return False
    
    async def update_stop_loss(self, position_id: str, new_stop_loss: float) -> bool:
        """
        Update position stop loss (for trailing)
        
        Args:
            position_id: Position ID
            new_stop_loss: New stop loss price
        
        Returns:
            True if successful
        """
        try:
            from bson import ObjectId
            
            await self.positions_collection.update_one(
                {'_id': ObjectId(position_id)},
                {'$set': {'stop_loss': new_stop_loss}}
            )
            
            bot_logger.info(f"Stop loss updated for position {position_id}: {new_stop_loss}")
            return True
            
        except Exception as e:
            bot_logger.error(f"Error updating stop loss: {str(e)}", exc_info=True)
            return False
    
    async def get_position_summary(self, telegram_user_id: int) -> Dict:
        """
        Get position summary for user
        
        Args:
            telegram_user_id: Telegram user ID
        
        Returns:
            Summary dictionary
        """
        try:
            open_positions = await self.get_open_positions(telegram_user_id)
            
            # Get closed positions (last 10)
            closed_positions = await self.positions_collection.find({
                'telegram_user_id': telegram_user_id,
                'status': 'closed'
            }).sort('exit_time', -1).limit(10).to_list(length=10)
            
            # Calculate statistics
            total_pnl = sum(p.get('pnl', 0) for p in closed_positions)
            winning_trades = len([p for p in closed_positions if p.get('pnl', 0) > 0])
            losing_trades = len([p for p in closed_positions if p.get('pnl', 0) < 0])
            win_rate = (winning_trades / len(closed_positions) * 100) if closed_positions else 0
            
            return {
                'open_positions_count': len(open_positions),
                'open_positions': open_positions,
                'closed_positions_count': len(closed_positions),
                'recent_closed_positions': closed_positions,
                'total_pnl': total_pnl,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate
            }
            
        except Exception as e:
            bot_logger.error(f"Error getting position summary: {str(e)}", exc_info=True)
            return {}
    
    async def sync_with_exchange(self, telegram_user_id: int) -> List[Dict]:
        """
        Synchronize local positions with Delta Exchange
        
        Args:
            telegram_user_id: User ID
        
        Returns:
            List of discrepancies found
        """
        try:
            # Get positions from exchange
            exchange_positions = await delta_client.get_positions()
            
            # Get local open positions
            local_positions = await self.get_open_positions(telegram_user_id)
            
            discrepancies = []
            
            # Check for positions that exist locally but not on exchange
            for local_pos in local_positions:
                product_id = local_pos['product_id']
                found = False
                
                for ex_pos in exchange_positions:
                    if ex_pos.get('product_id') == product_id:
                        found = True
                        
                        # Check if sizes match
                        local_size = local_pos['remaining_size']
                        exchange_size = abs(int(ex_pos.get('size', 0)))
                        
                        if local_size != exchange_size:
                            discrepancies.append({
                                'type': 'size_mismatch',
                                'position_id': str(local_pos['_id']),
                                'symbol': local_pos['symbol'],
                                'local_size': local_size,
                                'exchange_size': exchange_size
                            })
                        break
                
                if not found:
                    discrepancies.append({
                        'type': 'missing_on_exchange',
                        'position_id': str(local_pos['_id']),
                        'symbol': local_pos['symbol']
                    })
            
            if discrepancies:
                bot_logger.warning(f"Found {len(discrepancies)} position discrepancies")
            
            return discrepancies
            
        except Exception as e:
            bot_logger.error(f"Error syncing with exchange: {str(e)}", exc_info=True)
            return []
    
    async def close_position(self, position_id: str, reason: str = "Manual close") -> bool:
        """
        Manually close a position
        
        Args:
            position_id: Position ID
            reason: Reason for closure
        
        Returns:
            True if successful
        """
        try:
            from bson import ObjectId
            
            position = await self.get_position(position_id)
            if not position or position['status'] != 'open':
                bot_logger.warning(f"Position not found or already closed: {position_id}")
                return False
            
            # Close position on exchange
            close_response = await delta_client.close_position(position['product_id'])
            
            if close_response.get('success'):
                # Update database
                await self.positions_collection.update_one(
                    {'_id': ObjectId(position_id)},
                    {
                        '$set': {
                            'status': 'closed',
                            'exit_time': datetime.utcnow(),
                            'remaining_size': 0
                        }
                    }
                )
                
                bot_logger.info(f"Position closed: {position_id} - Reason: {reason}")
                return True
            
            return False
            
        except Exception as e:
            bot_logger.error(f"Error closing position: {str(e)}", exc_info=True)
            return False


# Global position manager instance
position_manager = PositionManager()
