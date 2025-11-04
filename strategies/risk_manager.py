"""
Risk Management and Risk-Reward Ratio Calculator
"""
from typing import Dict, List, Optional, Tuple
from config.settings import settings
from config.constants import SIDE_BUY, SIDE_SELL
from utils.logger import bot_logger


class RiskManager:
    """
    Risk management and RR ratio calculation for trade signals
    """
    
    def __init__(self, min_risk_reward: float = None):
        """
        Initialize Risk Manager
        
        Args:
            min_risk_reward: Minimum acceptable risk-reward ratio
        """
        self.min_risk_reward = min_risk_reward or settings.MIN_RISK_REWARD_RATIO
        bot_logger.info(f"Risk Manager initialized - Min RR: 1:{self.min_risk_reward}")
    
    def calculate_stop_loss(self, 
                           entry_price: float, 
                           side: str, 
                           pattern_high: float, 
                           pattern_low: float, 
                           stop_pips: int) -> float:
        """
        Calculate stop loss price based on pattern and pips
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            pattern_high: Highest point of entry pattern
            pattern_low: Lowest point of entry pattern
            stop_pips: Number of pips beyond pattern
        
        Returns:
            Stop loss price
        """
        # Calculate pip value (assuming price scale)
        pip_value = entry_price * 0.0001 * stop_pips
        
        if side == SIDE_BUY:
            # For long entries, SL below pattern low
            stop_loss = pattern_low - pip_value
        else:  # SIDE_SELL
            # For short entries, SL above pattern high
            stop_loss = pattern_high + pip_value
        
        bot_logger.debug(
            f"Calculated SL: {stop_loss:.2f} for {side} entry at {entry_price:.2f} "
            f"({stop_pips} pips beyond pattern)"
        )
        
        return stop_loss
    
    def calculate_risk(self, entry_price: float, stop_loss: float) -> float:
        """
        Calculate risk amount per unit
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
        
        Returns:
            Risk amount
        """
        return abs(entry_price - stop_loss)
    
    def calculate_target_by_rr(self, 
                               entry_price: float, 
                               stop_loss: float, 
                               side: str, 
                               rr_ratio: float) -> float:
        """
        Calculate target price based on risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'buy' or 'sell'
            rr_ratio: Risk-reward ratio (e.g., 1.5 for 1:1.5)
        
        Returns:
            Target price
        """
        risk = self.calculate_risk(entry_price, stop_loss)
        reward = risk * rr_ratio
        
        if side == SIDE_BUY:
            target = entry_price + reward
        else:  # SIDE_SELL
            target = entry_price - reward
        
        return target
    
    def calculate_rr_ratio(self, 
                          entry_price: float, 
                          stop_loss: float, 
                          target_price: float) -> float:
        """
        Calculate risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            target_price: Target price
        
        Returns:
            Risk-reward ratio
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        
        if risk == 0:
            return 0.0
        
        return reward / risk
    
    def calculate_target_by_zone(self, 
                                entry_price: float, 
                                side: str, 
                                vrz_zone: Dict) -> float:
        """
        Calculate target based on VRZ zone
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            vrz_zone: VRZ zone dictionary
        
        Returns:
            Target price (zone boundary)
        """
        if side == SIDE_BUY:
            # For long, target is resistance zone lower bound
            target = vrz_zone['zone_lower']
        else:  # SIDE_SELL
            # For short, target is support zone upper bound
            target = vrz_zone['zone_upper']
        
        return target
    
    def calculate_multiple_targets(self, 
                                   entry_price: float, 
                                   stop_loss: float, 
                                   side: str, 
                                   target_type: str,
                                   target_levels: List[float] = None,
                                   vrz_zones: List[Dict] = None) -> List[Dict]:
        """
        Calculate multiple target levels
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            side: 'buy' or 'sell'
            target_type: 'rr' or 'zone'
            target_levels: List of RR ratios (for 'rr' type)
            vrz_zones: List of VRZ zones (for 'zone' type)
        
        Returns:
            List of target dictionaries with prices and percentages
        """
        targets = []
        
        if target_type == 'rr' and target_levels:
            # RR-based targets
            from config.constants import PARTIAL_EXIT_PERCENTAGES
            
            num_targets = len(target_levels)
            exit_percentages = PARTIAL_EXIT_PERCENTAGES.get(num_targets, [100])
            
            for i, rr_level in enumerate(target_levels):
                target_price = self.calculate_target_by_rr(
                    entry_price, stop_loss, side, rr_level
                )
                
                targets.append({
                    'level': i + 1,
                    'type': 'rr',
                    'rr_ratio': rr_level,
                    'price': target_price,
                    'exit_percentage': exit_percentages[i] if i < len(exit_percentages) else 100
                })
        
        elif target_type == 'zone' and vrz_zones:
            # Zone-based targets
            from config.constants import PARTIAL_EXIT_PERCENTAGES
            
            num_targets = len(vrz_zones)
            exit_percentages = PARTIAL_EXIT_PERCENTAGES.get(num_targets, [100])
            
            for i, zone in enumerate(vrz_zones):
                target_price = self.calculate_target_by_zone(entry_price, side, zone)
                
                # Calculate RR for this zone
                rr_ratio = self.calculate_rr_ratio(entry_price, stop_loss, target_price)
                
                targets.append({
                    'level': i + 1,
                    'type': 'zone',
                    'zone_price': zone['price_level'],
                    'price': target_price,
                    'rr_ratio': rr_ratio,
                    'exit_percentage': exit_percentages[i] if i < len(exit_percentages) else 100
                })
        
        return targets
    
    def validate_trade_setup(self, 
                            entry_price: float, 
                            stop_loss: float, 
                            target_price: float,
                            side: str) -> Tuple[bool, str, float]:
        """
        Validate if trade setup meets minimum RR requirements
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            target_price: Target price
            side: 'buy' or 'sell'
        
        Returns:
            Tuple of (is_valid, reason, rr_ratio)
        """
        # Calculate RR ratio
        rr_ratio = self.calculate_rr_ratio(entry_price, stop_loss, target_price)
        
        # Check if RR meets minimum
        if rr_ratio < self.min_risk_reward:
            return (
                False, 
                f"RR {rr_ratio:.2f} below minimum {self.min_risk_reward}", 
                rr_ratio
            )
        
        # Validate stop loss placement
        if side == SIDE_BUY:
            if stop_loss >= entry_price:
                return (False, "Stop loss must be below entry for long positions", rr_ratio)
            if target_price <= entry_price:
                return (False, "Target must be above entry for long positions", rr_ratio)
        else:  # SIDE_SELL
            if stop_loss <= entry_price:
                return (False, "Stop loss must be above entry for short positions", rr_ratio)
            if target_price >= entry_price:
                return (False, "Target must be below entry for short positions", rr_ratio)
        
        return (True, "Trade setup valid", rr_ratio)
    
    def calculate_position_size(self, 
                               account_balance: float, 
                               risk_percentage: float, 
                               entry_price: float, 
                               stop_loss: float,
                               contract_size: float = 1.0) -> int:
        """
        Calculate position size based on risk percentage
        
        Args:
            account_balance: Account balance
            risk_percentage: Percentage of account to risk per trade
            entry_price: Entry price
            stop_loss: Stop loss price
            contract_size: Size of one contract
        
        Returns:
            Number of contracts to trade
        """
        # Calculate risk amount
        risk_per_unit = abs(entry_price - stop_loss)
        
        # Calculate max risk in currency
        max_risk_amount = account_balance * (risk_percentage / 100)
        
        # Calculate position size
        position_size = int(max_risk_amount / (risk_per_unit * contract_size))
        
        # Ensure at least 1 contract
        position_size = max(1, position_size)
        
        bot_logger.debug(
            f"Position Size Calculation: Balance={account_balance}, "
            f"Risk%={risk_percentage}, Risk/Unit={risk_per_unit:.2f}, "
            f"Size={position_size} contracts"
        )
        
        return position_size
    
    def calculate_partial_exits(self, 
                               position_size: int, 
                               num_targets: int) -> List[int]:
        """
        Calculate partial exit quantities for each target
        
        Args:
            position_size: Total position size
            num_targets: Number of targets
        
        Returns:
            List of quantities to exit at each target
        """
        from config.constants import PARTIAL_EXIT_PERCENTAGES
        
        percentages = PARTIAL_EXIT_PERCENTAGES.get(num_targets, [100])
        exit_quantities = []
        remaining_size = position_size
        
        for i, percentage in enumerate(percentages):
            if i == len(percentages) - 1:
                # Last target gets all remaining
                exit_quantities.append(remaining_size)
            else:
                # Calculate quantity for this target
                qty = int(position_size * (percentage / 100))
                qty = max(1, qty)  # At least 1 contract
                exit_quantities.append(qty)
                remaining_size -= qty
        
        return exit_quantities
    
    def get_nearest_opposite_zone(self, 
                                 entry_price: float, 
                                 side: str, 
                                 vrz_zones: List[Dict]) -> Optional[Dict]:
        """
        Get nearest opposite VRZ zone for target calculation
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            vrz_zones: List of VRZ zones
        
        Returns:
            Nearest opposite zone or None
        """
        if side == SIDE_BUY:
            # For long, find nearest resistance above entry
            valid_zones = [z for z in vrz_zones if z['zone_lower'] > entry_price]
        else:  # SIDE_SELL
            # For short, find nearest support below entry
            valid_zones = [z for z in vrz_zones if z['zone_upper'] < entry_price]
        
        if not valid_zones:
            return None
        
        # Sort by distance and return nearest
        valid_zones.sort(key=lambda z: abs(z['price_level'] - entry_price))
        return valid_zones[0]
    
    def format_risk_summary(self, 
                           entry_price: float, 
                           stop_loss: float, 
                           targets: List[Dict],
                           side: str,
                           position_size: int) -> str:
        """
        Format risk summary for logging/display
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            targets: List of target dictionaries
            side: 'buy' or 'sell'
            position_size: Position size
        
        Returns:
            Formatted risk summary string
        """
        risk = self.calculate_risk(entry_price, stop_loss)
        risk_percentage = (risk / entry_price) * 100
        
        summary = f"\n{'='*50}\n"
        summary += f"RISK MANAGEMENT SUMMARY\n"
        summary += f"{'='*50}\n"
        summary += f"Side: {side.upper()}\n"
        summary += f"Entry Price: {entry_price:.2f}\n"
        summary += f"Stop Loss: {stop_loss:.2f}\n"
        summary += f"Risk per Unit: {risk:.2f} ({risk_percentage:.2f}%)\n"
        summary += f"Position Size: {position_size} contracts\n"
        summary += f"\nTargets:\n"
        
        for target in targets:
            summary += f"  T{target['level']}: {target['price']:.2f} "
            summary += f"(RR: 1:{target['rr_ratio']:.2f}, "
            summary += f"Exit: {target['exit_percentage']}%)\n"
        
        summary += f"{'='*50}\n"
        
        return summary


# Global risk manager instance
risk_manager = RiskManager()
                                     
