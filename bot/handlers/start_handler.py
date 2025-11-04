"""
Start and help command handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import bot_keyboards  # ← Updated import
from database.repositories.user_settings_repository import user_settings_repository
from utils.logger import bot_logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        bot_logger.info(f"Start command from user {user.id} ({user.username})")
        
        # Get or create user settings
        user_settings = await user_settings_repository.get_user_settings(user.id)
        
        welcome_message = f"""
👋 **Welcome to Delta VRZ Trading Bot!**

Hello {user.first_name}! 

This bot helps you trade futures on Delta Exchange India using VRZ (Value Rejection Zone) strategy with candlestick pattern recognition.

**Features:**
✅ Multi-timeframe VRZ Support/Resistance detection
✅ 20+ Candlestick pattern recognition
✅ Automated entry signal generation
✅ Risk-Reward ratio management
✅ Multiple target exits (Zone or RR-based)
✅ Trailing stop loss
✅ Position tracking and management

**Quick Setup:**
1. Use ⚙️ **Settings** to configure your strategy
2. Select 🎯 **Select Asset** to choose trading instruments
3. Click ▶️ **Start Bot** to begin automated trading

**Current Status:** {'🟢 Active' if user_settings.get('is_active') else '🔴 Inactive'}

Use the menu below to navigate 👇
"""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=bot_keyboards.main_menu()
        )
        
    except Exception as e:
        bot_logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        help_text = """
📚 **VRZ Trading Bot Help**

**Main Commands:**
• `/start` - Start the bot and show main menu
• `/help` - Show this help message
• `/settings` - Configure trading parameters
• `/status` - View active VRZ zones and positions
• `/positions` - View open positions
• `/history` - View trade history

**Strategy Explanation:**

**VRZ (Value Rejection Zone):**
- Support and Resistance levels calculated from swing highs/lows
- Base timeframe (default 1h) for VRZ calculation
- Trading timeframe (default 15m) for entry signals
- Zones have ±0.3% buffer by default

**Entry Logic:**
1. Bot monitors price near VRZ zones
2. Detects candlestick reversal patterns
3. Validates Risk-Reward ratio (min 1:1.5)
4. Places trade with stop loss and targets

**Exit Logic:**
- Multiple targets (T1, T2, T3) based on zones or RR
- Partial exits at each target level
- Trailing stop loss after T1
- Full exit at final target or stop loss

**Settings Configuration:**
⏰ **Timeframes** - Set base and trading timeframes
📦 **Lot Size** - Position size per trade
🛑 **Stop Loss** - Pips beyond pattern high/low
🎯 **Targets** - Zone-based or RR-based
📝 **Order Type** - Market or Limit orders

**Asset Selection:**
📈 **Top Gainers** - Trade top 10 gaining assets
📉 **Top Losers** - Trade top 10 losing assets
🔄 **Both** - Trade both gainers and losers
🌐 **All Futures** - Trade all available futures
✍️ **Individual** - Select specific assets

**Need Support?**
Contact: @your_support_handle
Docs: docs.delta.exchange
"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    except Exception as e:
        bot_logger.error(f"Error in help command: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again.")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    try:
        user_id = update.effective_user.id
        
        # Deactivate bot for user
        await user_settings_repository.toggle_active_status(user_id, False)
        
        bot_logger.info(f"Bot stopped for user {user_id}")
        
        await update.message.reply_text(
            "🔴 **Bot Stopped**\n\n"
            "All automated trading has been disabled.\n"
            "Your open positions are still active.\n\n"
            "Use ▶️ **Start Bot** to resume automated trading.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot_logger.error(f"Error in stop command: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again.")
      
