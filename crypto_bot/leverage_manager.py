"""LEVERAGE MANAGER - PAPER TRADING 5x MAX - LIEN MARKET INTELLIGENCE"""
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
        
        # NOUVEAU: Leverage basé sur Market Intelligence
        self.market_score = 50  # Score par défaut
    
    def set_market_score(self, score: int):
        """Met à jour le score du marché depuis Market Intelligence"""
        self.market_score = score
        logger.info(f"🧠 Leverage Manager: Market Score mis à jour → {score}/100")
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        confidence = signal.get('confidence', 0)
        score = signal.get('score', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        reasons = []
        
        # NOUVEAU: Boost basé sur Market Intelligence
        market_boost = 0
        if self.market_score >= 80:
            market_boost = 2  # Marché SUPER → Boost +2 niveaux
            reasons.append(f"🧠 MARCHÉ SUPER ({self.market_score}) → LEVERAGE MAX!")
        elif self.market_score >= 70:
            market_boost = 1  # Marché Excellent → Boost +1 niveau
            reasons.append(f"🧠 Marché excellent ({self.market_score}) → Leverage boost!")
        elif self.market_score < 40:
            market_boost = -2  # Marché risqué → Réduction
            reasons.append(f"⚠️ Marché risqué ({self.market_score}) → Leverage réduit")
        
        can_leverage = confidence >= 75 and score >= 8 and self.leveraged_positions < 3
        
        # Calcul du niveau de base
        if confidence >= 95 and score >= 11:
            base_level = 4  # EXTREME
        elif confidence >= 90 and score >= 10:
            base_level = 3  # HIGH
        elif confidence >= 85 and score >= 9:
            base_level = 2  # MEDIUM
        elif confidence >= 80 and score >= 8:
            base_level = 1  # LOW
        else:
            base_level = 0  # NONE
            can_leverage = False
        
        # Appliquer le boost du marché
        final_level = max(0, min(4, base_level + market_boost))
        
        # Mapper au niveau de leverage
        level_map = {0: (LeverageLevel.NONE, 1.0), 1: (LeverageLevel.LOW, 1.5), 2: (LeverageLevel.MEDIUM, 2.0), 3: (LeverageLevel.HIGH, 3.0), 4: (LeverageLevel.EXTREME, 5.0)}
        level, multiplier = level_map[final_level]
        
        # Si marché SUPER (80+) et signal OK (75%+), forcer leverage élevé
        if self.market_score >= 80 and confidence >= 75 and score >= 7:
            level = LeverageLevel.EXTREME
            multiplier = 5.0
            can_leverage = True
            reasons.append("🔥🔥🔥 MARCHÉ SUPER + SIGNAL OK = LEVERAGE 5x FORCÉ!")
        
        if multiplier > 1:
            reasons.append(f"📊 Leverage final: {multiplier}x (base {base_level} + boost {market_boost})")
        
        return LeverageDecision(can_leverage=can_leverage, multiplier=multiplier, level=level, reasons=reasons, adjusted_stop_loss=stop_loss_pct * self.stop_multipliers[level], adjusted_position_size=1.0, risk_score=50)
    
    def open_leveraged_position(self): self.leveraged_positions += 1
    def close_leveraged_position(self, pnl): self.leveraged_positions = max(0, self.leveraged_positions - 1)
    def reset_daily(self): self.daily_leveraged_trades = 0
    def get_status(self): return {'max_leverage': '5x', 'positions': self.leveraged_positions, 'market_score': self.market_score}
