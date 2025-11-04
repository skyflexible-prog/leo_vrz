"""
Main Telegram bot initialization and setup
"""
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.settings import settings
from utils.logger import bot_logger
from bot.handlers.start_handler import start_command, help_command, stop_command
from bot.handlers.settings_handler import (
    settings_command, handle_timeframes_setting, handle_timeframe_selection,
    handle_lot_size_setting, handle_lot_size_selection, handle_stop_loss_setting,
    handle_stop_loss_selection, handle_target_setting, handle_target_type_selection,
    handle_rr_level_selection, handle_order_type_setting, handle_order_type_selection
)
from bot.handlers.asset_selection import asset_selection_command, handle_asset_mode_selection
from bot.handlers.status_handler import status_command, positions_command
from bot.handlers.callback_handler import handle_callback_query
from bot.handlers.message_handler import handle_message, handle_button_press


class TelegramBot:
    """Main Telegram bot class"""
    
    def __init__(self):
        self.application = None
        self.bot = None
        bot_logger.info("Telegram bot initializing...")
    
    async def initialize(self):
        """Initialize bot application"""
        try:
            # Create application
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            self.bot = self.application.bot
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("help", help_command))
            self.application.add_handler(CommandHandler("stop", stop_command))
            self.application.add_handler(CommandHandler("settings", settings_command))
            self.application.add_handler(CommandHandler("status", status_command))
            self.application.add_handler(CommandHandler("positions", positions_command))
            
            # Add callback query handler
            self.application.add_handler(CallbackQueryHandler(handle_callback_query))
            
            # Add message handlers
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            # Add Telegram logging if configured
            if settings.ENABLE_TELEGRAM_LOGGING and settings.TELEGRAM_LOG_CHAT_ID:
                bot_logger.add_telegram_handler(self.bot, settings.TELEGRAM_LOG_CHAT_ID)
            
            bot_logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            bot_logger.error(f"Failed to initialize Telegram bot: {str(e)}", exc_info=True)
            raise
    
    async def start(self):
        """Start the bot"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
            
            bot_logger.info("Telegram bot started and polling for updates")
            
        except Exception as e:
            bot_logger.error(f"Failed to start Telegram bot: {str(e)}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop the bot"""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            bot_logger.info("Telegram bot stopped")
            
        except Exception as e:
            bot_logger.error(f"Error stopping Telegram bot: {str(e)}", exc_info=True)
    
    def get_bot(self):
        """Get bot instance"""
        return self.bot


# Global bot instance
telegram_bot = TelegramBot()
