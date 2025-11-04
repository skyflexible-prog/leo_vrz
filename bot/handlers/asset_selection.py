"""
Asset selection handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards import bot_keyboards  # ← Updated import
from database.repositories.user_settings_repository import user_settings_repository
from api.delta_client import delta_client
from utils.logger import bot_logger


async def asset_selection_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection"""
    try:
        text = """
🎯 **Asset Selection**

Choose how to select trading assets:

📈 **Top Gainers** - Top 10 assets with highest 24h gains
📉 **Top Losers** - Top 10 assets with highest 24h losses
🔄 **Both** - Trade both top gainers and losers
🌐 **All Futures** - Trade all available futures
✍️ **Individual** - Manually select specific assets
"""
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                text,
                parse_mode='Markdown',
                reply_markup=bot_keyboards.asset_selection_menu()
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=bot_keyboards.asset_selection_menu()
            )
        
    except Exception as e:
        bot_logger.error(f"Error in asset selection: {str(e)}", exc_info=True)


async def handle_asset_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle asset selection mode"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    mode = data[1] if len(data) > 1 else data[0]
    
    user_id = update.effective_user.id
    
    try:
        if mode == 'individual':
            context.user_data['awaiting'] = 'asset_symbols'
            await query.message.edit_text(
                "✍️ **Enter Asset Symbols**\n\n"
                "Send comma-separated symbols (e.g., BTCUSDT, ETHUSDT, BNBUSDT):",
                parse_mode='Markdown'
            )
            return
        
        # Update asset selection mode
        await user_settings_repository.update_asset_selection_mode(user_id, mode)
        
        # Fetch and display selected assets
        if mode in ['top_gainers', 'top_losers', 'both']:
            top_movers = await delta_client.get_top_movers(limit=10)
            
            if mode == 'top_gainers':
                assets = top_movers['top_gainers']
                title = "📈 Top Gainers"
            elif mode == 'top_losers':
                assets = top_movers['top_losers']
                title = "📉 Top Losers"
            else:  # both
                assets = top_movers['top_gainers'] + top_movers['top_losers']
                title = "🔄 Top Gainers & Losers"
            
            asset_list = "\n".join([
                f"{i+1}. {a['symbol']} ({a['change_24h']:+.2f}%)"
                for i, a in enumerate(assets[:20])
            ])
            
            message = f"✅ **{title} Selected**\n\n{asset_list}"
        
        elif mode == 'all':
            products = await delta_client.get_products()
            futures = [p for p in products if p.get('product_type') == 'future']
            
            message = f"✅ **All Futures Selected**\n\n{len(futures)} assets selected"
        
        await query.message.edit_text(
            message,
            parse_mode='Markdown',
            reply_markup=bot_keyboards.asset_selection_menu()
        )
        
        bot_logger.info(f"User {user_id} selected asset mode: {mode}")
        
    except Exception as e:
        bot_logger.error(f"Error handling asset mode: {str(e)}", exc_info=True)
        await query.message.edit_text(
            "❌ Error selecting assets. Please try again.",
            reply_markup=bot_keyboards.asset_selection_menu()
        )
      
