"""
Telegram keyboard layouts and inline buttons
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List


class BotKeyboards:
    """Telegram keyboard layouts for bot interaction"""
    
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard"""
        keyboard = [
            [KeyboardButton("⚙️ Settings"), KeyboardButton("📊 Status")],
            [KeyboardButton("🎯 Select Asset"), KeyboardButton("📈 Positions")],
            [KeyboardButton("📋 Trade History"), KeyboardButton("🔄 Sync")],
            [KeyboardButton("▶️ Start Bot"), KeyboardButton("⏸ Stop Bot")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def asset_selection_menu() -> InlineKeyboardMarkup:
        """Asset selection mode keyboard"""
        keyboard = [
            [InlineKeyboardButton("📈 Top Gainers", callback_data="asset_top_gainers")],
            [InlineKeyboardButton("📉 Top Losers", callback_data="asset_top_losers")],
            [InlineKeyboardButton("🔄 Both Gainers & Losers", callback_data="asset_both")],
            [InlineKeyboardButton("🌐 All Futures", callback_data="asset_all")],
            [InlineKeyboardButton("✍️ Individual Asset", callback_data="asset_individual")],
            [InlineKeyboardButton("« Back", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Settings configuration keyboard"""
        keyboard = [
            [InlineKeyboardButton("⏰ Timeframes", callback_data="settings_timeframes")],
            [InlineKeyboardButton("📦 Lot Size", callback_data="settings_lot_size")],
            [InlineKeyboardButton("🛑 Stop Loss", callback_data="settings_stop_loss")],
            [InlineKeyboardButton("🎯 Targets", callback_data="settings_targets")],
            [InlineKeyboardButton("📝 Order Type", callback_data="settings_order_type")],
            [InlineKeyboardButton("🔧 Advanced", callback_data="settings_advanced")],
            [InlineKeyboardButton("« Back", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def timeframe_selection(timeframe_type: str) -> InlineKeyboardMarkup:
        """Timeframe selection keyboard"""
        timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]
        
        keyboard = []
        row = []
        for i, tf in enumerate(timeframes):
            row.append(InlineKeyboardButton(tf, callback_data=f"tf_{timeframe_type}_{tf}"))
            if (i + 1) % 4 == 0:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        if timeframe_type == "base":
            keyboard.append([InlineKeyboardButton("🔄 Auto (4x Trading TF)", callback_data="tf_base_auto")])
        
        keyboard.append([InlineKeyboardButton("« Back", callback_data="back_settings")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def lot_size_selection() -> InlineKeyboardMarkup:
        """Lot size selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("1", callback_data="lot_1"),
             InlineKeyboardButton("2", callback_data="lot_2"),
             InlineKeyboardButton("5", callback_data="lot_5")],
            [InlineKeyboardButton("10", callback_data="lot_10"),
             InlineKeyboardButton("20", callback_data="lot_20"),
             InlineKeyboardButton("50", callback_data="lot_50")],
            [InlineKeyboardButton("✍️ Custom", callback_data="lot_custom")],
            [InlineKeyboardButton("« Back", callback_data="back_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def stop_loss_pips_selection() -> InlineKeyboardMarkup:
        """Stop loss pips selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("5 pips", callback_data="sl_pips_5"),
             InlineKeyboardButton("10 pips", callback_data="sl_pips_10")],
            [InlineKeyboardButton("15 pips", callback_data="sl_pips_15"),
             InlineKeyboardButton("20 pips", callback_data="sl_pips_20")],
            [InlineKeyboardButton("« Back", callback_data="back_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def target_type_selection() -> InlineKeyboardMarkup:
        """Target type selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("📍 Zone-based Targets", callback_data="target_type_zone")],
            [InlineKeyboardButton("📊 RR-based Targets", callback_data="target_type_rr")],
            [InlineKeyboardButton("« Back", callback_data="back_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def rr_target_selection() -> InlineKeyboardMarkup:
        """RR target levels selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("1:1.5", callback_data="rr_1.5"),
             InlineKeyboardButton("1:2", callback_data="rr_2")],
            [InlineKeyboardButton("1:2.5", callback_data="rr_2.5"),
             InlineKeyboardButton("1:3", callback_data="rr_3")],
            [InlineKeyboardButton("1:3.5", callback_data="rr_3.5"),
             InlineKeyboardButton("1:4", callback_data="rr_4")],
            [InlineKeyboardButton("✅ Done", callback_data="rr_done")],
            [InlineKeyboardButton("« Back", callback_data="back_targets")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def zone_target_selection() -> InlineKeyboardMarkup:
        """Zone target count selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("T1 (1 Zone)", callback_data="zone_count_1")],
            [InlineKeyboardButton("T1, T2 (2 Zones)", callback_data="zone_count_2")],
            [InlineKeyboardButton("T1, T2, T3 (3 Zones)", callback_data="zone_count_3")],
            [InlineKeyboardButton("« Back", callback_data="back_targets")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def order_type_selection() -> InlineKeyboardMarkup:
        """Order type selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("🚀 Market Order", callback_data="order_type_market")],
            [InlineKeyboardButton("📝 Limit Order", callback_data="order_type_limit")],
            [InlineKeyboardButton("« Back", callback_data="back_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def position_actions(position_id: str) -> InlineKeyboardMarkup:
        """Position management actions keyboard"""
        keyboard = [
            [InlineKeyboardButton("❌ Close Position", callback_data=f"close_pos_{position_id}")],
            [InlineKeyboardButton("📊 View Details", callback_data=f"view_pos_{position_id}")],
            [InlineKeyboardButton("« Back", callback_data="back_positions")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_action(action: str, data: str) -> InlineKeyboardMarkup:
        """Confirmation keyboard for actions"""
        keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{data}"),
             InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
        """Generic pagination keyboard"""
        keyboard = []
        
        if total_pages > 1:
            buttons = []
            if current_page > 1:
                buttons.append(InlineKeyboardButton("« Prev", callback_data=f"{callback_prefix}_page_{current_page-1}"))
            
            buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="page_info"))
            
            if current_page < total_pages:
                buttons.append(InlineKeyboardButton("Next »", callback_data=f"{callback_prefix}_page_{current_page+1}"))
            
            keyboard.append(buttons)
        
        keyboard.append([InlineKeyboardButton("« Back", callback_data="back_main")])
        return InlineKeyboardMarkup(keyboard)


# Global keyboard instance
bot_keyboards = BotKeyboards()
        
