"""
Status and monitoring handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.repositories.user_settings_repository import user_settings_repository
from database.repositories.vrz_repository import vrz_repository
from trading.position_manager import position_manager
from api.delta_client import delta_client
from utils.logger import bot_logger
from utils.timezone_helper import TimezoneHelper


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show VRZ zones and bot status"""
    try:
        user_id = update.effective_user.id
        user_settings = await user_settings_repository.get_user_settings(user_id)
        
        # Get bot status
        is_active = user_settings.get('is_active', False)
        status_emoji = "🟢" if is_active else "🔴"
        status_text = "Active" if is_active else "Inactive"
        
        # Get open positions count
        open_positions = await position_manager.get_open_positions(user_id)
        
        # Get selected assets
        asset_mode = user_settings.get('asset_selection_mode', 'individual')
        selected_assets = user_settings.get('selected_assets', [])
        
        status_message = f"""
📊 **Bot Status Dashboard**

**Status:** {status_emoji} {status_text}
**Open Positions:** {len(open_positions)}
**Asset Mode:** {asset_mode.replace('_', ' ').title()}
**Assets:** {len(selected_assets) if asset_mode == 'individual' else 'Auto'}

**Configuration:**
⏰ Base TF: `{user_settings.get('base_timeframe', 'auto')}`
⏰ Trading TF: `{user_settings.get('trading_timeframe', '15m')}`
📦 Lot Size: `{user_settings.get('lot_size', 1)}`
🛑 Stop Loss: `{user_settings.get('stop_loss_pips', 10)} pips`
🎯 Target Type: `{user_settings.get('target_type', 'rr').upper()}`

**Active VRZ Zones:**
"""
        
        # Show VRZ zones for first selected asset
        if selected_assets:
            symbol = selected_assets[0]
            
            # Get active zones
            resistance_zones = await vrz_repository.get_active_zones(
                symbol, 
                user_settings.get('base_timeframe', '1h'),
                zone_type='resistance'
            )
            
            support_zones = await vrz_repository.get_active_zones(
                symbol, 
                user_settings.get('base_timeframe', '1h'),
                zone_type='support'
            )
            
            status_message += f"\n📍 {symbol}:\n"
            
            if resistance_zones:
                status_message += "\n🔴 Resistance:\n"
                for i, zone in enumerate(resistance_zones[:3], 1):
                    status_message += f"  R{i}: `{zone['price_level']:.2f}` ({zone['zone_lower']:.2f}-{zone['zone_upper']:.2f})\n"
            
            if support_zones:
                status_message += "\n🟢 Support:\n"
                for i, zone in enumerate(support_zones[:3], 1):
                    status_message += f"  S{i}: `{zone['price_level']:.2f}` ({zone['zone_lower']:.2f}-{zone['zone_upper']:.2f})\n"
        
        status_message += f"\n\n🕐 Updated: {TimezoneHelper.format_ist(TimezoneHelper.now_utc())}"
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        
    except Exception as e:
        bot_logger.error(f"Error in status command: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error fetching status. Please try again.")


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /positions command"""
    try:
        user_id = update.effective_user.id
        
        # Get position summary
        summary = await position_manager.get_position_summary(user_id)
        
        open_positions = summary.get('open_positions', [])
        total_pnl = summary.get('total_pnl', 0)
        win_rate = summary.get('win_rate', 0)
        
        message = f"""
📈 **Positions Summary**

**Open Positions:** {len(open_positions)}
**Total PnL:** `{total_pnl:+.2f}`
**Win Rate:** `{win_rate:.1f}%`

"""
        
        if open_positions:
            message += "**Open Positions:**\n\n"
            
            for pos in open_positions:
                side_emoji = "🟢" if pos['side'] == 'buy' else "🔴"
                
                # Calculate current PnL estimate
                current_pnl = pos.get('pnl', 0)
                
                message += f"{side_emoji} **{pos['symbol']}**\n"
                message += f"  Entry: `{pos['entry_price']:.2f}`\n"
                message += f"  Size: `{pos['remaining_size']}`\n"
                message += f"  SL: `{pos['stop_loss']:.2f}`\n"
                message += f"  PnL: `{current_pnl:+.2f}`\n"
                message += f"  Pattern: `{pos['entry_pattern']}`\n\n"
        else:
            message += "No open positions.\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        bot_logger.error(f"Error in positions command: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error fetching positions. Please try again.")
      
