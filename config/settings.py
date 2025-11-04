"""
Configuration settings loaded from environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_LOG_CHAT_ID: Optional[str] = None
    
    # Delta Exchange API Settings
    DELTA_API_KEY: str
    DELTA_API_SECRET: str
    DELTA_BASE_URL: str = "https://api.india.delta.exchange"
    
    # MongoDB Settings
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "delta_vrz_bot"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 10000
    
    # Trading Settings
    DEFAULT_BASE_TIMEFRAME: str = "1h"
    DEFAULT_TRADING_TIMEFRAME: str = "15m"
    DEFAULT_SWING_LEFT_BARS: int = 3
    DEFAULT_SWING_RIGHT_BARS: int = 3
    VRZ_BUFFER_PERCENT: float = 0.3
    MIN_RISK_REWARD_RATIO: float = 1.5
    
    # Stop Loss Settings
    DEFAULT_STOP_LOSS_PIPS: int = 10
    STOP_LOSS_PIP_OPTIONS: List[int] = [5, 10]
    
    # Target Settings
    MAX_VRZ_ZONES: int = 3
    RR_TARGET_OPTIONS: List[float] = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    # Asset Selection
    TOP_MOVERS_LIMIT: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_TELEGRAM_LOGGING: bool = True
    
    # Database Cleanup
    VRZ_RETENTION_DAYS: int = 30
    TRADE_RETENTION_DAYS: int = 90
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
