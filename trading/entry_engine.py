"""
Entry Engine - Scans for entry signals and generates trade setups
"""
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
from config.settings import settings
from config.constants import SIDE_BUY, SIDE_SELL, ZONE_TYPE_RESISTANCE, ZONE_TYPE_SUPPORT
from strategies.pattern_detector import PatternDetector
from strategies.vrz_calculator import VRZCalculator
from strategies.risk_manager import risk_manager
from api.delta_client import delta_client
from utils.logger import bot_logger


class EntryEngine:
    """
    Entry signal generation engine
    Monitors trading timeframe for entry patterns near VRZ zones
    """
    
    def __init__(self, user_settings: Dict):
        """
        Initialize Entry Engine
        
        Args:
            user_settings: User configuration dictionary
        """
        self.user_settings = user_settings
        self.pattern_detector = PatternDetector()
        self.vrz_calculator = VRZCalculator(
            base_timeframe=user_settings.get('base_timeframe', 'auto'),
            trading_timeframe=user_settings.get('trading_timeframe', '15m'),
            swing_left_bars=user_settings.get('swing_left_bars', 3),
            swing_right_bars=user_settings.get('swing_right_bars', 3)
        )
        
        bot_logger.info(
            f"Entry Engine initialized for user {user_settings.get('telegram_user_id')}"
        )
    
    async def scan_for_entry_signals(self, symbol: str, product_id: int) -> Optional[Dict]:
        """
        Scan for entry signals on trading timeframe
        
        Args:
            symbol: Trading symbol
            product_id: Delta Exchange product ID
        
        Returns:
            Entry signal dictionary or None
        """
        try:
            bot_logger.info(f"Scanning for entry signals: {symbol}")
            
            # 1. Fetch trading timeframe candles
            candles = await self.vrz_calculator.fetch_candles(
                symbol, 
                self.vrz_calculator.trading_timeframe, 
                bars=50
            )
            
            if len(candles) < 10:
                bot_logger.warning(f"Insufficient candles for {symbol}")
                return None
            
            # 2. Get current price
            current_price = candles[-1]['close']
            
            # 3. Get active VRZ zones near current price
            vrz_zones = await self.vrz_calculator.get_active_zones(
                symbol, 
                current_price, 
                max_zones=self.user_settings.get('max_vrz_zones', 3)
            )
            
            resistance_zones = vrz_zones['resistance_zones']
            support_zones = vrz_zones['support_zones']
            
            bot_logger.debug(
                f"Active zones for {symbol}: {len(resistance_zones)} resistance, "
                f"{len(support_zones)} support"
            )
            
            # 4. Check if price is near any zone
            near_resistance = self._find_nearby_zone(current_price, resistance_zones)
            near_support = self._find_nearby_zone(current_price, support_zones)
            
            if not near_resistance and not near_support:
                bot_logger.debug(f"Price not near any VRZ zone for {symbol}")
                return None
            
            # 5. Detect candlestick patterns at current candle
            patterns = self.pattern_detector.scan_all_patterns(candles, len(candles) - 1)
            
            if not patterns:
                bot_logger.debug(f"No patterns detected for {symbol}")
                return None
            
            # 6. Find best pattern
            best_pattern = max(patterns, key=lambda p: p['confidence'])
            
            bot_logger.log_pattern_detection(
                best_pattern['pattern_name'],
                symbol,
                self.vrz_calculator.trading_timeframe,
                best_pattern['confidence']
            )
            
            # 7. Validate pattern direction with zone
            entry_signal = None
            
            if best_pattern['direction'] == 'bullish' and near_support:
                # Bullish pattern near support - potential long entry
                entry_signal = await self._create_long_signal(
                    symbol, product_id, current_price, best_pattern, 
                    near_support, support_zones, resistance_zones
                )
            
            elif best_pattern['direction'] == 'bearish' and near_resistance:
                # Bearish pattern near resistance - potential short entry
                entry_signal = await self._create_short_signal(
                    symbol, product_id, current_price, best_pattern, 
                    near_resistance, resistance_zones, support_zones
                )
            
            if entry_signal:
                bot_logger.log_entry_signal(entry_signal)
            
            return entry_signal
            
        except Exception as e:
            bot_logger.error(f"Error scanning for entry signals: {str(e)}", exc_info=True)
            return None
    
    def _find_nearby_zone(self, price: float, zones: List[Dict]) -> Optional[Dict]:
        """
        Find if price is near any zone
        
        Args:
            price: Current price
            zones: List of VRZ zones
        
        Returns:
            Nearby zone or None
        """
        for zone in zones:
            if self.vrz_calculator.is_price_near_zone(price, zone, proximity_percent=0.5):
                return zone
        return None
    
    async def _create_long_signal(self, 
                                  symbol: str, 
                                  product_id: int,
                                  current_price: float, 
                                  pattern: Dict, 
                                  entry_zone: Dict,
                                  support_zones: List[Dict],
                                  resistance_zones: List[Dict]) -> Optional[Dict]:
        """
        Create long entry signal
        
        Args:
            symbol: Trading symbol
            product_id: Product ID
            current_price: Current market price
            pattern: Detected pattern
            entry_zone: VRZ support zone for entry
            support_zones: List of support zones
            resistance_zones: List of resistance zones (for targets)
        
        Returns:
            Long entry signal or None
        """
        try:
            # Calculate stop loss
            stop_loss = risk_manager.calculate_stop_loss(
                entry_price=current_price,
                side=SIDE_BUY,
                pattern_high=pattern['pattern_high'],
                pattern_low=pattern['pattern_low'],
                stop_pips=self.user_settings.get('stop_loss_pips', 10)
            )
            
            # Get entry timeframe VRZ zones for targets
            entry_tf_zones = await self.vrz_calculator.calculate_entry_timeframe_vrz(
                symbol, product_id
            )
            
            target_type = self.user_settings.get('target_type', 'rr')
            
            # Calculate targets
            if target_type == 'zone':
                # Use resistance zones as targets
                target_zones = resistance_zones[:self.user_settings.get('max_vrz_zones', 3)]
                targets = risk_manager.calculate_multiple_targets(
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    side=SIDE_BUY,
                    target_type='zone',
                    vrz_zones=target_zones
                )
            else:  # RR-based
                target_levels = self.user_settings.get('target_levels', [1.5, 2.0, 2.5])
                targets = risk_manager.calculate_multiple_targets(
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    side=SIDE_BUY,
                    target_type='rr',
                    target_levels=target_levels
                )
            
            if not targets:
                bot_logger.warning("No valid targets calculated")
                return None
            
            # Validate trade setup (check minimum RR)
            first_target = targets[0]['price']
            is_valid, reason, rr_ratio = risk_manager.validate_trade_setup(
                entry_price=current_price,
                stop_loss=stop_loss,
                target_price=first_target,
                side=SIDE_BUY
            )
            
            if not is_valid:
                bot_logger.info(f"Trade setup invalid: {reason}")
                return None
            
            # Create entry signal
            signal = {
                'symbol': symbol,
                'product_id': product_id,
                'side': SIDE_BUY,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'targets': targets,
                'risk_reward': rr_ratio,
                'pattern': pattern['pattern_name'],
                'pattern_confidence': pattern['confidence'],
                'entry_zone': entry_zone,
                'timeframe': self.vrz_calculator.trading_timeframe,
                'timestamp': datetime.utcnow(),
                'lot_size': self.user_settings.get('lot_size', 1),
                'order_type': self.user_settings.get('order_type', 'market_order')
            }
            
            # Log risk summary
            risk_summary = risk_manager.format_risk_summary(
                entry_price=current_price,
                stop_loss=stop_loss,
                targets=targets,
                side=SIDE_BUY,
                position_size=signal['lot_size']
            )
            bot_logger.info(risk_summary)
            
            return signal
            
        except Exception as e:
            bot_logger.error(f"Error creating long signal: {str(e)}", exc_info=True)
            return None
    
    async def _create_short_signal(self, 
                                   symbol: str, 
                                   product_id: int,
                                   current_price: float, 
                                   pattern: Dict, 
                                   entry_zone: Dict,
                                   resistance_zones: List[Dict],
                                   support_zones: List[Dict]) -> Optional[Dict]:
        """
        Create short entry signal
        
        Args:
            symbol: Trading symbol
            product_id: Product ID
            current_price: Current market price
            pattern: Detected pattern
            entry_zone: VRZ resistance zone for entry
            resistance_zones: List of resistance zones
            support_zones: List of support zones (for targets)
        
        Returns:
            Short entry signal or None
        """
        try:
            # Calculate stop loss
            stop_loss = risk_manager.calculate_stop_loss(
                entry_price=current_price,
                side=SIDE_SELL,
                pattern_high=pattern['pattern_high'],
                pattern_low=pattern['pattern_low'],
                stop_pips=self.user_settings.get('stop_loss_pips', 10)
            )
            
            # Get entry timeframe VRZ zones for targets
            entry_tf_zones = await self.vrz_calculator.calculate_entry_timeframe_vrz(
                symbol, product_id
            )
            
            target_type = self.user_settings.get('target_type', 'rr')
            
            # Calculate targets
            if target_type == 'zone':
                # Use support zones as targets
                target_zones = support_zones[:self.user_settings.get('max_vrz_zones', 3)]
                targets = risk_manager.calculate_multiple_targets(
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    side=SIDE_SELL,
                    target_type='zone',
                    vrz_zones=target_zones
                )
            else:  # RR-based
                target_levels = self.user_settings.get('target_levels', [1.5, 2.0, 2.5])
                targets = risk_manager.calculate_multiple_targets(
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    side=SIDE_SELL,
                    target_type='rr',
                    target_levels=target_levels
                )
            
            if not targets:
                bot_logger.warning("No valid targets calculated")
                return None
            
            # Validate trade setup
            first_target = targets[0]['price']
            is_valid, reason, rr_ratio = risk_manager.validate_trade_setup(
                entry_price=current_price,
                stop_loss=stop_loss,
                target_price=first_target,
                side=SIDE_SELL
            )
            
            if not is_valid:
                bot_logger.info(f"Trade setup invalid: {reason}")
                return None
            
            # Create entry signal
            signal = {
                'symbol': symbol,
                'product_id': product_id,
                'side': SIDE_SELL,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'targets': targets,
                'risk_reward': rr_ratio,
                'pattern': pattern['pattern_name'],
                'pattern_confidence': pattern['confidence'],
                'entry_zone': entry_zone,
                'timeframe': self.vrz_calculator.trading_timeframe,
                'timestamp': datetime.utcnow(),
                'lot_size': self.user_settings.get('lot_size', 1),
                'order_type': self.user_settings.get('order_type', 'market_order')
            }
            
            # Log risk summary
            risk_summary = risk_manager.format_risk_summary(
                entry_price=current_price,
                stop_loss=stop_loss,
                targets=targets,
                side=SIDE_SELL,
                position_size=signal['lot_size']
            )
            bot_logger.info(risk_summary)
            
            return signal
            
        except Exception as e:
            bot_logger.error(f"Error creating short signal: {str(e)}", exc_info=True)
            return None
    
    async def execute_entry(self, signal: Dict) -> Optional[Dict]:
        """
        Execute entry order based on signal
        
        Args:
            signal: Entry signal dictionary
        
        Returns:
            Order response or None
        """
        try:
            bot_logger.info(f"Executing entry: {signal['symbol']} {signal['side']}")
            
            # Prepare stop loss order
            stop_loss_order = {
                'order_type': 'stop_market_order',
                'stop_price': str(signal['stop_loss']),
                'trail_amount': '0'
            }
            
            # Place order
            order_response = await delta_client.place_order(
                product_id=signal['product_id'],
                size=signal['lot_size'],
                side=signal['side'],
                order_type=signal['order_type'],
                limit_price=signal['entry_price'] if signal['order_type'] == 'limit_order' else None,
                stop_loss_order=stop_loss_order
            )
            
            if order_response.get('success'):
                bot_logger.info(f"Entry order placed successfully: {signal['symbol']}")
                return order_response
            else:
                bot_logger.error(f"Entry order failed: {order_response}")
                return None
            
        except Exception as e:
            bot_logger.error(f"Error executing entry: {str(e)}", exc_info=True)
            return None
          
