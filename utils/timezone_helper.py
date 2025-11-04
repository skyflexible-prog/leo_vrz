"""
Timezone conversion utilities for UTC and IST
"""
from datetime import datetime
import pytz


class TimezoneHelper:
    """Helper class for timezone conversions"""
    
    UTC = pytz.UTC
    IST = pytz.timezone('Asia/Kolkata')
    
    @staticmethod
    def utc_to_ist(utc_time: datetime) -> datetime:
        """Convert UTC datetime to IST"""
        if utc_time.tzinfo is None:
            utc_time = TimezoneHelper.UTC.localize(utc_time)
        return utc_time.astimezone(TimezoneHelper.IST)
    
    @staticmethod
    def ist_to_utc(ist_time: datetime) -> datetime:
        """Convert IST datetime to UTC"""
        if ist_time.tzinfo is None:
            ist_time = TimezoneHelper.IST.localize(ist_time)
        return ist_time.astimezone(TimezoneHelper.UTC)
    
    @staticmethod
    def now_utc() -> datetime:
        """Get current time in UTC"""
        return datetime.now(TimezoneHelper.UTC)
    
    @staticmethod
    def now_ist() -> datetime:
        """Get current time in IST"""
        return datetime.now(TimezoneHelper.IST)
    
    @staticmethod
    def timestamp_to_utc(timestamp: int) -> datetime:
        """Convert Unix timestamp to UTC datetime"""
        return datetime.fromtimestamp(timestamp, tz=TimezoneHelper.UTC)
    
    @staticmethod
    def timestamp_to_ist(timestamp: int) -> datetime:
        """Convert Unix timestamp to IST datetime"""
        utc_time = TimezoneHelper.timestamp_to_utc(timestamp)
        return TimezoneHelper.utc_to_ist(utc_time)
    
    @staticmethod
    def format_ist(dt: datetime) -> str:
        """Format datetime in IST for display"""
        ist_time = TimezoneHelper.utc_to_ist(dt) if dt.tzinfo == TimezoneHelper.UTC else dt
        return ist_time.strftime('%Y-%m-%d %H:%M:%S IST')
    
    @staticmethod
    def format_utc(dt: datetime) -> str:
        """Format datetime in UTC for display"""
        utc_time = TimezoneHelper.ist_to_utc(dt) if dt.tzinfo == TimezoneHelper.IST else dt
        return utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')
      
