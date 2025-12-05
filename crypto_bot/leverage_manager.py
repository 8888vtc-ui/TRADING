"""LEVERAGE MANAGER - PAPER TRADING 5x MAX"""
import logging
from typing import Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LeverageLevel(Enum):
    NONE = 1.0
    LOW = 1.5
    MEDIUM = 2.0
    HIGH = 3.0
    EXTREME = 5.0

@dataclass
class LeverageDecision:
    can_leverage: bool
    multiplier: float
    level: LeverageLevel
    reasons: list
    adjusted_stop_loss: float
    adjusted_position_size: float
    risk_score: float

class LeverageManager:
    def __init__(self, market_checker=None):
        self.market_checker = market_checker
        self.max_leverage = 5.0
        self.thresholds = {'min_confidence': 75, 'min_score': 8}
        self.stop_multipliers = {LeverageLevel.NONE: 1.0, LeverageLevel.LOW: 0.75, LeverageLevel.MEDIUM: 0.60, LeverageLevel.HIGH: 0.45, LeverageLevel.EXTREME: 0.30}
        self.leveraged_positions = 0
        self.max_leveraged_positions = 3
        self.daily_leveraged_trades = 0
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        confidence = signal.get('confidence', 0)
        score = signal.get('score', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        reasons = []
        can_leverage = confidence >= 75 and score >= 8 and self.leveraged_positions < 3
        
        if confidence >= 95 and score >= 11:
            level, multiplier = LeverageLevel.EXTREME, 5.0
            reasons.append("🔥🔥🔥 LEVERAGE 5x!")
        elif confidence >= 90 and score >= 10:
            level, multiplier = LeverageLevel.HIGH, 3.0
            reasons.append("🔥🔥 LEVERAGE 3x!")
        elif confidence >= 85 and score >= 9:
            level, multiplier = LeverageLevel.MEDIUM, 2.0
        elif confidence >= 80 and score >= 8:
            level, multiplier = LeverageLevel.LOW, 1.5
        else:
            level, multiplier = LeverageLevel.NONE, 1.0
            can_leverage = False
        
        return LeverageDecision(can_leverage=can_leverage, multiplier=multiplier, level=level, reasons=reasons, adjusted_stop_loss=stop_loss_pct * self.stop_multipliers[level], adjusted_position_size=1.0, risk_score=50)
    
    def open_leveraged_position(self): self.leveraged_positions += 1
    def close_leveraged_position(self, pnl): self.leveraged_positions = max(0, self.leveraged_positions - 1)
    def reset_daily(self): self.daily_leveraged_trades = 0
    def get_status(self): return {'max_leverage': '5x', 'positions': self.leveraged_positions}
