"""
Comprehensive logging system with Telegram integration
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path


class TelegramLogHandler(logging.Handler):
    """Custom handler to send critical logs to Telegram"""
    
    def __init__(self, bot=None, chat_id=None):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id
    
    def emit(self, record):
        if self.bot and self.chat_id:
            try:
                log_message = self.format(record)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            self.bot.send_message(
                                chat_id=self.chat_id,
                                text=f"🔴 {log_message[:4000]}"
                            )
                        )
                except:
                    pass
            except:
                pass


class BotLogger:
    """Main logging class for the trading bot"""
    
    def __init__(self, name: str = "DeltaVRZBot", log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.telegram_handler: Optional[TelegramLogHandler] = None
    
    def add_telegram_handler(self, bot, chat_id: str):
        """Add Telegram logging handler"""
        self.telegram_handler = TelegramLogHandler(bot, chat_id)
        self.telegram_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        self.telegram_handler.setFormatter(formatter)
        self.logger.addHandler(self.telegram_handler)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str, exc_info=False):
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info=False):
        self.logger.critical(message, exc_info=exc_info)
    
    def log_api_call(self, endpoint: str, method: str, params: dict, response: dict):
        """Log API calls with details"""
        self.logger.debug(f"API Call: {method} {endpoint}")
        self.logger.debug(f"Parameters: {params}")
        self.logger.debug(f"Response: {response}")
    
    def log_vrz_detection(self, zone_type: str, price: float, timeframe: str, symbol: str):
        """Log VRZ zone detection"""
        self.logger.info(
            f"VRZ Detected - Type: {zone_type.upper()}, "
            f"Price: {price}, Timeframe: {timeframe}, Symbol: {symbol}"
        )
    
    def log_pattern_detection(self, pattern: str, symbol: str, timeframe: str, confidence: float):
        """Log candlestick pattern detection"""
        self.logger.info(
            f"Pattern Detected - {pattern.upper()}, "
            f"Symbol: {symbol}, TF: {timeframe}, Confidence: {confidence:.2%}"
        )
    
    def log_entry_signal(self, signal: dict):
        """Log entry signal generation"""
        self.logger.info(
            f"Entry Signal - Symbol: {signal.get('symbol')}, "
            f"Side: {signal.get('side')}, Price: {signal.get('entry_price')}, "
            f"SL: {signal.get('stop_loss')}, RR: {signal.get('risk_reward')}"
        )
    
    def log_order_placed(self, order_id: str, symbol: str, side: str, quantity: int, price: float):
        """Log order placement"""
        self.logger.info(
            f"Order Placed - ID: {order_id}, Symbol: {symbol}, "
            f"Side: {side.upper()}, Qty: {quantity}, Price: {price}"
        )
    
    def log_trade_exit(self, symbol: str, pnl: float, reason: str):
        """Log trade exit"""
        pnl_emoji = "✅" if pnl > 0 else "❌"
        self.logger.info(
            f"Trade Closed {pnl_emoji} - Symbol: {symbol}, "
            f"PnL: {pnl:.2f}, Reason: {reason}"
        )


# Global logger instance
bot_logger = BotLogger()
  
