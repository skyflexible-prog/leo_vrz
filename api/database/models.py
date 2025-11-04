"""
MongoDB data models using Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class VRZZone(BaseModel):
    """VRZ Support/Resistance Zone Model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    symbol: str
    product_id: int
    type: str  # 'resistance' or 'support'
    price_level: float
    zone_upper: float
    zone_lower: float
    bar_index: int
    timestamp: datetime
    timeframe: str
    status: str = "active"  # 'active' or 'invalidated'
    breach_details: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserSettings(BaseModel):
    """User Configuration Model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    telegram_user_id: int
    selected_assets: List[str] = []
    asset_selection_mode: str = "individual"  # 'top_gainers', 'top_losers', 'both', 'all', 'individual'
    base_timeframe: str = "1h"
    trading_timeframe: str = "15m"
    lot_size: int = 1
    stop_loss_pips: int = 10
    target_type: str = "rr"  # 'zone' or 'rr'
    target_levels: List[float] = [1.5, 2.0, 2.5]
    order_type: str = "market_order"
    max_vrz_zones: int = 3
    swing_left_bars: int = 3
    swing_right_bars: int = 3
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Trade(BaseModel):
    """Trade Execution Model"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    telegram_user_id: int
    symbol: str
    product_id: int
    order_id: Optional[str] = None
    entry_price: float
    stop_loss: float
    targets: List[Dict]  # [{'level': 1.5, 'price': 100, 'percentage': 33}]
    position_size: int
    remaining_size: int
    side: str  # 'buy' or 'sell'
    entry_pattern: str
    entry_vrz_zone: Dict
    entry_time: datetime
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    status: str = "open"  # 'open', 'closed', 'pending'
    exit_details: List[Dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
  
