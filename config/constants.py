"""
Trading constants and configuration values
"""

# Timeframe mappings for Delta Exchange
TIMEFRAME_MAPPINGS = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "1d": "1d",
    "1w": "1w",
    "1M": "1M"
}

# Timeframe multipliers (in minutes)
TIMEFRAME_MINUTES = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "6h": 360,
    "1d": 1440,
    "1w": 10080,
    "1M": 43200
}

# Candlestick pattern names
BULLISH_PATTERNS = [
    "bullish_engulfing",
    "piercing_line",
    "bullish_harami",
    "tweezer_bottom",
    "morning_star",
    "three_white_soldiers",
    "three_outside_up",
    "abandoned_baby_bullish",
    "hammer",
    "inverted_hammer",
    "bullish_marubozu"
]

BEARISH_PATTERNS = [
    "bearish_engulfing",
    "dark_cloud_cover",
    "bearish_harami",
    "tweezer_top",
    "evening_star",
    "three_black_crows",
    "three_outside_down",
    "abandoned_baby_bearish",
    "hanging_man",
    "shooting_star",
    "bearish_marubozu"
]

# Order types
ORDER_TYPE_MARKET = "market_order"
ORDER_TYPE_LIMIT = "limit_order"

# Position sides
SIDE_BUY = "buy"
SIDE_SELL = "sell"

# VRZ Zone types
ZONE_TYPE_RESISTANCE = "resistance"
ZONE_TYPE_SUPPORT = "support"

# VRZ Status
ZONE_STATUS_ACTIVE = "active"
ZONE_STATUS_INVALIDATED = "invalidated"

# Target types
TARGET_TYPE_ZONE = "zone"
TARGET_TYPE_RR = "rr"

# Trade status
TRADE_STATUS_OPEN = "open"
TRADE_STATUS_CLOSED = "closed"
TRADE_STATUS_PENDING = "pending"

# API Rate limits
DELTA_API_RATE_LIMIT = 10000  # requests per 5 minutes
DELTA_API_RATE_WINDOW = 300  # seconds

# Partial exit percentages
PARTIAL_EXIT_PERCENTAGES = {
    2: [50, 50],  # T1: 50%, T2: 50%
    3: [33, 33, 34],  # T1: 33%, T2: 33%, T3: 34%
    4: [25, 25, 25, 25]  # T1-T4: 25% each
}
