"""
Settings configuration handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import bot_keyboards  # ← Updated import
from database.repositories.user_settings_repository import user_settings_repository
from utils.logger import bot_logger


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    try:
        user_id = update.effective_user.id
        user_settings = await user_settings_repository.get_user_settings(user_id)
        
        settings_text = f"""
⚙️ **Trading Settings**

**Current Configuration:**

⏰ **Timeframes:**
  • Base TF: `{user_settings.get('base_timeframe', 'auto')}`
  • Trading TF: `{user_settings.get('trading_timeframe', '15m')}`

📦 **Position Size:**
  • Lot Size: `{user_settings.get('lot_size', 1)}`

🛑 **Risk Management:**
  • Stop Loss: `{user_settings.get('stop_loss_pips', 10)} pips`
  • Min RR Ratio: `1:1.5`

🎯 **Targets:**
  • Type: `{user_settings.get('target_type', 'rr').upper()}`
  • Levels: `{user_settings.get('target_levels', [1.5, 2.0, 2.5])}`

📝 **Order Type:**
  • Type: `{user_settings.get('order_type', 'market_order').replace('_', ' ').title()}`

🔧 **Advanced:**
  • Max VRZ Zones: `{user_settings.get('max_vrz_zones', 3)}`
  • Swing Bars: `{user_settings.get('swing_left_bars', 3)}L / {user_settings.get('swing_right_bars', 3)}R`

