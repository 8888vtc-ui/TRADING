"""LEVERAGE MANAGER - UNIFIÉ AVEC STRATÉGIE OPTIMALE"""
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
    """Leverage Manager unifié avec la stratégie optimale"""
    
    def __init__(self, market_checker=None):
        self.market_checker = market_checker
        self.max_leverage = 5.0
        self.leveraged_positions = 0
        self.max_leveraged_positions = 3
        self.daily_leveraged_trades = 0
        self.market_score = 50
        self.unified_score = 50  # Score de la stratégie optimale
        
        # Matrice leverage basée sur score unifié
        self.leverage_matrix = {
            (90, 100): 5.0,
            (80, 90): 3.0,
            (70, 80): 2.0,
            (60, 70): 1.5,
            (55, 60): 1.0,
            (0, 55): 0,
        }
        
        # Stops ajustés par leverage
        self.stop_multipliers = {
            LeverageLevel.NONE: 1.0,
            LeverageLevel.LOW: 0.75,
            LeverageLevel.MEDIUM: 0.60,
            LeverageLevel.HIGH: 0.45,
            LeverageLevel.EXTREME: 0.30,
        }
    
    def set_unified_score(self, score: int):
        """Met à jour le score unifié depuis la stratégie optimale"""
        self.unified_score = score
        logger.info(f"🏆 Score Unifié: {score}/100")
    
    def get_optimal_leverage(self) -> float:
        """Retourne le leverage optimal basé sur le score unifié"""
        for (min_s, max_s), lev in self.leverage_matrix.items():
            if min_s <= self.unified_score < max_s:
                return lev
        return 1.0
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        confidence = signal.get('confidence', 0)
        score = signal.get('score', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        reasons = []
        
        # Utiliser le leverage optimal basé sur le score unifié
        optimal_lev = self.get_optimal_leverage()
        
        can_leverage = (
            optimal_lev > 1.0 and 
            confidence >= 60 and 
            self.leveraged_positions < self.max_leveraged_positions
        )
        
        # Mapper au niveau
        if optimal_lev >= 5:
            level = LeverageLevel.EXTREME
            reasons.append(f"🔥🔥🔥 Score {self.unified_score} → LEVERAGE 5x!")
        elif optimal_lev >= 3:
            level = LeverageLevel.HIGH
            reasons.append(f"🔥🔥 Score {self.unified_score} → LEVERAGE 3x!")
        elif optimal_lev >= 2:
            level = LeverageLevel.MEDIUM
            reasons.append(f"🔥 Score {self.unified_score} → LEVERAGE 2x")
        elif optimal_lev >= 1.5:
            level = LeverageLevel.LOW
            reasons.append(f"✅ Score {self.unified_score} → LEVERAGE 1.5x")
        else:
            level = LeverageLevel.NONE
            can_leverage = False
            reasons.append(f"📊 Score {self.unified_score} → Pas de leverage")
        
        adjusted_stop = stop_loss_pct * self.stop_multipliers[level]
        
        return LeverageDecision(
            can_leverage=can_leverage,
            multiplier=optimal_lev if can_leverage else 1.0,
            level=level,
            reasons=reasons,
            adjusted_stop_loss=adjusted_stop,
            adjusted_position_size=1.0,
            risk_score=self.unified_score
        )
    
    def open_leveraged_position(self): 
        self.leveraged_positions += 1
    
    def close_leveraged_position(self, pnl): 
        self.leveraged_positions = max(0, self.leveraged_positions - 1)
        self.daily_leveraged_trades += 1
    
    def reset_daily(self): 
        self.daily_leveraged_trades = 0
    
    def get_status(self): 
        return {
            'max_leverage': '5x', 
            'positions': self.leveraged_positions,
            'unified_score': self.unified_score,
            'optimal_leverage': f'{self.get_optimal_leverage()}x'
        }
