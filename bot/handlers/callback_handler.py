"""
Unified callback query handler
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.settings_handler import (
    settings_command, handle_timeframes_setting, handle_timeframe_selection,
    handle_lot_size_setting, handle_lot_size_selection, handle_stop_loss_setting,
    handle_stop_loss_selection, handle_target_setting, handle_target_type_selection,
    handle_rr_level_selection, handle_order_type_setting, handle_order_type_selection
)
from bot.handlers.asset_selection import asset_selection_command, handle_asset_mode_selection
from bot.handlers.status_handler import status_command
from utils.logger import bot_logger


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Unified callback query handler - routes callbacks to appropriate handlers
    """
    query = update.callback_query
    data = query.data
    
    bot_logger.debug(f"Callback received: {data} from user {update.effective_user.id}")
    
    try:
        # Settings callbacks
        if data == "settings_timeframes":
            await handle_timeframes_setting(update, context)
        
        elif data.startswith("tf_"):
            await handle_timeframe_selection(update, context)
        
        elif data == "settings_lot_size":
            await handle_lot_size_setting(update, context)
        
        elif data.startswith("lot_"):
            await handle_lot_size_selection(update, context)
        
        elif data == "settings_stop_loss":
            await handle_stop_loss_setting(update, context)
        
        elif data.startswith("sl_pips_"):
            await handle_stop_loss_selection(update, context)
        
        elif data == "settings_targets":
            await handle_target_setting(update, context)
        
        elif data.startswith("target_type_"):
            await handle_target_type_selection(update, context)
        
        elif data.startswith("rr_") or data.startswith("zone_count_"):
            await handle_rr_level_selection(update, context)
        
        elif data == "settings_order_type":
            await handle_order_type_setting(update, context)
        
        elif data.startswith("order_type_"):
            await handle_order_type_selection(update, context)
        
        # Asset selection callbacks
        elif data.startswith("asset_"):
            await handle_asset_mode_selection(update, context)
        
        # Navigation callbacks
        elif data == "back_main":
            await query.answer()
            await query.message.delete()
        
        elif data == "back_settings":
            await settings_command(update, context)
        
        elif data == "back_targets":
            await handle_target_setting(update, context)
        
        else:
            await query.answer("Unknown action")
            bot_logger.warning(f"Unhandled callback: {data}")
    
    except Exception as e:
        bot_logger.error(f"Error handling callback {data}: {str(e)}", exc_info=True)
        await query.answer("An error occurred. Please try again.")
      