Select an option below to modify:
"""
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                settings_text,
                parse_mode='Markdown',
                reply_markup=bot_keyboards.settings_menu()
            )
        else:
            await update.message.reply_text(
                settings_text,
                parse_mode='Markdown',
                reply_markup=bot_keyboards.settings_menu()
            )
        
    except Exception as e:
        bot_logger.error(f"Error in settings command: {str(e)}", exc_info=True)


async def handle_timeframes_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe settings"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "⏰ **Select Base Timeframe**\n\n"
        "Base timeframe is used for VRZ calculation.\n"
        "Choose 'Auto' for 4x your trading timeframe.",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.timeframe_selection('base')
    )


async def handle_timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe selection callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    tf_type = data[1]  # 'base' or 'trading'
    tf_value = data[2]
    
    user_id = update.effective_user.id
    user_settings = await user_settings_repository.get_user_settings(user_id)
    
    if tf_type == 'base':
        # Store base timeframe selection temporarily
        context.user_data['base_timeframe'] = tf_value
        
        await query.message.edit_text(
            f"✅ Base Timeframe: **{tf_value}**\n\n"
            "⏰ **Now Select Trading Timeframe**\n\n"
            "Trading timeframe is used for entry signals.",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.timeframe_selection('trading')
        )
    
    elif tf_type == 'trading':
        # Update both timeframes
        base_tf = context.user_data.get('base_timeframe', 'auto')
        trading_tf = tf_value
        
        await user_settings_repository.update_timeframes(user_id, base_tf, trading_tf)
        
        await query.message.edit_text(
            f"✅ **Timeframes Updated!**\n\n"
            f"Base TF: `{base_tf}`\n"
            f"Trading TF: `{trading_tf}`",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.settings_menu()
        )
        
        bot_logger.info(f"User {user_id} updated timeframes: {base_tf}/{trading_tf}")


async def handle_lot_size_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lot size settings"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "📦 **Select Lot Size**\n\n"
        "This is the number of contracts per trade.",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.lot_size_selection()
    )


async def handle_lot_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle lot size selection callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    
    if data[1] == 'custom':
        context.user_data['awaiting'] = 'lot_size'
        await query.message.edit_text(
            "📦 **Enter Custom Lot Size**\n\n"
            "Send a number (e.g., 10, 25, 100):",
            parse_mode='Markdown'
        )
    else:
        lot_size = int(data[1])
        user_id = update.effective_user.id
        
        await user_settings_repository.update_lot_size(user_id, lot_size)
        
        await query.message.edit_text(
            f"✅ **Lot Size Updated!**\n\n"
            f"Lot Size: `{lot_size}` contracts",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.settings_menu()
        )
        
        bot_logger.info(f"User {user_id} updated lot size: {lot_size}")


async def handle_stop_loss_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stop loss settings"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "🛑 **Select Stop Loss Distance**\n\n"
        "Stop loss will be placed this many pips beyond\n"
        "the pattern high/low.",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.stop_loss_pips_selection()
    )


async def handle_stop_loss_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stop loss selection callback"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    pips = int(data[2])
    
    user_id = update.effective_user.id
    await user_settings_repository.update_stop_loss_pips(user_id, pips)
    
    await query.message.edit_text(
        f"✅ **Stop Loss Updated!**\n\n"
        f"Stop Loss: `{pips} pips` beyond pattern",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.settings_menu()
    )
    
    bot_logger.info(f"User {user_id} updated stop loss: {pips} pips")


async def handle_target_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target settings"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "🎯 **Select Target Type**\n\n"
        "**Zone-based:** Targets set at VRZ zones\n"
        "**RR-based:** Targets based on Risk-Reward ratios",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.target_type_selection()
    )


async def handle_target_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle target type selection"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    target_type = data[2]  # 'zone' or 'rr'
    
    context.user_data['target_type'] = target_type
    
    if target_type == 'zone':
        await query.message.edit_text(
            "🎯 **Zone-based Targets**\n\n"
            "Select number of target zones:",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.zone_target_selection()
        )
    else:  # rr
        context.user_data['rr_levels'] = []
        await query.message.edit_text(
            "🎯 **RR-based Targets**\n\n"
            "Select Risk-Reward levels (you can select multiple):\n"
            "Tap each level you want, then click Done.",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.rr_target_selection()
        )


async def handle_rr_level_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle RR level selection"""
    query = update.callback_query
    
    data = query.data.split('_')
    
    if data[1] == 'done':
        # Finalize RR selection
        rr_levels = context.user_data.get('rr_levels', [1.5, 2.0, 2.5])
        user_id = update.effective_user.id
        
        await user_settings_repository.update_target_settings(
            user_id, 'rr', rr_levels
        )
        
        await query.answer("Targets updated!")
        await query.message.edit_text(
            f"✅ **Targets Updated!**\n\n"
            f"Type: RR-based\n"
            f"Levels: `{rr_levels}`",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.settings_menu()
        )
        
        bot_logger.info(f"User {user_id} updated RR targets: {rr_levels}")
    
    else:
        # Add/remove RR level
        rr_value = float(data[1])
        rr_levels = context.user_data.get('rr_levels', [])
        
        if rr_value in rr_levels:
            rr_levels.remove(rr_value)
            await query.answer(f"Removed 1:{rr_value}")
        else:
            rr_levels.append(rr_value)
            rr_levels.sort()
            await query.answer(f"Added 1:{rr_value}")
        
        context.user_data['rr_levels'] = rr_levels
        
        # Update message with selected levels
        await query.message.edit_text(
            f"🎯 **RR-based Targets**\n\n"
            f"Selected levels: `{rr_levels if rr_levels else 'None'}`\n\n"
            "Tap levels to add/remove, then click Done.",
            parse_mode='Markdown',
            reply_markup=bot_keyboards.rr_target_selection()
        )


async def handle_order_type_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order type settings"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "📝 **Select Order Type**\n\n"
        "**Market:** Execute immediately at current price\n"
        "**Limit:** Wait for specific price level",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.order_type_selection()
    )


async def handle_order_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order type selection"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    order_type = f"{data[2]}_order"
    
    user_id = update.effective_user.id
    await user_settings_repository.update_order_type(user_id, order_type)
    
    await query.message.edit_text(
        f"✅ **Order Type Updated!**\n\n"
        f"Type: `{order_type.replace('_', ' ').title()}`",
        parse_mode='Markdown',
        reply_markup=bot_keyboards.settings_menu()
    )
    
    bot_logger.info(f"User {user_id} updated order type: {order_type}")
                         
