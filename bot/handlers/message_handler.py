"""
Message and button press handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.settings_handler import settings_command
from bot.handlers.asset_selection import asset_selection_command
from bot.handlers.status_handler import status_command, positions_command
from bot.handlers.start_handler import start_command, help_command, stop_command
from database.repositories.user_settings_repository import user_settings_repository
from utils.logger import bot_logger


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    try:
        text = update.message.text
        user_id = update.effective_user.id
        
        # Check if bot is awaiting specific input
        awaiting = context.user_data.get('awaiting')
        
        if awaiting == 'lot_size':
            # Handle custom lot size input
            try:
                lot_size = int(text)
                if lot_size > 0:
                    await user_settings_repository.update_lot_size(user_id, lot_size)
                    await update.message.reply_text(
                        f"✅ **Lot Size Updated!**\n\nLot Size: `{lot_size}` contracts",
                        parse_mode='Markdown'
                    )
                    context.user_data.pop('awaiting', None)
                else:
                    await update.message.reply_text("❌ Please enter a positive number.")
            except ValueError:
                await update.message.reply_text("❌ Invalid number. Please enter a valid lot size.")
        
        elif awaiting == 'asset_symbols':
            # Handle individual asset symbols
            symbols = [s.strip().upper() for s in text.split(',')]
            await user_settings_repository.update_selected_assets(user_id, symbols)
            await user_settings_repository.update_asset_selection_mode(user_id, 'individual')
            
            await update.message.reply_text(
                f"✅ **Assets Selected!**\n\n"
                f"Symbols: `{', '.join(symbols)}`",
                parse_mode='Markdown'
            )
            context.user_data.pop('awaiting', None)
        
        else:
            # Handle button presses (text from reply keyboard)
            await handle_button_press(update, context)
    
    except Exception as e:
        bot_logger.error(f"Error handling message: {str(e)}", exc_info=True)
        await update.message.reply_text("An error occurred. Please try again.")


async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reply keyboard button presses"""
    text = update.message.text
    
    try:
        if text == "⚙️ Settings":
            await settings_command(update, context)
        
        elif text == "📊 Status":
            await status_command(update, context)
        
        elif text == "🎯 Select Asset":
            await asset_selection_command(update, context)
        
        elif text == "📈 Positions":
            await positions_command(update, context)
        
        elif text == "📋 Trade History":
            await handle_trade_history(update, context)
        
        elif text == "🔄 Sync":
            await handle_sync(update, context)
        
        elif text == "▶️ Start Bot":
            await handle_start_bot(update, context)
        
        elif text == "⏸ Stop Bot":
            await stop_command(update, context)
        
        else:
            await update.message.reply_text(
                "Use the menu buttons below or /help for available commands."
            )
    
    except Exception as e:
        bot_logger.error(f"Error handling button press: {str(e)}", exc_info=True)


async def handle_trade_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trade history request"""
    try:
        from database.repositories.trade_repository import trade_repository
        from utils.timezone_helper import TimezoneHelper
        
        user_id = update.effective_user.id
        
        # Get trade statistics
        stats = await trade_repository.get_trade_statistics(user_id, days=30)
        
        # Get recent closed trades
        recent_trades = await trade_repository.get_closed_trades(user_id, limit=10)
        
        message = f"""
📋 **Trade History (Last 30 Days)**

**Statistics:**
Total Trades: `{stats.get('total_trades', 0)}`
Win Rate: `{stats.get('win_rate', 0):.1f}%`
Total PnL: `{stats.get('total_pnl', 0):+.2f}`
Profit Factor: `{stats.get('profit_factor', 0):.2f}`

**Best Trade:** `{stats.get('best_trade', 0):+.2f}`
**Worst Trade:** `{stats.get('worst_trade', 0):+.2f}`
**Avg Win:** `{stats.get('avg_win', 0):.2f}`
**Avg Loss:** `{stats.get('avg_loss', 0):.2f}`

**Recent Trades:**
"""
        
        if recent_trades:
            for trade in recent_trades[:5]:
                pnl_emoji = "✅" if trade.get('pnl', 0) > 0 else "❌"
                side_emoji = "🟢" if trade['side'] == 'buy' else "🔴"
                
                message += f"\n{pnl_emoji} {side_emoji} {trade['symbol']}"
                message += f"\n  PnL: `{trade.get('pnl', 0):+.2f}`"
                message += f"\n  Pattern: `{trade['entry_pattern']}`\n"
        else:
            message += "\nNo trades yet.\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        bot_logger.error(f"Error fetching trade history: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error fetching trade history.")


async def handle_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sync request"""
    try:
        from trading.position_manager import position_manager
        
        user_id = update.effective_user.id
        
        await update.message.reply_text("🔄 Syncing with Delta Exchange...")
        
        # Sync positions
        discrepancies = await position_manager.sync_with_exchange(user_id)
        
        if discrepancies:
            message = f"⚠️ **Sync Complete - Issues Found**\n\n"
            message += f"Found {len(discrepancies)} discrepancies:\n\n"
            
            for disc in discrepancies[:5]:
                message += f"• {disc['type']}: {disc.get('symbol', 'Unknown')}\n"
        else:
            message = "✅ **Sync Complete**\n\nAll positions are synchronized."
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        bot_logger.error(f"Error syncing: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error during synchronization.")


async def handle_start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start bot button"""
    try:
        user_id = update.effective_user.id
        
        # Activate bot for user
        await user_settings_repository.toggle_active_status(user_id, True)
        
        bot_logger.info(f"Bot started for user {user_id}")
        
        await update.message.reply_text(
            "🟢 **Bot Started!**\n\n"
            "Automated trading is now active.\n"
            "The bot will monitor VRZ zones and execute trades based on your settings.\n\n"
            "Use /status to monitor activity.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot_logger.error(f"Error starting bot: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error starting bot.")
      
