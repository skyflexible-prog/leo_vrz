"""
Timeframe conversion and calculation utilities
"""
from typing import Optional
from config.constants import TIMEFRAME_MINUTES


class TimeframeConverter:
    """Utilities for timeframe calculations"""
    
    @staticmethod
    def get_higher_timeframe(base_timeframe: str, multiplier: int = 4) -> str:
        """Get a higher timeframe that is 'multiplier' times the base timeframe"""
        if base_timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"Invalid timeframe: {base_timeframe}")
        
        base_minutes = TIMEFRAME_MINUTES[base_timeframe]
        target_minutes = base_minutes * multiplier
        
        # Find closest matching timeframe
        for tf, minutes in sorted(TIMEFRAME_MINUTES.items(), key=lambda x: x[1]):
            if minutes >= target_minutes:
                return tf
        
        return "1d"
    
    @staticmethod
    def get_lower_timeframe(base_timeframe: str, divisor: int = 4) -> str:
        """Get a lower timeframe that is 'divisor' times smaller than base timeframe"""
        if base_timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"Invalid timeframe: {base_timeframe}")
        
        base_minutes = TIMEFRAME_MINUTES[base_timeframe]
        target_minutes = base_minutes // divisor
        
        closest_tf = "1m"
        for tf, minutes in sorted(TIMEFRAME_MINUTES.items(), key=lambda x: x[1], reverse=True):
            if minutes <= target_minutes:
                return tf
        
        return closest_tf
    
    @staticmethod
    def calculate_auto_timeframe(trading_timeframe: str) -> str:
        """Calculate base timeframe automatically (4x trading timeframe)"""
        return TimeframeConverter.get_higher_timeframe(trading_timeframe, 4)
    
    @staticmethod
    def get_candles_needed(timeframe: str, lookback_bars: int = 100) -> int:
        """Calculate number of candles needed for analysis"""
        return lookback_bars + 50
    
    @staticmethod
    def timeframe_to_seconds(timeframe: str) -> int:
        """Convert timeframe to seconds"""
        return TIMEFRAME_MINUTES.get(timeframe, 60) * 60
      
