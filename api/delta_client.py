"""
Delta Exchange India API Client with authentication
"""
import hmac
import hashlib
import time
from typing import Optional, Dict, List, Any
import httpx
from config.settings import settings
from utils.logger import bot_logger


class DeltaExchangeClient:
    """Client for Delta Exchange India API"""
    
    def __init__(self):
        self.base_url = settings.DELTA_BASE_URL
        self.api_key = settings.DELTA_API_KEY
        self.api_secret = settings.DELTA_API_SECRET
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_signature(self, method: str, endpoint: str, payload: str = "") -> Dict[str, str]:
        """Generate HMAC-SHA256 signature for authentication"""
        timestamp = str(int(time.time()))
        signature_data = method + timestamp + endpoint + payload
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'DeltaVRZBot/1.0'
        }
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                      data: Optional[Dict] = None, authenticated: bool = False) -> Dict:
        """Make HTTP request to Delta Exchange API"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if authenticated:
            payload = ""
            if data:
                import json
                payload = json.dumps(data)
            headers.update(self._generate_signature(method, endpoint, payload))
        
        try:
            if method == "GET":
                response = await self.client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await self.client.post(url, json=data, headers=headers)
            elif method == "DELETE":
                response = await self.client.delete(url, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            bot_logger.log_api_call(endpoint, method, params or data, result)
            return result
            
        except Exception as e:
            bot_logger.error(f"API request failed: {method} {endpoint} - {str(e)}", exc_info=True)
            raise
    
    async def get_products(self) -> List[Dict]:
        """Get all available products"""
        response = await self._request("GET", "/v2/products")
        return response.get('result', [])
    
    async def get_product_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get product details by symbol"""
        response = await self._request("GET", f"/v2/products/{symbol}")
        return response.get('result')
    
    async def get_tickers(self) -> List[Dict]:
        """Get all tickers for top gainers/losers calculation"""
        response = await self._request("GET", "/v2/tickers")
        return response.get('result', [])
    
    async def get_top_movers(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """Get top gainers and losers"""
        tickers = await self.get_tickers()
        
        futures = []
        for ticker in tickers:
            if ticker.get('product_type') == 'future':
                try:
                    change_24h = float(ticker.get('change_24h', 0))
                    futures.append({
                        'symbol': ticker.get('symbol'),
                        'product_id': ticker.get('product_id'),
                        'mark_price': ticker.get('mark_price'),
                        'change_24h': change_24h,
                        'volume_24h': ticker.get('volume')
                    })
                except:
                    continue
        
        sorted_futures = sorted(futures, key=lambda x: x['change_24h'], reverse=True)
        
        return {
            'top_gainers': sorted_futures[:limit],
            'top_losers': sorted_futures[-limit:][::-1]
        }
    
    async def get_ohlc_candles(self, symbol: str, resolution: str, start: int, end: int) -> List[Dict]:
        """Get OHLC candlestick data"""
        params = {'resolution': resolution, 'start': start, 'end': end}
        response = await self._request("GET", f"/v2/history/candles", params=params)
        candles = response.get('result', [])
        
        formatted_candles = []
        for candle in candles:
            formatted_candles.append({
                'time': candle['time'],
                'open': float(candle['open']),
                'high': float(candle['high']),
                'low': float(candle['low']),
                'close': float(candle['close']),
                'volume': float(candle['volume'])
            })
        
        return formatted_candles
    
    async def get_wallet_balances(self) -> List[Dict]:
        """Get account wallet balances"""
        response = await self._request("GET", "/v2/wallet/balances", authenticated=True)
        return response.get('result', [])
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        response = await self._request("GET", "/v2/positions", authenticated=True)
        return response.get('result', [])
    
    async def get_orders(self, product_id: Optional[int] = None) -> List[Dict]:
        """Get open orders"""
        params = {}
        if product_id:
            params['product_id'] = product_id
        response = await self._request("GET", "/v2/orders", params=params, authenticated=True)
        return response.get('result', [])
    
    async def place_order(self, product_id: int, size: int, side: str, 
                         order_type: str = "market_order", 
                         limit_price: Optional[float] = None,
                         stop_loss_order: Optional[Dict] = None) -> Dict:
        """Place an order"""
        order_data = {
            'product_id': product_id,
            'size': size,
            'side': side,
            'order_type': order_type
        }
        
        if order_type == "limit_order" and limit_price:
            order_data['limit_price'] = str(limit_price)
        
        if stop_loss_order:
            order_data['stop_loss_order'] = stop_loss_order
        
        response = await self._request("POST", "/v2/orders", data=order_data, authenticated=True)
        
        if response.get('success'):
            order = response.get('result', {})
            bot_logger.log_order_placed(
                order.get('id', 'N/A'),
                order.get('product', {}).get('symbol', 'N/A'),
                side, size, limit_price or 0
            )
        
        return response
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        response = await self._request("DELETE", f"/v2/orders/{order_id}", authenticated=True)
        return response
    
    async def close_position(self, product_id: int) -> Dict:
        """Close a position using market order"""
        positions = await self.get_positions()
        
        for position in positions:
            if position.get('product_id') == product_id:
                size = abs(int(position.get('size', 0)))
                side = 'sell' if float(position.get('size', 0)) > 0 else 'buy'
                
                return await self.place_order(
                    product_id=product_id, size=size, side=side, order_type='market_order'
                )
        
        return {'success': False, 'error': 'Position not found'}
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global client instance
delta_client = DeltaExchangeClient()
