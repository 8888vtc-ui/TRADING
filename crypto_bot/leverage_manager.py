"""
🚀 LEVERAGE MANAGER V2.0 - MODE PAPER TRADING AGRESSIF
=====================================================
LEVERAGE MAX: 5x (pour tester en paper trading)
"""

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
        self.thresholds = {
            'min_confidence': 75,
            'low_confidence': 80,
            'medium_confidence': 85,
            'high_confidence': 90,
            'extreme_confidence': 95,
            'min_score': 8,
            'min_risk_reward': 2.0,
        }
        self.max_leveraged_exposure = 0.50
        self.max_leveraged_positions = 3
        self.stop_multipliers = {
            LeverageLevel.NONE: 1.0,
            LeverageLevel.LOW: 0.75,
            LeverageLevel.MEDIUM: 0.60,
            LeverageLevel.HIGH: 0.45,
            LeverageLevel.EXTREME: 0.30,
        }
        self.leveraged_positions = 0
        self.daily_leveraged_trades = 0
        self.max_daily_leveraged = 10
        logger.info(f"🚀 LEVERAGE MAX: {self.max_leverage}x")
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        reasons = []
        can_leverage = True
        confidence = signal.get('confidence', 0)
        score = signal.get('score', 0)
        risk_reward = signal.get('risk_reward', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        
        if confidence < self.thresholds['min_confidence']:
            reasons.append(f"❌ Confiance {confidence:.0f}%")
            can_leverage = False
        else:
            reasons.append(f"✅ Confiance: {confidence:.0f}%")
        
        if score < self.thresholds['min_score']:
            can_leverage = False
        
        if self.leveraged_positions >= self.max_leveraged_positions:
            can_leverage = False
        
        if not can_leverage:
            level = LeverageLevel.NONE
            multiplier = 1.0
        elif confidence >= 95 and score >= 11:
            level = LeverageLevel.EXTREME
            multiplier = 5.0
            reasons.append("🔥🔥🔥 LEVERAGE 5x!")
        elif confidence >= 90 and score >= 10:
            level = LeverageLevel.HIGH
            multiplier = 3.0
            reasons.append("🔥🔥 LEVERAGE 3x!")
        elif confidence >= 85 and score >= 9:
            level = LeverageLevel.MEDIUM
            multiplier = 2.0
            reasons.append("🔥 LEVERAGE 2x")
        elif confidence >= 80 and score >= 8:
            level = LeverageLevel.LOW
            multiplier = 1.5
            reasons.append("🚀 LEVERAGE 1.5x")
        else:
            level = LeverageLevel.NONE
            multiplier = 1.0
        
        stop_multiplier = self.stop_multipliers[level]
        adjusted_stop = stop_loss_pct * stop_multiplier
        
        return LeverageDecision(
            can_leverage=can_leverage and multiplier > 1.0,
            multiplier=multiplier,
            level=level,
            reasons=reasons,
            adjusted_stop_loss=adjusted_stop,
            adjusted_position_size=1.0,
            risk_score=50
        )
    
    def open_leveraged_position(self):
        self.leveraged_positions += 1
    
    def close_leveraged_position(self, pnl: float):
        self.leveraged_positions = max(0, self.leveraged_positions - 1)
        self.daily_leveraged_trades += 1
    
    def reset_daily(self):
        self.daily_leveraged_trades = 0
    
    def get_status(self) -> Dict:
        return {
            'max_leverage': f'{self.max_leverage}x',
            'leveraged_positions': self.leveraged_positions,
            'daily_leveraged_trades': self.daily_leveraged_trades
        }
