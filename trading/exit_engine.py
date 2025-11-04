"""
Exit Engine - Manages trade exits, targets, and stop loss trailing
"""
from typing import Dict, List, Optional
from datetime import datetime
from config.constants import SIDE_BUY, SIDE_SELL
from api.delta_client import delta_client
from database.repositories.vrz_repository import vrz_repository
from utils.logger import bot_logger


class ExitEngine:
    """
    Exit management engine
    Handles partial exits at targets and stop loss trailing
    """
    
    def __init__(self):
        bot_logger.info("Exit Engine initialized")
    
    async def manage_exits(self, trade: Dict, current_price: float) -> Dict:
        """
        Manage exit logic for open trade
        
        Args:
            trade: Trade dictionary from database
            current_price: Current market price
        
        Returns:
            Updated trade dictionary with exit actions
        """
        try:
            bot_logger.debug(f"Managing exits for {trade['symbol']}: Price={current_price}")
            
            actions = []
            
            # Check if any targets are hit
            for target in trade['targets']:
                if target['level'] not in [e['target_level'] for e in trade.get('exit_details', [])]:
                    # Target not yet hit
                    if self._is_target_hit(current_price, target, trade['side']):
                        # Execute partial exit
                        exit_action = await self._execute_partial_exit(trade, target, current_price)
                        if exit_action:
                            actions.append(exit_action)
            
            # Check if stop loss is hit
            if self._is_stop_loss_hit(current_price, trade['stop_loss'], trade['side']):
                exit_action = await self._execute_stop_loss_exit(trade, current_price)
                if exit_action:
                    actions.append(exit_action)
            
            # Trail stop loss after first target
            if self._should_trail_stop(trade):
                new_stop = self._calculate_trailing_stop(trade, current_price)
                if new_stop:
                    actions.append({
                        'action': 'trail_stop',
                        'new_stop_loss': new_stop
                    })
            
            return {
                'trade_id': trade.get('_id'),
                'actions': actions,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            bot_logger.error(f"Error managing exits: {str(e)}", exc_info=True)
            return {'trade_id': trade.get('_id'), 'actions': [], 'error': str(e)}
    
    def _is_target_hit(self, current_price: float, target: Dict, side: str) -> bool:
        """Check if target price is hit"""
        target_price = target['price']
        
        if side == SIDE_BUY:
            # For long, target hit when price >= target
            return current_price >= target_price
        else:  # SIDE_SELL
            # For short, target hit when price <= target
            return current_price <= target_price
    
    def _is_stop_loss_hit(self, current_price: float, stop_loss: float, side: str) -> bool:
        """Check if stop loss is hit"""
        if side == SIDE_BUY:
            return current_price <= stop_loss
        else:  # SIDE_SELL
            return current_price >= stop_loss
    
    async def _execute_partial_exit(self, trade: Dict, target: Dict, current_price: float) -> Optional[Dict]:
        """Execute partial exit at target"""
        try:
            # Calculate exit quantity
            exit_percentage = target['exit_percentage']
            exit_quantity = int(trade['remaining_size'] * (exit_percentage / 100))
            exit_quantity = max(1, exit_quantity)  # At least 1 contract
            
            bot_logger.info(
                f"Executing partial exit: {trade['symbol']} T{target['level']} - "
                f"{exit_quantity} contracts at {current_price}"
            )
            
            # Place exit order (opposite side)
            exit_side = SIDE_SELL if trade['side'] == SIDE_BUY else SIDE_BUY
            
            order_response = await delta_client.place_order(
                product_id=trade['product_id'],
                size=exit_quantity,
                side=exit_side,
                order_type='market_order'
            )
            
            if order_response.get('success'):
                # Calculate PnL for this exit
                entry_price = trade['entry_price']
                if trade['side'] == SIDE_BUY:
                    pnl = (current_price - entry_price) * exit_quantity
                else:
                    pnl = (entry_price - current_price) * exit_quantity
                
                return {
                    'action': 'partial_exit',
                    'target_level': target['level'],
                    'exit_price': current_price,
                    'exit_quantity': exit_quantity,
                    'remaining_quantity': trade['remaining_size'] - exit_quantity,
                    'pnl': pnl,
                    'order_id': order_response.get('result', {}).get('id'),
                    'timestamp': datetime.utcnow()
                }
            
            return None
            
        except Exception as e:
            bot_logger.error(f"Error executing partial exit: {str(e)}", exc_info=True)
            return None
    
    async def _execute_stop_loss_exit(self, trade: Dict, current_price: float) -> Optional[Dict]:
        """Execute stop loss exit"""
        try:
            bot_logger.warning(
                f"Stop Loss Hit: {trade['symbol']} - "
                f"Closing {trade['remaining_size']} contracts at {current_price}"
            )
            
            # Close entire remaining position
            exit_side = SIDE_SELL if trade['side'] == SIDE_BUY else SIDE_BUY
            
            order_response = await delta_client.place_order(
                product_id=trade['product_id'],
                size=trade['remaining_size'],
                side=exit_side,
                order_type='market_order'
            )
            
            if order_response.get('success'):
                # Calculate PnL
                entry_price = trade['entry_price']
                if trade['side'] == SIDE_BUY:
                    pnl = (current_price - entry_price) * trade['remaining_size']
                else:
                    pnl = (entry_price - current_price) * trade['remaining_size']
                
                bot_logger.log_trade_exit(trade['symbol'], pnl, "Stop Loss")
                
                return {
                    'action': 'stop_loss_exit',
                    'exit_price': current_price,
                    'exit_quantity': trade['remaining_size'],
                    'remaining_quantity': 0,
                    'pnl': pnl,
                    'order_id': order_response.get('result', {}).get('id'),
                    'timestamp': datetime.utcnow()
                }
            
            return None
            
        except Exception as e:
            bot_logger.error(f"Error executing stop loss exit: {str(e)}", exc_info=True)
            return None
    
    def _should_trail_stop(self, trade: Dict) -> bool:
        """Check if stop loss should be trailed"""
        # Trail after first target is hit
        exit_details = trade.get('exit_details', [])
        return len(exit_details) > 0 and trade['remaining_size'] > 0
    
    def _calculate_trailing_stop(self, trade: Dict, current_price: float) -> Optional[float]:
        """Calculate new trailing stop loss"""
        try:
            # Move stop to breakeven after first target
            entry_price = trade['entry_price']
            current_stop = trade['stop_loss']
            
            if trade['side'] == SIDE_BUY:
                # For long, trail stop up
                if current_price > entry_price and current_stop < entry_price:
                    # Move to breakeven
                    new_stop = entry_price
                    bot_logger.info(f"Trailing stop to breakeven: {new_stop}")
                    return new_stop
            else:  # SIDE_SELL
                # For short, trail stop down
                if current_price < entry_price and current_stop > entry_price:
                    # Move to breakeven
                    new_stop = entry_price
                    bot_logger.info(f"Trailing stop to breakeven: {new_stop}")
                    return new_stop
            
            return None
            
        except Exception as e:
            bot_logger.error(f"Error calculating trailing stop: {str(e)}", exc_info=True)
            return None
    
    async def close_all_positions(self, symbol: str = None) -> List[Dict]:
        """
        Emergency close all positions
        
        Args:
            symbol: Specific symbol to close (None for all)
        
        Returns:
            List of closed position details
        """
        try:
            positions = await delta_client.get_positions()
            closed_positions = []
            
            for position in positions:
                position_symbol = position.get('product', {}).get('symbol')
                
                if symbol and position_symbol != symbol:
                    continue
                
                product_id = position.get('product_id')
                close_response = await delta_client.close_position(product_id)
                
                if close_response.get('success'):
                    closed_positions.append({
                        'symbol': position_symbol,
                        'product_id': product_id,
                        'size': position.get('size'),
                        'timestamp': datetime.utcnow()
                    })
                    bot_logger.warning(f"Emergency closed position: {position_symbol}")
            
            return closed_positions
            
        except Exception as e:
            bot_logger.error(f"Error closing all positions: {str(e)}", exc_info=True)
            return []


# Global exit engine instance
exit_engine = ExitEngine()
