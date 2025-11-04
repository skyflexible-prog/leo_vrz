"""
VRZ (Value Rejection Zone) Calculator for Support/Resistance Detection
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from config.settings import settings
from config.constants import ZONE_TYPE_RESISTANCE, ZONE_TYPE_SUPPORT
from strategies.swing_detector import SwingDetector
from database.models import VRZZone
from database.repositories.vrz_repository import vrz_repository
from api.delta_client import delta_client
from utils.logger import bot_logger
from utils.timeframe_converter import TimeframeConverter
from utils.timezone_helper import TimezoneHelper


class VRZCalculator:
    """
    VRZ Support/Resistance Zone Calculator using Multi-Timeframe Analysis
    """
    
    def __init__(self, 
                 base_timeframe: str = "auto",
                 trading_timeframe: str = "15m",
                 buffer_percent: float = None,
                 swing_left_bars: int = None,
                 swing_right_bars: int = None):
        """
        Initialize VRZ Calculator
        
        Args:
            base_timeframe: Timeframe for VRZ calculation ("auto" or specific like "1h")
            trading_timeframe: Timeframe for trade execution
            buffer_percent: Zone buffer percentage (default from settings)
            swing_left_bars: Bars to check before pivot
            swing_right_bars: Bars to check after pivot
        """
        self.trading_timeframe = trading_timeframe
        
        # Auto-calculate base timeframe if set to "auto"
        if base_timeframe == "auto":
            self.base_timeframe = TimeframeConverter.calculate_auto_timeframe(trading_timeframe)
            bot_logger.info(f"Auto-calculated base timeframe: {self.base_timeframe} (4x {trading_timeframe})")
        else:
            self.base_timeframe = base_timeframe
        
        self.buffer_percent = buffer_percent or settings.VRZ_BUFFER_PERCENT
        
        # Initialize swing detector
        left_bars = swing_left_bars or settings.DEFAULT_SWING_LEFT_BARS
        right_bars = swing_right_bars or settings.DEFAULT_SWING_RIGHT_BARS
        self.swing_detector = SwingDetector(left_bars, right_bars)
        
        bot_logger.info(
            f"VRZ Calculator initialized - Base TF: {self.base_timeframe}, "
            f"Trading TF: {self.trading_timeframe}, Buffer: {self.buffer_percent}%"
        )
    
    async def fetch_candles(self, symbol: str, timeframe: str, bars: int = 150) -> List[Dict]:
        """
        Fetch OHLC candles from Delta Exchange
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            bars: Number of bars to fetch
        
        Returns:
            List of OHLC candles
        """
        try:
            # Calculate time range
            now = int(time.time())
            seconds_per_bar = TimeframeConverter.timeframe_to_seconds(timeframe)
            start = now - (bars * seconds_per_bar)
            
            bot_logger.debug(f"Fetching {bars} candles for {symbol} on {timeframe}")
            
            candles = await delta_client.get_ohlc_candles(
                symbol=symbol,
                resolution=timeframe,
                start=start,
                end=now
            )
            
            bot_logger.info(f"Fetched {len(candles)} candles for {symbol} ({timeframe})")
            return candles
            
        except Exception as e:
            bot_logger.error(f"Error fetching candles: {str(e)}", exc_info=True)
            return []
    
    def _calculate_zone_bounds(self, price_level: float) -> tuple:
        """
        Calculate zone upper and lower bounds with buffer
        
        Args:
            price_level: Center price of zone
        
        Returns:
            Tuple of (zone_lower, zone_upper)
        """
        buffer = price_level * (self.buffer_percent / 100)
        zone_upper = price_level + buffer
        zone_lower = price_level - buffer
        
        return (zone_lower, zone_upper)
    
    async def calculate_vrz_zones(self, symbol: str, product_id: int) -> Dict[str, List[Dict]]:
        """
        Calculate VRZ Support and Resistance zones on base timeframe
        
        Args:
            symbol: Trading symbol
            product_id: Delta Exchange product ID
        
        Returns:
            Dictionary with 'resistance_zones' and 'support_zones' lists
        """
        try:
            # Fetch candles for base timeframe
            candles = await self.fetch_candles(symbol, self.base_timeframe, bars=150)
            
            if not candles:
                bot_logger.warning(f"No candles received for {symbol}")
                return {'resistance_zones': [], 'support_zones': []}
            
            # Detect swing highs and lows
            swings = self.swing_detector.detect_all_swings(candles)
            
            resistance_zones = []
            support_zones = []
            
            # Process resistance zones (swing highs)
            for swing_high in swings['resistance_zones']:
                price_level = swing_high['price']
                zone_lower, zone_upper = self._calculate_zone_bounds(price_level)
                
                # Create VRZ zone model
                vrz_zone = VRZZone(
                    symbol=symbol,
                    product_id=product_id,
                    type=ZONE_TYPE_RESISTANCE,
                    price_level=price_level,
                    zone_upper=zone_upper,
                    zone_lower=zone_lower,
                    bar_index=swing_high['index'],
                    timestamp=datetime.fromtimestamp(swing_high['timestamp']),
                    timeframe=self.base_timeframe,
                    status='active'
                )
                
                # Store in database
                zone_id = await vrz_repository.create_zone(vrz_zone)
                
                zone_dict = vrz_zone.dict(by_alias=True)
                zone_dict['_id'] = zone_id
                resistance_zones.append(zone_dict)
            
            # Process support zones (swing lows)
            for swing_low in swings['support_zones']:
                price_level = swing_low['price']
                zone_lower, zone_upper = self._calculate_zone_bounds(price_level)
                
                # Create VRZ zone model
                vrz_zone = VRZZone(
                    symbol=symbol,
                    product_id=product_id,
                    type=ZONE_TYPE_SUPPORT,
                    price_level=price_level,
                    zone_upper=zone_upper,
                    zone_lower=zone_lower,
                    bar_index=swing_low['index'],
                    timestamp=datetime.fromtimestamp(swing_low['timestamp']),
                    timeframe=self.base_timeframe,
                    status='active'
                )
                
                # Store in database
                zone_id = await vrz_repository.create_zone(vrz_zone)
                
                zone_dict = vrz_zone.dict(by_alias=True)
                zone_dict['_id'] = zone_id
                support_zones.append(zone_dict)
            
            bot_logger.info(
                f"VRZ Calculation Complete for {symbol}: "
                f"{len(resistance_zones)} resistance, {len(support_zones)} support zones"
            )
            
            return {
                'resistance_zones': resistance_zones,
                'support_zones': support_zones
            }
            
        except Exception as e:
            bot_logger.error(f"Error calculating VRZ zones: {str(e)}", exc_info=True)
            return {'resistance_zones': [], 'support_zones': []}
    
    async def calculate_entry_timeframe_vrz(self, symbol: str, product_id: int) -> Dict[str, List[Dict]]:
        """
        Calculate VRZ zones on entry/trading timeframe for exit targets
        
        Args:
            symbol: Trading symbol
            product_id: Delta Exchange product ID
        
        Returns:
            Dictionary with entry timeframe VRZ zones
        """
        try:
            # Fetch candles for trading timeframe
            candles = await self.fetch_candles(symbol, self.trading_timeframe, bars=200)
            
            if not candles:
                return {'resistance_zones': [], 'support_zones': []}
            
            # Detect swing highs and lows
            swings = self.swing_detector.detect_all_swings(candles)
            
            resistance_zones = []
            support_zones = []
            
            # Process resistance zones
            for swing_high in swings['resistance_zones']:
                price_level = swing_high['price']
                zone_lower, zone_upper = self._calculate_zone_bounds(price_level)
                
                vrz_zone = VRZZone(
                    symbol=symbol,
                    product_id=product_id,
                    type=ZONE_TYPE_RESISTANCE,
                    price_level=price_level,
                    zone_upper=zone_upper,
                    zone_lower=zone_lower,
                    bar_index=swing_high['index'],
                    timestamp=datetime.fromtimestamp(swing_high['timestamp']),
                    timeframe=self.trading_timeframe,
                    status='active'
                )
                
                zone_id = await vrz_repository.create_zone(vrz_zone)
                zone_dict = vrz_zone.dict(by_alias=True)
                zone_dict['_id'] = zone_id
                resistance_zones.append(zone_dict)
            
            # Process support zones
            for swing_low in swings['support_zones']:
                price_level = swing_low['price']
                zone_lower, zone_upper = self._calculate_zone_bounds(price_level)
                
                vrz_zone = VRZZone(
                    symbol=symbol,
                    product_id=product_id,
                    type=ZONE_TYPE_SUPPORT,
                    price_level=price_level,
                    zone_upper=zone_upper,
                    zone_lower=zone_lower,
                    bar_index=swing_low['index'],
                    timestamp=datetime.fromtimestamp(swing_low['timestamp']),
                    timeframe=self.trading_timeframe,
                    status='active'
                )
                
                zone_id = await vrz_repository.create_zone(vrz_zone)
                zone_dict = vrz_zone.dict(by_alias=True)
                zone_dict['_id'] = zone_id
                support_zones.append(zone_dict)
            
            bot_logger.info(
                f"Entry TF VRZ Calculation for {symbol} ({self.trading_timeframe}): "
                f"{len(resistance_zones)} resistance, {len(support_zones)} support zones"
            )
            
            return {
                'resistance_zones': resistance_zones,
                'support_zones': support_zones
            }
            
        except Exception as e:
            bot_logger.error(f"Error calculating entry timeframe VRZ: {str(e)}", exc_info=True)
            return {'resistance_zones': [], 'support_zones': []}
    
    async def invalidate_zones(self, symbol: str, current_candle: Dict):
        """
        Monitor and invalidate breached VRZ zones
        
        Args:
            symbol: Trading symbol
            current_candle: Latest candle data
        """
        try:
            await vrz_repository.check_and_invalidate(symbol, current_candle)
            
        except Exception as e:
            bot_logger.error(f"Error invalidating zones: {str(e)}", exc_info=True)
    
    async def get_active_zones(self, symbol: str, current_price: float, 
                              max_zones: int = 3) -> Dict[str, List[Dict]]:
        """
        Get active VRZ zones near current price
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            max_zones: Maximum number of zones to return per type
        
        Returns:
            Dictionary with nearest active zones
        """
        try:
            # Get nearest resistance zones (above current price)
            resistance_zones = await vrz_repository.get_nearest_zones(
                symbol=symbol,
                timeframe=self.base_timeframe,
                current_price=current_price,
                zone_type=ZONE_TYPE_RESISTANCE,
                limit=max_zones
            )
            
            # Filter only zones above current price
            resistance_zones = [
                z for z in resistance_zones 
                if z['zone_lower'] > current_price
            ][:max_zones]
            
            # Get nearest support zones (below current price)
            support_zones = await vrz_repository.get_nearest_zones(
                symbol=symbol,
                timeframe=self.base_timeframe,
                current_price=current_price,
                zone_type=ZONE_TYPE_SUPPORT,
                limit=max_zones
            )
            
            # Filter only zones below current price
            support_zones = [
                z for z in support_zones 
                if z['zone_upper'] < current_price
            ][:max_zones]
            
            return {
                'resistance_zones': resistance_zones,
                'support_zones': support_zones
            }
            
        except Exception as e:
            bot_logger.error(f"Error getting active zones: {str(e)}", exc_info=True)
            return {'resistance_zones': [], 'support_zones': []}
    
    def is_price_near_zone(self, price: float, zone: Dict, proximity_percent: float = 0.5) -> bool:
        """
        Check if price is near a VRZ zone
        
        Args:
            price: Price to check
            zone: VRZ zone dictionary
            proximity_percent: Additional proximity buffer percentage
        
        Returns:
            True if price is near zone
        """
        zone_lower = zone['zone_lower']
        zone_upper = zone['zone_upper']
        
        # Add proximity buffer
        proximity_buffer = zone['price_level'] * (proximity_percent / 100)
        extended_lower = zone_lower - proximity_buffer
        extended_upper = zone_upper + proximity_buffer
        
        return extended_lower <= price <= extended_upper
    
    async def update_zones_continuous(self, symbol: str, product_id: int):
        """
        Continuously update VRZ zones (for background task)
        
        Args:
            symbol: Trading symbol
            product_id: Delta Exchange product ID
        """
        try:
            # Fetch latest candle
            candles = await self.fetch_candles(symbol, self.base_timeframe, bars=10)
            
            if candles:
                latest_candle = candles[-1]
                
                # Check and invalidate breached zones
                await self.invalidate_zones(symbol, latest_candle)
                
                # Detect new VRZ zones in recent candles
                recent_swings = self.swing_detector.detect_all_swings(candles)
                
                # Store any new zones (check if they already exist)
                for swing_high in recent_swings['resistance_zones'][-3:]:
                    price_level = swing_high['price']
                    zone_lower, zone_upper = self._calculate_zone_bounds(price_level)
                    
                    vrz_zone = VRZZone(
                        symbol=symbol,
                        product_id=product_id,
                        type=ZONE_TYPE_RESISTANCE,
                        price_level=price_level,
                        zone_upper=zone_upper,
                        zone_lower=zone_lower,
                        bar_index=swing_high['index'],
                        timestamp=datetime.fromtimestamp(swing_high['timestamp']),
                        timeframe=self.base_timeframe,
                        status='active'
                    )
                    
                    await vrz_repository.create_zone(vrz_zone)
                
                for swing_low in recent_swings['support_zones'][-3:]:
                    price_level = swing_low['price']
                    zone_lower, zone_upper = self._calculate_zone_bounds(price_level)
                    
                    vrz_zone = VRZZone(
                        symbol=symbol,
                        product_id=product_id,
                        type=ZONE_TYPE_SUPPORT,
                        price_level=price_level,
                        zone_upper=zone_upper,
                        zone_lower=zone_lower,
                        bar_index=swing_low['index'],
                        timestamp=datetime.fromtimestamp(swing_low['timestamp']),
                        timeframe=self.base_timeframe,
                        status='active'
                    )
                    
                    await vrz_repository.create_zone(vrz_zone)
                
                bot_logger.debug(f"VRZ zones updated for {symbol}")
            
        except Exception as e:
            bot_logger.error(f"Error updating zones continuously: {str(e)}", exc_info=True)
  
