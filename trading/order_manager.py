"""
Order Manager - Handles order placement, modification, and tracking
"""
from typing import Dict, List, Optional
from datetime import datetime
from api.delta_client import delta_client
from utils.logger import bot_logger


class OrderManager:
    """
    Manages order lifecycle - placement, modification, cancellation, and tracking
    """
    
    def __init__(self):
        self.active_orders = {}  # Track active orders
        bot_logger.info("Order Manager initialized")
    
    async def place_market_order(self, 
                                 product_id: int, 
                                 size: int, 
                                 side: str,
                                 stop_loss: Optional[float] = None) -> Optional[Dict]:
        """
        Place market order
        
        Args:
            product_id: Delta Exchange product ID
            size: Order size (number of contracts)
            side: 'buy' or 'sell'
            stop_loss: Stop loss price (optional)
        
        Returns:
            Order response dictionary or None
        """
        try:
            bot_logger.info(f"Placing market order: Product={product_id}, Side={side}, Size={size}")
            
            stop_loss_order = None
            if stop_loss:
                stop_loss_order = {
                    'order_type': 'stop_market_order',
                    'stop_price': str(stop_loss),
                    'trail_amount': '0'
                }
            
            response = await delta_client.place_order(
                product_id=product_id,
                size=size,
                side=side,
                order_type='market_order',
                stop_loss_order=stop_loss_order
            )
            
            if response.get('success'):
                order = response.get('result', {})
                order_id = order.get('id')
                
                # Track order
                self.active_orders[order_id] = {
                    'product_id': product_id,
                    'size': size,
                    'side': side,
                    'order_type': 'market_order',
                    'status': 'placed',
                    'timestamp': datetime.utcnow()
                }
                
                bot_logger.info(f"Market order placed successfully: Order ID={order_id}")
                return response
            else:
                bot_logger.error(f"Market order failed: {response}")
                return None
                
        except Exception as e:
            bot_logger.error(f"Error placing market order: {str(e)}", exc_info=True)
            return None
    
    async def place_limit_order(self, 
                               product_id: int, 
                               size: int, 
                               side: str,
                               limit_price: float,
                               stop_loss: Optional[float] = None) -> Optional[Dict]:
        """
        Place limit order
        
        Args:
            product_id: Delta Exchange product ID
            size: Order size
            side: 'buy' or 'sell'
            limit_price: Limit price
            stop_loss: Stop loss price (optional)
        
        Returns:
            Order response or None
        """
        try:
            bot_logger.info(
                f"Placing limit order: Product={product_id}, Side={side}, "
                f"Size={size}, Price={limit_price}"
            )
            
            stop_loss_order = None
            if stop_loss:
                stop_loss_order = {
                    'order_type': 'stop_market_order',
                    'stop_price': str(stop_loss),
                    'trail_amount': '0'
                }
            
            response = await delta_client.place_order(
                product_id=product_id,
                size=size,
                side=side,
                order_type='limit_order',
                limit_price=limit_price,
                stop_loss_order=stop_loss_order
            )
            
            if response.get('success'):
                order = response.get('result', {})
                order_id = order.get('id')
                
                self.active_orders[order_id] = {
                    'product_id': product_id,
                    'size': size,
                    'side': side,
                    'order_type': 'limit_order',
                    'limit_price': limit_price,
                    'status': 'placed',
                    'timestamp': datetime.utcnow()
                }
                
                bot_logger.info(f"Limit order placed successfully: Order ID={order_id}")
                return response
            else:
                bot_logger.error(f"Limit order failed: {response}")
                return None
                
        except Exception as e:
            bot_logger.error(f"Error placing limit order: {str(e)}", exc_info=True)
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            True if successful, False otherwise
        """
        try:
            bot_logger.info(f"Cancelling order: {order_id}")
            
            response = await delta_client.cancel_order(order_id)
            
            if response.get('success'):
                if order_id in self.active_orders:
                    self.active_orders[order_id]['status'] = 'cancelled'
                
                bot_logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                bot_logger.error(f"Order cancellation failed: {response}")
                return False
                
        except Exception as e:
            bot_logger.error(f"Error cancelling order: {str(e)}", exc_info=True)
            return False
    
    async def get_order_status(self, product_id: int) -> List[Dict]:
        """
        Get all open orders for a product
        
        Args:
            product_id: Product ID
        
        Returns:
            List of open orders
        """
        try:
            orders = await delta_client.get_orders(product_id)
            return orders
            
        except Exception as e:
            bot_logger.error(f"Error getting order status: {str(e)}", exc_info=True)
            return []
    
    async def cancel_all_orders(self, product_id: Optional[int] = None) -> int:
        """
        Cancel all open orders
        
        Args:
            product_id: Specific product ID (None for all products)
        
        Returns:
            Number of orders cancelled
        """
        try:
            orders = await delta_client.get_orders(product_id)
            cancelled_count = 0
            
            for order in orders:
                order_id = order.get('id')
                if await self.cancel_order(order_id):
                    cancelled_count += 1
            
            bot_logger.info(f"Cancelled {cancelled_count} orders")
            return cancelled_count
            
        except Exception as e:
            bot_logger.error(f"Error cancelling all orders: {str(e)}", exc_info=True)
            return 0
    
    def get_active_order_count(self) -> int:
        """Get count of active orders"""
        return len([o for o in self.active_orders.values() if o['status'] == 'placed'])
    
    def clear_completed_orders(self):
        """Clear completed/cancelled orders from tracking"""
        self.active_orders = {
            k: v for k, v in self.active_orders.items() 
            if v['status'] == 'placed'
        }
        bot_logger.debug("Cleared completed orders from tracking")


# Global order manager instance
order_manager = OrderManager()
