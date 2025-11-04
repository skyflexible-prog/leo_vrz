"""
Swing high/low detection for VRZ calculation
"""
from typing import List, Tuple, Dict
from utils.logger import bot_logger


class SwingDetector:
    """Detects swing highs and lows for VRZ zones"""
    
    def __init__(self, left_bars: int = 3, right_bars: int = 3):
        """
        Initialize swing detector
        
        Args:
            left_bars: Number of bars to check before pivot
            right_bars: Number of bars to check after pivot
        """
        self.left_bars = left_bars
        self.right_bars = right_bars
    
    def is_valid_swing_high(self, candles: List[Dict], index: int) -> Tuple[bool, float, int]:
        """
        Check if candle at index is a valid swing high (resistance)
        
        A valid swing high must have:
        - No candle high (including wicks) exceeding pivot high for left_bars before
        - No candle high exceeding pivot high for right_bars after
        - Represents a lower high in downtrend
        
        Args:
            candles: List of OHLC candles
            index: Index to check for swing high
        
        Returns:
            Tuple of (is_valid, price_level, bar_index)
        """
        # Check boundaries
        if index < self.left_bars or index >= len(candles) - self.right_bars:
            return (False, 0.0, index)
        
        pivot_high = candles[index]['high']
        
        # Check left bars - no high should exceed pivot
        for i in range(index - self.left_bars, index):
            if candles[i]['high'] >= pivot_high:
                return (False, 0.0, index)
        
        # Check right bars - no high should exceed pivot
        for i in range(index + 1, index + self.right_bars + 1):
            if candles[i]['high'] >= pivot_high:
                return (False, 0.0, index)
        
        return (True, pivot_high, index)
    
    def is_valid_swing_low(self, candles: List[Dict], index: int) -> Tuple[bool, float, int]:
        """
        Check if candle at index is a valid swing low (support)
        
        A valid swing low must have:
        - No candle low (including wicks) below pivot low for left_bars before
        - No candle low below pivot low for right_bars after
        - Represents a higher low in uptrend
        
        Args:
            candles: List of OHLC candles
            index: Index to check for swing low
        
        Returns:
            Tuple of (is_valid, price_level, bar_index)
        """
        # Check boundaries
        if index < self.left_bars or index >= len(candles) - self.right_bars:
            return (False, 0.0, index)
        
        pivot_low = candles[index]['low']
        
        # Check left bars - no low should be below pivot
        for i in range(index - self.left_bars, index):
            if candles[i]['low'] <= pivot_low:
                return (False, 0.0, index)
        
        # Check right bars - no low should be below pivot
        for i in range(index + 1, index + self.right_bars + 1):
            if candles[i]['low'] <= pivot_low:
                return (False, 0.0, index)
        
        return (True, pivot_low, index)
    
    def detect_all_swings(self, candles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Detect all swing highs and lows in candle data
        
        Args:
            candles: List of OHLC candles
        
        Returns:
            Dictionary with 'resistance_zones' and 'support_zones' lists
        """
        swing_highs = []
        swing_lows = []
        
        # Iterate through valid range
        for i in range(self.left_bars, len(candles) - self.right_bars):
            # Check for swing high
            is_high, high_price, high_idx = self.is_valid_swing_high(candles, i)
            if is_high:
                swing_highs.append({
                    'price': high_price,
                    'index': high_idx,
                    'timestamp': candles[i]['time']
                })
            
            # Check for swing low
            is_low, low_price, low_idx = self.is_valid_swing_low(candles, i)
            if is_low:
                swing_lows.append({
                    'price': low_price,
                    'index': low_idx,
                    'timestamp': candles[i]['time']
                })
        
        bot_logger.debug(
            f"Swing Detection Complete: {len(swing_highs)} resistance zones, "
            f"{len(swing_lows)} support zones detected"
        )
        
        return {
            'resistance_zones': swing_highs,
            'support_zones': swing_lows
        }
    
    def get_recent_swings(self, candles: List[Dict], count: int = 5) -> Dict[str, List[Dict]]:
        """
        Get most recent swing highs and lows
        
        Args:
            candles: List of OHLC candles
            count: Number of recent swings to return
        
        Returns:
            Dictionary with recent resistance and support zones
        """
        all_swings = self.detect_all_swings(candles)
        
        return {
            'resistance_zones': all_swings['resistance_zones'][-count:],
            'support_zones': all_swings['support_zones'][-count:]
        }
        
