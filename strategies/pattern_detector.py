"""
Candlestick pattern detection for entry signals
"""
from typing import List, Dict, Optional
from utils.logger import bot_logger


class PatternDetector:
    """Detects two and three candlestick reversal patterns"""
    
    def __init__(self):
        self.min_body_size = 0.0001  # Minimum body size threshold
    
    def _get_body_size(self, candle: Dict) -> float:
        """Calculate candle body size"""
        return abs(candle['close'] - candle['open'])
    
    def _is_bullish(self, candle: Dict) -> bool:
        """Check if candle is bullish"""
        return candle['close'] > candle['open']
    
    def _is_bearish(self, candle: Dict) -> bool:
        """Check if candle is bearish"""
        return candle['close'] < candle['open']
    
    def _get_upper_shadow(self, candle: Dict) -> float:
        """Get upper shadow length"""
        return candle['high'] - max(candle['open'], candle['close'])
    
    def _get_lower_shadow(self, candle: Dict) -> float:
        """Get lower shadow length"""
        return min(candle['open'], candle['close']) - candle['low']
    
    def _is_doji(self, candle: Dict) -> bool:
        """Check if candle is a doji (very small body)"""
        body_size = self._get_body_size(candle)
        total_range = candle['high'] - candle['low']
        return body_size / total_range < 0.1 if total_range > 0 else False
    
    # ==================== TWO-CANDLE PATTERNS ====================
    
    def detect_bullish_engulfing(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Bullish Engulfing pattern
        
        Pattern: Small bearish candle followed by larger bullish candle that engulfs it
        Signal: Strong bullish reversal
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        # Previous candle is bearish, current is bullish
        if not self._is_bearish(prev_candle) or not self._is_bullish(curr_candle):
            return None
        
        # Current candle engulfs previous candle body
        if (curr_candle['open'] <= prev_candle['close'] and 
            curr_candle['close'] >= prev_candle['open'] and
            self._get_body_size(curr_candle) > self._get_body_size(prev_candle)):
            
            return {
                'detected': True,
                'pattern_name': 'bullish_engulfing',
                'direction': 'bullish',
                'confidence': 0.75,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': curr_candle['high'],
                'pattern_low': min(prev_candle['low'], curr_candle['low'])
            }
        
        return None
    
    def detect_bearish_engulfing(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Bearish Engulfing pattern
        
        Pattern: Small bullish candle followed by larger bearish candle that engulfs it
        Signal: Strong bearish reversal
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        # Previous candle is bullish, current is bearish
        if not self._is_bullish(prev_candle) or not self._is_bearish(curr_candle):
            return None
        
        # Current candle engulfs previous candle body
        if (curr_candle['open'] >= prev_candle['close'] and 
            curr_candle['close'] <= prev_candle['open'] and
            self._get_body_size(curr_candle) > self._get_body_size(prev_candle)):
            
            return {
                'detected': True,
                'pattern_name': 'bearish_engulfing',
                'direction': 'bearish',
                'confidence': 0.75,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': max(prev_candle['high'], curr_candle['high']),
                'pattern_low': curr_candle['low']
            }
        
        return None
    
    def detect_piercing_line(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Piercing Line pattern (bullish)
        
        Pattern: Bearish candle followed by bullish candle that opens below and closes above midpoint
        Signal: Bullish reversal
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        if not self._is_bearish(prev_candle) or not self._is_bullish(curr_candle):
            return None
        
        # Current opens below previous close and closes above midpoint
        prev_midpoint = (prev_candle['open'] + prev_candle['close']) / 2
        
        if (curr_candle['open'] < prev_candle['close'] and
            curr_candle['close'] > prev_midpoint and
            curr_candle['close'] < prev_candle['open']):
            
            return {
                'detected': True,
                'pattern_name': 'piercing_line',
                'direction': 'bullish',
                'confidence': 0.70,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': curr_candle['high'],
                'pattern_low': min(prev_candle['low'], curr_candle['low'])
            }
        
        return None
    
    def detect_dark_cloud_cover(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Dark Cloud Cover pattern (bearish)
        
        Pattern: Bullish candle followed by bearish candle that opens above and closes below midpoint
        Signal: Bearish reversal
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        if not self._is_bullish(prev_candle) or not self._is_bearish(curr_candle):
            return None
        
        # Current opens above previous close and closes below midpoint
        prev_midpoint = (prev_candle['open'] + prev_candle['close']) / 2
        
        if (curr_candle['open'] > prev_candle['close'] and
            curr_candle['close'] < prev_midpoint and
            curr_candle['close'] > prev_candle['open']):
            
            return {
                'detected': True,
                'pattern_name': 'dark_cloud_cover',
                'direction': 'bearish',
                'confidence': 0.70,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': max(prev_candle['high'], curr_candle['high']),
                'pattern_low': curr_candle['low']
            }
        
        return None
    
    def detect_bullish_harami(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Bullish Harami pattern
        
        Pattern: Large bearish candle followed by small bullish candle contained within
        Signal: Bullish reversal (moderate strength)
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        if not self._is_bearish(prev_candle) or not self._is_bullish(curr_candle):
            return None
        
        # Current candle body is within previous candle body
        if (curr_candle['open'] >= prev_candle['close'] and
            curr_candle['close'] <= prev_candle['open'] and
            self._get_body_size(curr_candle) < self._get_body_size(prev_candle)):
            
            return {
                'detected': True,
                'pattern_name': 'bullish_harami',
                'direction': 'bullish',
                'confidence': 0.65,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': prev_candle['high'],
                'pattern_low': prev_candle['low']
            }
        
        return None
    
    def detect_bearish_harami(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Bearish Harami pattern
        
        Pattern: Large bullish candle followed by small bearish candle contained within
        Signal: Bearish reversal (moderate strength)
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        if not self._is_bullish(prev_candle) or not self._is_bearish(curr_candle):
            return None
        
        # Current candle body is within previous candle body
        if (curr_candle['open'] <= prev_candle['close'] and
            curr_candle['close'] >= prev_candle['open'] and
            self._get_body_size(curr_candle) < self._get_body_size(prev_candle)):
            
            return {
                'detected': True,
                'pattern_name': 'bearish_harami',
                'direction': 'bearish',
                'confidence': 0.65,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': prev_candle['high'],
                'pattern_low': prev_candle['low']
            }
        
        return None
    
    def detect_tweezer_bottom(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Tweezer Bottom pattern (bullish)
        
        Pattern: Two candles with nearly identical lows
        Signal: Support level, bullish reversal
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        # Both candles have nearly identical lows
        low_diff = abs(prev_candle['low'] - curr_candle['low'])
        avg_low = (prev_candle['low'] + curr_candle['low']) / 2
        
        if low_diff / avg_low < 0.001:  # Within 0.1% tolerance
            return {
                'detected': True,
                'pattern_name': 'tweezer_bottom',
                'direction': 'bullish',
                'confidence': 0.60,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': max(prev_candle['high'], curr_candle['high']),
                'pattern_low': min(prev_candle['low'], curr_candle['low'])
            }
        
        return None
    
    def detect_tweezer_top(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Tweezer Top pattern (bearish)
        
        Pattern: Two candles with nearly identical highs
        Signal: Resistance level, bearish reversal
        """
        if index < 1:
            return None
        
        prev_candle = candles[index - 1]
        curr_candle = candles[index]
        
        # Both candles have nearly identical highs
        high_diff = abs(prev_candle['high'] - curr_candle['high'])
        avg_high = (prev_candle['high'] + curr_candle['high']) / 2
        
        if high_diff / avg_high < 0.001:  # Within 0.1% tolerance
            return {
                'detected': True,
                'pattern_name': 'tweezer_top',
                'direction': 'bearish',
                'confidence': 0.60,
                'candles_involved': [prev_candle, curr_candle],
                'pattern_high': max(prev_candle['high'], curr_candle['high']),
                'pattern_low': min(prev_candle['low'], curr_candle['low'])
            }
        
        return None

    # ==================== THREE-CANDLE PATTERNS ====================
    
    def detect_morning_star(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Morning Star pattern (bullish)
        
        Pattern: Bearish candle, small-bodied star, bullish candle
        Signal: Strong bullish reversal
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]  # Star
        candle3 = candles[index]
        
        # First candle is bearish
        if not self._is_bearish(candle1):
            return None
        
        # Star has small body
        if self._get_body_size(candle2) > self._get_body_size(candle1) * 0.3:
            return None
        
        # Third candle is bullish
        if not self._is_bullish(candle3):
            return None
        
        # Third candle closes well into first candle body
        if candle3['close'] > (candle1['open'] + candle1['close']) / 2:
            return {
                'detected': True,
                'pattern_name': 'morning_star',
                'direction': 'bullish',
                'confidence': 0.80,
                'candles_involved': [candle1, candle2, candle3],
                'pattern_high': candle3['high'],
                'pattern_low': min(candle1['low'], candle2['low'], candle3['low'])
            }
        
        return None
    
    def detect_evening_star(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Evening Star pattern (bearish)
        
        Pattern: Bullish candle, small-bodied star, bearish candle
        Signal: Strong bearish reversal
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]  # Star
        candle3 = candles[index]
        
        # First candle is bullish
        if not self._is_bullish(candle1):
            return None
        
        # Star has small body
        if self._get_body_size(candle2) > self._get_body_size(candle1) * 0.3:
            return None
        
        # Third candle is bearish
        if not self._is_bearish(candle3):
            return None
        
        # Third candle closes well into first candle body
        if candle3['close'] < (candle1['open'] + candle1['close']) / 2:
            return {
                'detected': True,
                'pattern_name': 'evening_star',
                'direction': 'bearish',
                'confidence': 0.80,
                'candles_involved': [candle1, candle2, candle3],
                'pattern_high': max(candle1['high'], candle2['high'], candle3['high']),
                'pattern_low': candle3['low']
            }
        
        return None
    
    def detect_three_white_soldiers(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Three White Soldiers pattern (bullish)
        
        Pattern: Three consecutive long bullish candles
        Signal: Strong bullish trend
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]
        candle3 = candles[index]
        
        # All three candles must be bullish
        if not (self._is_bullish(candle1) and self._is_bullish(candle2) and self._is_bullish(candle3)):
            return None
        
        # Each candle opens within previous body and closes higher
        if not (candle2['open'] > candle1['open'] and candle2['open'] < candle1['close']):
            return None
        if not (candle3['open'] > candle2['open'] and candle3['open'] < candle2['close']):
            return None
        
        # Each candle closes progressively higher
        if not (candle2['close'] > candle1['close'] and candle3['close'] > candle2['close']):
            return None
        
        # Check for minimal shadows (strong bodies)
        for candle in [candle1, candle2, candle3]:
            body_size = self._get_body_size(candle)
            upper_shadow = self._get_upper_shadow(candle)
            lower_shadow = self._get_lower_shadow(candle)
            
            if upper_shadow > body_size * 0.3 or lower_shadow > body_size * 0.3:
                return None
        
        return {
            'detected': True,
            'pattern_name': 'three_white_soldiers',
            'direction': 'bullish',
            'confidence': 0.85,
            'candles_involved': [candle1, candle2, candle3],
            'pattern_high': candle3['high'],
            'pattern_low': min(candle1['low'], candle2['low'], candle3['low'])
        }
    
    def detect_three_black_crows(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Three Black Crows pattern (bearish)
        
        Pattern: Three consecutive long bearish candles
        Signal: Strong bearish trend
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]
        candle3 = candles[index]
        
        # All three candles must be bearish
        if not (self._is_bearish(candle1) and self._is_bearish(candle2) and self._is_bearish(candle3)):
            return None
        
        # Each candle opens within previous body and closes lower
        if not (candle2['open'] < candle1['open'] and candle2['open'] > candle1['close']):
            return None
        if not (candle3['open'] < candle2['open'] and candle3['open'] > candle2['close']):
            return None
        
        # Each candle closes progressively lower
        if not (candle2['close'] < candle1['close'] and candle3['close'] < candle2['close']):
            return None
        
        # Check for minimal shadows (strong bodies)
        for candle in [candle1, candle2, candle3]:
            body_size = self._get_body_size(candle)
            upper_shadow = self._get_upper_shadow(candle)
            lower_shadow = self._get_lower_shadow(candle)
            
            if upper_shadow > body_size * 0.3 or lower_shadow > body_size * 0.3:
                return None
        
        return {
            'detected': True,
            'pattern_name': 'three_black_crows',
            'direction': 'bearish',
            'confidence': 0.85,
            'candles_involved': [candle1, candle2, candle3],
            'pattern_high': max(candle1['high'], candle2['high'], candle3['high']),
            'pattern_low': candle3['low']
        }
    
    def detect_three_outside_up(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Three Outside Up pattern (bullish)
        
        Pattern: Bearish candle, bullish engulfing, continuation bullish
        Signal: Strong bullish reversal
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]
        candle3 = candles[index]
        
        # First candle bearish
        if not self._is_bearish(candle1):
            return None
        
        # Second candle engulfs first (bullish engulfing)
        if not (self._is_bullish(candle2) and 
                candle2['open'] <= candle1['close'] and 
                candle2['close'] >= candle1['open']):
            return None
        
        # Third candle closes higher than second
        if not (self._is_bullish(candle3) and candle3['close'] > candle2['close']):
            return None
        
        return {
            'detected': True,
            'pattern_name': 'three_outside_up',
            'direction': 'bullish',
            'confidence': 0.78,
            'candles_involved': [candle1, candle2, candle3],
            'pattern_high': candle3['high'],
            'pattern_low': min(candle1['low'], candle2['low'], candle3['low'])
        }
    
    def detect_three_outside_down(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Three Outside Down pattern (bearish)
        
        Pattern: Bullish candle, bearish engulfing, continuation bearish
        Signal: Strong bearish reversal
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]
        candle3 = candles[index]
        
        # First candle bullish
        if not self._is_bullish(candle1):
            return None
        
        # Second candle engulfs first (bearish engulfing)
        if not (self._is_bearish(candle2) and 
                candle2['open'] >= candle1['close'] and 
                candle2['close'] <= candle1['open']):
            return None
        
        # Third candle closes lower than second
        if not (self._is_bearish(candle3) and candle3['close'] < candle2['close']):
            return None
        
        return {
            'detected': True,
            'pattern_name': 'three_outside_down',
            'direction': 'bearish',
            'confidence': 0.78,
            'candles_involved': [candle1, candle2, candle3],
            'pattern_high': max(candle1['high'], candle2['high'], candle3['high']),
            'pattern_low': candle3['low']
        }
    
    def detect_abandoned_baby_bullish(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Abandoned Baby Bullish pattern
        
        Pattern: Bearish candle, gap down doji, gap up bullish candle
        Signal: Very strong bullish reversal (rare)
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]  # Doji
        candle3 = candles[index]
        
        # First candle bearish
        if not self._is_bearish(candle1):
            return None
        
        # Middle candle is doji
        if not self._is_doji(candle2):
            return None
        
        # Third candle bullish
        if not self._is_bullish(candle3):
            return None
        
        # Check for gaps (no shadow overlap)
        if candle2['high'] >= candle1['low'] or candle2['high'] >= candle3['low']:
            return None
        
        return {
            'detected': True,
            'pattern_name': 'abandoned_baby_bullish',
            'direction': 'bullish',
            'confidence': 0.90,
            'candles_involved': [candle1, candle2, candle3],
            'pattern_high': candle3['high'],
            'pattern_low': candle2['low']
        }
    
    def detect_abandoned_baby_bearish(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Abandoned Baby Bearish pattern
        
        Pattern: Bullish candle, gap up doji, gap down bearish candle
        Signal: Very strong bearish reversal (rare)
        """
        if index < 2:
            return None
        
        candle1 = candles[index - 2]
        candle2 = candles[index - 1]  # Doji
        candle3 = candles[index]
        
        # First candle bullish
        if not self._is_bullish(candle1):
            return None
        
        # Middle candle is doji
        if not self._is_doji(candle2):
            return None
        
        # Third candle bearish
        if not self._is_bearish(candle3):
            return None
        
        # Check for gaps (no shadow overlap)
        if candle2['low'] <= candle1['high'] or candle2['low'] <= candle3['high']:
            return None
        
        return {
            'detected': True,
            'pattern_name': 'abandoned_baby_bearish',
            'direction': 'bearish',
            'confidence': 0.90,
            'candles_involved': [candle1, candle2, candle3],
            'pattern_high': candle2['high'],
            'pattern_low': candle3['low']
        }
    
    # ==================== SINGLE CANDLE PATTERNS ====================
    
    def detect_hammer(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Hammer pattern (bullish)
        
        Pattern: Small body at top, long lower shadow, minimal upper shadow
        Signal: Bullish reversal at support
        """
        if index < 0:
            return None
        
        candle = candles[index]
        
        body_size = self._get_body_size(candle)
        lower_shadow = self._get_lower_shadow(candle)
        upper_shadow = self._get_upper_shadow(candle)
        total_range = candle['high'] - candle['low']
        
        # Lower shadow at least 2x body size
        # Upper shadow very small
        # Body in upper part of range
        if (lower_shadow >= body_size * 2 and 
            upper_shadow < body_size * 0.3 and
            body_size / total_range < 0.3):
            
            return {
                'detected': True,
                'pattern_name': 'hammer',
                'direction': 'bullish',
                'confidence': 0.70,
                'candles_involved': [candle],
                'pattern_high': candle['high'],
                'pattern_low': candle['low']
            }
        
        return None
    
    def detect_inverted_hammer(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Inverted Hammer pattern (bullish)
        
        Pattern: Small body at bottom, long upper shadow, minimal lower shadow
        Signal: Potential bullish reversal
        """
        if index < 0:
            return None
        
        candle = candles[index]
        
        body_size = self._get_body_size(candle)
        lower_shadow = self._get_lower_shadow(candle)
        upper_shadow = self._get_upper_shadow(candle)
        total_range = candle['high'] - candle['low']
        
        # Upper shadow at least 2x body size
        # Lower shadow very small
        # Body in lower part of range
        if (upper_shadow >= body_size * 2 and 
            lower_shadow < body_size * 0.3 and
            body_size / total_range < 0.3):
            
            return {
                'detected': True,
                'pattern_name': 'inverted_hammer',
                'direction': 'bullish',
                'confidence': 0.65,
                'candles_involved': [candle],
                'pattern_high': candle['high'],
                'pattern_low': candle['low']
            }
        
        return None
    
    def detect_hanging_man(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Hanging Man pattern (bearish)
        
        Pattern: Small body at top, long lower shadow (same as hammer but in uptrend)
        Signal: Bearish reversal at resistance
        """
        if index < 0:
            return None
        
        candle = candles[index]
        
        body_size = self._get_body_size(candle)
        lower_shadow = self._get_lower_shadow(candle)
        upper_shadow = self._get_upper_shadow(candle)
        total_range = candle['high'] - candle['low']
        
        if (lower_shadow >= body_size * 2 and 
            upper_shadow < body_size * 0.3 and
            body_size / total_range < 0.3):
            
            return {
                'detected': True,
                'pattern_name': 'hanging_man',
                'direction': 'bearish',
                'confidence': 0.70,
                'candles_involved': [candle],
                'pattern_high': candle['high'],
                'pattern_low': candle['low']
            }
        
        return None
    
    def detect_shooting_star(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Detect Shooting Star pattern (bearish)
        
        Pattern: Small body at bottom, long upper shadow (same as inverted hammer but in uptrend)
        Signal: Bearish reversal at resistance
        """
        if index < 0:
            return None
        
        candle = candles[index]
        
        body_size = self._get_body_size(candle)
        lower_shadow = self._get_lower_shadow(candle)
        upper_shadow = self._get_upper_shadow(candle)
        total_range = candle['high'] - candle['low']
        
        if (upper_shadow >= body_size * 2 and 
            lower_shadow < body_size * 0.3 and
            body_size / total_range < 0.3):
            
            return {
                'detected': True,
                'pattern_name': 'shooting_star',
                'direction': 'bearish',
                'confidence': 0.70,
                'candles_involved': [candle],
                'pattern_high': candle['high'],
                'pattern_low': candle['low']
            }
        
        return None
    
    # ==================== PATTERN SCANNING ====================
    
    def scan_all_patterns(self, candles: List[Dict], index: int) -> List[Dict]:
        """
        Scan for all pattern types at given index
        
        Args:
            candles: List of OHLC candles
            index: Index to scan for patterns
        
        Returns:
            List of detected patterns
        """
        detected_patterns = []
        
        # Two-candle patterns
        two_candle_detectors = [
            self.detect_bullish_engulfing,
            self.detect_bearish_engulfing,
            self.detect_piercing_line,
            self.detect_dark_cloud_cover,
            self.detect_bullish_harami,
            self.detect_bearish_harami,
            self.detect_tweezer_bottom,
            self.detect_tweezer_top
        ]
        
        # Three-candle patterns
        three_candle_detectors = [
            self.detect_morning_star,
            self.detect_evening_star,
            self.detect_three_white_soldiers,
            self.detect_three_black_crows,
            self.detect_three_outside_up,
            self.detect_three_outside_down,
            self.detect_abandoned_baby_bullish,
            self.detect_abandoned_baby_bearish
        ]
        
        # Single-candle patterns
        single_candle_detectors = [
            self.detect_hammer,
            self.detect_inverted_hammer,
            self.detect_hanging_man,
            self.detect_shooting_star
        ]
        
        # Run all detectors
        for detector in two_candle_detectors + three_candle_detectors + single_candle_detectors:
            try:
                result = detector(candles, index)
                if result and result.get('detected'):
                    detected_patterns.append(result)
            except Exception as e:
                bot_logger.error(f"Pattern detection error in {detector.__name__}: {str(e)}")
        
        return detected_patterns
    
    def get_best_pattern(self, candles: List[Dict], index: int) -> Optional[Dict]:
        """
        Get the highest confidence pattern at given index
        
        Args:
            candles: List of OHLC candles
            index: Index to scan
        
        Returns:
            Pattern with highest confidence or None
        """
        patterns = self.scan_all_patterns(candles, index)
        
        if not patterns:
            return None
        
        # Sort by confidence and return best
        best_pattern = max(patterns, key=lambda p: p['confidence'])
        
        bot_logger.log_pattern_detection(
            best_pattern['pattern_name'],
            "symbol",  # Will be filled by caller
            "timeframe",  # Will be filled by caller
            best_pattern['confidence']
        )
        
        return best_pattern

