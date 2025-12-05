"""
🚀 LEVERAGE MANAGER V2.0 - AVEC SCORING UNIFIÉ
==============================================
Gestion intelligente du leverage basée sur:
- Score unifié (APIs + Indicateurs)
- Conditions de marché
- Mode PANIC pour short
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

class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"
    NONE = "none"

@dataclass
class LeverageDecision:
    can_leverage: bool
    multiplier: float
    level: LeverageLevel
    direction: TradeDirection
    reasons: list
    adjusted_stop_loss: float
    adjusted_position_size: float
    risk_score: float

class LeverageManager:
    """Leverage Manager V2.0 - Basé sur score unifié"""
    
    def __init__(self, market_checker=None):
        self.market_checker = market_checker
        self.max_leverage = 5.0
        self.leveraged_positions = 0
        self.max_leveraged_positions = 3
        self.daily_leveraged_trades = 0
        self.unified_score = 50
        
        # Mode PANIC pour short
        self.panic_mode = False
        self.fear_greed = 50
        self.market_change_24h = 0
        
        # Matrice LONG (score élevé = bullish)
        self.long_matrix = {
            (90, 101): 5.0,
            (80, 90): 3.0,
            (70, 80): 2.0,
            (60, 70): 1.5,
            (55, 60): 1.0,
            (0, 55): 0
        }
        
        # Matrice SHORT/PANIC
        self.short_matrix = {
            (0, 15): 5.0,
            (15, 25): 3.0,
            (25, 35): 2.0,
            (35, 45): 1.5
        }
        
        self.stop_multipliers = {
            LeverageLevel.NONE: 1.0,
            LeverageLevel.LOW: 0.75,
            LeverageLevel.MEDIUM: 0.60,
            LeverageLevel.HIGH: 0.45,
            LeverageLevel.EXTREME: 0.30
        }
        
        logger.info("🚀 Leverage Manager V2.0 initialisé")
    
    def set_market_conditions(self, fear_greed: int, market_change_24h: float):
        """Met à jour les conditions pour détecter le mode PANIC"""
        self.fear_greed = fear_greed
        self.market_change_24h = market_change_24h
        
        old_panic = self.panic_mode
        self.panic_mode = (fear_greed < 20 and market_change_24h < -3)
        
        if self.panic_mode and not old_panic:
            logger.warning("🚨🚨🚨 MODE PANIC ACTIVÉ - SHORT AUTORISÉ!")
        elif not self.panic_mode and old_panic:
            logger.info("✅ Mode PANIC désactivé")
    
    def set_unified_score(self, score: int):
        """Met à jour le score unifié"""
        self.unified_score = max(0, min(100, score))
        logger.info(f"🏆 Score Unifié: {self.unified_score}/100")
    
    def get_optimal_leverage_and_direction(self) -> tuple:
        """Retourne (leverage, direction) selon le score"""
        
        # MODE PANIC → SHORT
        if self.panic_mode:
            for (min_s, max_s), lev in self.short_matrix.items():
                if min_s <= self.fear_greed < max_s:
                    return lev, TradeDirection.SHORT
            if self.fear_greed < 45 and self.market_change_24h < -2:
                return 1.0, TradeDirection.SHORT
            return 0, TradeDirection.NONE
        
        # MODE NORMAL → LONG
        for (min_s, max_s), lev in self.long_matrix.items():
            if min_s <= self.unified_score < max_s:
                return lev, TradeDirection.LONG
        
        return 0, TradeDirection.NONE
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        confidence = signal.get('confidence', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        
        optimal_lev, direction = self.get_optimal_leverage_and_direction()
        
        can_leverage = (
            optimal_lev > 1.0 and
            confidence >= 60 and
            self.leveraged_positions < self.max_leveraged_positions and
            direction != TradeDirection.NONE
        )
        
        reasons = []
        
        if optimal_lev >= 5:
            level = LeverageLevel.EXTREME
            emoji = "🔴🔴🔴" if direction == TradeDirection.SHORT else "🟢🟢🟢"
            reasons.append(f"{emoji} {direction.value.upper()} 5x! Score={self.unified_score}")
        elif optimal_lev >= 3:
            level = LeverageLevel.HIGH
            emoji = "🔴🔴" if direction == TradeDirection.SHORT else "🟢🟢"
            reasons.append(f"{emoji} {direction.value.upper()} 3x! Score={self.unified_score}")
        elif optimal_lev >= 2:
            level = LeverageLevel.MEDIUM
            reasons.append(f"{'🔴' if direction == TradeDirection.SHORT else '🟢'} {direction.value.upper()} 2x")
        elif optimal_lev >= 1.5:
            level = LeverageLevel.LOW
            reasons.append(f"{'🔴' if direction == TradeDirection.SHORT else '🟢'} {direction.value.upper()} 1.5x")
        elif optimal_lev >= 1:
            level = LeverageLevel.NONE
            reasons.append(f"{'🔴' if direction == TradeDirection.SHORT else '🟢'} {direction.value.upper()} 1x")
        else:
            level = LeverageLevel.NONE
            can_leverage = False
            direction = TradeDirection.NONE
            reasons.append("📊 Pas de trade - conditions défavorables")
        
        stop_mult = self.stop_multipliers[level]
        if direction == TradeDirection.SHORT:
            stop_mult *= 0.8
        
        return LeverageDecision(
            can_leverage=can_leverage,
            multiplier=optimal_lev if can_leverage else 1.0,
            level=level,
            direction=direction,
            reasons=reasons,
            adjusted_stop_loss=stop_loss_pct * stop_mult,
            adjusted_position_size=1.0,
            risk_score=self.unified_score
        )
    
    def open_leveraged_position(self):
        self.leveraged_positions += 1
        self.daily_leveraged_trades += 1
    
    def close_leveraged_position(self, pnl):
        self.leveraged_positions = max(0, self.leveraged_positions - 1)
    
    def reset_daily(self):
        self.daily_leveraged_trades = 0
    
    def get_status(self):
        lev, direction = self.get_optimal_leverage_and_direction()
        return {
            'max_leverage': '5x',
            'positions': self.leveraged_positions,
            'unified_score': self.unified_score,
            'optimal_leverage': f'{lev}x',
            'direction': direction.value,
            'panic_mode': self.panic_mode,
            'fear_greed': self.fear_greed
        }
