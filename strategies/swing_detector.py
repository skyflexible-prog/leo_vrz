"""
Swing high/low detection for VRZ calculation
"""
from typing import List, Tuple, Dict
from utils.logger import bot_logger


class SwingDetector:
    """Detects swing highs and lows for VRZ zones"""
    
    def __init__(self, left_bars: int = 3, right_bars: int = 3):
        self.left_bars = left_bars
        self.right_bars = right_bars
    
    def is_valid_swing_high(self, candles: List[Dict], index: int) -> Tuple[bool, float, int]:
        """
        Check if candle at index is a valid swing high (resistance)
        
        Returns: (is_valid, price_level, bar_index)
        """
        if index < self.left_bars or index >= len(candles) - self.right_bars:
            return (False, 0.0, index)
        
        pivot_high = candles[index]['high']
        
        # Check left bars
        for i in range(index - self.left_bars, index):
            if candles[i]['high'] >= pivot_high:
                return (False, 0.0, index)
        
        # Check right bars
        for i in range(index + 1, index + self.right_bars + 1):
            if candles[i]['high'] >= pivot_high:
                return (False, 0.0, index)
        
        return (True, pivot_high, index)
    
    def is_valid_swing_low(self, candles: List[Dict], index: int) -> Tuple[bool, float, int]:
        """
        Check if candle at index is a valid swing low (support)
        
        Returns: (is_valid, price_level, bar_index)
        """
        if index < self.left_bars or index >= len(candles) - self.right_bars:
            return (False, 0.0, index)
        
        pivot_low = candles[index]['low']
        
        # Check left bars
        for i in range(index - self.left_bars, index):
            if candles[i]['low'] <= pivot_low:
                return (False, 0.0, index)
        
        # Check right bars
        for i in range(index + 1, index + self.right_bars + 1):
            if candles[i]['low'] <= pivot_low:
                return (False, 0.0, index)
        
        return (True, pivot_low, index)
    
    def detect_all_swings(self, candles: List[Dict]) -> Dict[str, List[Dict]]:
        """Detect all swing highs and lows in candle data"""
        swing_highs = []
        swing_lows = []
        
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
        
        bot_logger.debug(f"Detected {len(swing_highs)} swing highs and {len(swing_lows)} swing lows")
        
        return {
            'resistance_zones': swing_highs,
            'support_zones': swing_lows
        }
      
