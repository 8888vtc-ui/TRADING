"""
🚀 LEVERAGE MANAGER V2.0 - MODE PAPER TRADING AGRESSIF
=====================================================
LEVERAGE MAX: 5x (pour tester en paper trading)

⚠️ ATTENTION: Ces paramètres sont pour PAPER TRADING uniquement!
Réduire avant de passer en réel!

NIVEAUX:
- 85% confiance → 2x
- 90% confiance → 3x  
- 95% confiance → 5x (MAX)
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LeverageLevel(Enum):
    """Niveaux de leverage - MODE AGRESSIF"""
    NONE = 1.0       # Pas de leverage
    LOW = 1.5        # 1.5x - Confiance 80%+
    MEDIUM = 2.0     # 2x - Confiance 85%+
    HIGH = 3.0       # 3x - Confiance 90%+
    EXTREME = 5.0    # 5x - Confiance 95%+ (PAPER ONLY!)


@dataclass
class LeverageDecision:
    """Résultat de la décision de leverage"""
    can_leverage: bool
    multiplier: float
    level: LeverageLevel
    reasons: list
    adjusted_stop_loss: float
    adjusted_position_size: float
    risk_score: float


class LeverageManager:
    """
    🚀 LEVERAGE MANAGER - MODE PAPER TRADING AGRESSIF
    ================================================
    
    ⚠️ PARAMÈTRES AGRESSIFS POUR TEST PAPER TRADING
    
    En paper trading on peut tester les limites!
    À réduire avant passage en réel.
    """
    
    def __init__(self, market_checker=None):
        self.market_checker = market_checker
        
        # ═══════════════════════════════════════════════════════════
        # 🚀 PARAMÈTRES AGRESSIFS (PAPER TRADING)
        # ═══════════════════════════════════════════════════════════
        
        self.max_leverage = 5.0  # 🔥 MAX 5x en paper trading!
        
        # Seuils de confiance pour chaque niveau
        self.thresholds = {
            'min_confidence': 75,       # 75% pour considérer leverage
            'low_confidence': 80,       # 80% → 1.5x
            'medium_confidence': 85,    # 85% → 2x
            'high_confidence': 90,      # 90% → 3x
            'extreme_confidence': 95,   # 95% → 5x
            'min_score': 8,             # Score minimum 8/12
            'min_risk_reward': 2.0,     # R/R minimum 1:2
        }
        
        # Limites (plus souples pour paper trading)
        self.max_leveraged_exposure = 0.50  # 50% du capital avec leverage
        self.max_leveraged_positions = 3    # 3 positions leverage max
        
        # Ajustements stops avec leverage (TRÈS IMPORTANT)
        self.stop_multipliers = {
            LeverageLevel.NONE: 1.0,
            LeverageLevel.LOW: 0.75,     # Stop 25% plus serré
            LeverageLevel.MEDIUM: 0.60,  # Stop 40% plus serré
            LeverageLevel.HIGH: 0.45,    # Stop 55% plus serré
            LeverageLevel.EXTREME: 0.30, # Stop 70% plus serré
        }
        
        # Tracking
        self.leveraged_positions = 0
        self.daily_leveraged_trades = 0
        self.max_daily_leveraged = 10  # Plus de trades autorisés en paper
        
        logger.info("🚀 LEVERAGE MANAGER - MODE PAPER TRADING AGRESSIF")
        logger.info(f"   Max Leverage: {self.max_leverage}x")
        logger.info(f"   Max Positions Leverage: {self.max_leveraged_positions}")
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        """
        Détermine si on peut utiliser le leverage et à quel niveau
        
        MODE AGRESSIF pour paper trading!
        """
        reasons = []
        can_leverage = True
        
        confidence = signal.get('confidence', 0)
        score = signal.get('score', 0)
        risk_reward = signal.get('risk_reward', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 1: Confiance minimum (assoupli pour paper)
        # ═══════════════════════════════════════════════════════════
        if confidence < self.thresholds['min_confidence']:
            reasons.append(f"❌ Confiance insuffisante ({confidence:.0f}% < {self.thresholds['min_confidence']}%)")
            can_leverage = False
        else:
            reasons.append(f"✅ Confiance: {confidence:.0f}%")
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 2: Score minimum
        # ═══════════════════════════════════════════════════════════
        if score < self.thresholds['min_score']:
            reasons.append(f"❌ Score insuffisant ({score:.1f} < {self.thresholds['min_score']})")
            can_leverage = False
        else:
            reasons.append(f"✅ Score: {score:.1f}/12")
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 3: Risk/Reward
        # ═══════════════════════════════════════════════════════════
        if risk_reward < self.thresholds['min_risk_reward']:
            reasons.append(f"❌ R/R insuffisant ({risk_reward:.1f} < {self.thresholds['min_risk_reward']})")
            can_leverage = False
        else:
            reasons.append(f"✅ Risk/Reward: 1:{risk_reward:.1f}")
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 4: Conditions de marché (plus souple en paper)
        # ═══════════════════════════════════════════════════════════
        if market_conditions:
            # En paper trading, on est plus permissif
            fg_value = market_conditions.get('fear_greed', {}).get('value', 50)
            if fg_value > 85 or fg_value < 15:
                reasons.append(f"⚠️ Marché extrême (F&G: {fg_value}) - Leverage réduit")
                # On réduit mais on n'annule pas en paper
            else:
                reasons.append("✅ Marché OK pour leverage")
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 5: Limites de positions
        # ═══════════════════════════════════════════════════════════
        if self.leveraged_positions >= self.max_leveraged_positions:
            reasons.append(f"❌ Max positions leverage atteint ({self.leveraged_positions})")
            can_leverage = False
        
        if self.daily_leveraged_trades >= self.max_daily_leveraged:
            reasons.append(f"❌ Max trades leverage/jour atteint ({self.daily_leveraged_trades})")
            can_leverage = False
        
        # ═══════════════════════════════════════════════════════════
        # 🚀 DÉTERMINER NIVEAU DE LEVERAGE (AGRESSIF)
        # ═══════════════════════════════════════════════════════════
        if not can_leverage:
            level = LeverageLevel.NONE
            multiplier = 1.0
        elif confidence >= self.thresholds['extreme_confidence'] and score >= 11:
            level = LeverageLevel.EXTREME
            multiplier = 5.0
            reasons.append(f"🔥🔥🔥 LEVERAGE 5x - Signal EXCEPTIONNEL!")
        elif confidence >= self.thresholds['high_confidence'] and score >= 10:
            level = LeverageLevel.HIGH
            multiplier = 3.0
            reasons.append(f"🔥🔥 LEVERAGE 3x - Signal très fort!")
        elif confidence >= self.thresholds['medium_confidence'] and score >= 9:
            level = LeverageLevel.MEDIUM
            multiplier = 2.0
            reasons.append(f"🔥 LEVERAGE 2x - Signal fort")
        elif confidence >= self.thresholds['low_confidence'] and score >= 8:
            level = LeverageLevel.LOW
            multiplier = 1.5
            reasons.append(f"🚀 LEVERAGE 1.5x - Signal bon")
        else:
            level = LeverageLevel.NONE
            multiplier = 1.0
            reasons.append("📊 Pas de leverage - Signal standard")
        
        # ═══════════════════════════════════════════════════════════
        # CALCUL STOP AJUSTÉ
        # ═══════════════════════════════════════════════════════════
        stop_multiplier = self.stop_multipliers[level]
        adjusted_stop = stop_loss_pct * stop_multiplier
        
        risk_score = self._calculate_risk_score(signal, market_conditions, multiplier)
        
        return LeverageDecision(
            can_leverage=can_leverage and multiplier > 1.0,
            multiplier=multiplier,
            level=level,
            reasons=reasons,
            adjusted_stop_loss=adjusted_stop,
            adjusted_position_size=1.0,
            risk_score=risk_score
        )
    
    def _calculate_risk_score(self, signal: Dict, market: Dict, multiplier: float) -> float:
        """Calcule un score de risque global"""
        score = 50
        
        confidence = signal.get('confidence', 50)
        score -= (confidence - 50) * 0.3
        
        # Leverage augmente le risque
        score += (multiplier - 1) * 15
        
        if market:
            fg = market.get('fear_greed', {}).get('value', 50)
            score += abs(fg - 50) * 0.3
        
        return max(0, min(100, score))
    
    def apply_leverage(self, position_size: float, decision: LeverageDecision) -> Dict:
        """Applique le leverage à une position"""
        if not decision.can_leverage:
            return {
                'position_size': position_size,
                'leverage': 1.0,
                'effective_exposure': position_size,
                'stop_loss_pct': None
            }
        
        leveraged_size = position_size * decision.multiplier
        
        result = {
            'position_size': position_size,
            'leverage': decision.multiplier,
            'effective_exposure': leveraged_size,
            'stop_loss_pct': decision.adjusted_stop_loss,
            'level': decision.level.name,
            'risk_score': decision.risk_score
        }
        
        logger.info(f"🚀 LEVERAGE {decision.multiplier}x APPLIQUÉ!")
        logger.info(f"   Position: ${position_size:.2f}")
        logger.info(f"   Exposition: ${leveraged_size:.2f}")
        logger.info(f"   Stop ajusté: {decision.adjusted_stop_loss:.2f}%")
        
        return result
    
    def record_leveraged_trade(self, pnl: float):
        """Enregistre un trade avec leverage"""
        self.daily_leveraged_trades += 1
        if pnl >= 0:
            logger.info(f"✅ Trade leverage GAGNANT: +${pnl:.2f}")
        else:
            logger.warning(f"❌ Trade leverage perdant: ${pnl:.2f}")
    
    def open_leveraged_position(self):
        """Ouvre une position leverage"""
        self.leveraged_positions += 1
        logger.info(f"🚀 Position leverage ouverte ({self.leveraged_positions}/{self.max_leveraged_positions})")
    
    def close_leveraged_position(self, pnl: float):
        """Ferme une position leverage"""
        self.leveraged_positions = max(0, self.leveraged_positions - 1)
        self.record_leveraged_trade(pnl)
    
    def reset_daily(self):
        """Reset quotidien"""
        logger.info(f"📊 Trades leverage aujourd'hui: {self.daily_leveraged_trades}")
        self.daily_leveraged_trades = 0
    
    def get_status(self) -> Dict:
        """Statut du leverage manager"""
        return {
            'mode': '🔥 PAPER TRADING AGRESSIF',
            'max_leverage': f'{self.max_leverage}x',
            'leveraged_positions': self.leveraged_positions,
            'max_leveraged_positions': self.max_leveraged_positions,
            'daily_leveraged_trades': self.daily_leveraged_trades,
            'max_daily_leveraged': self.max_daily_leveraged
        }


class SafeLeverageCalculator:
    """Calculateur de leverage (version paper trading)"""
    
    @staticmethod
    def calculate_safe_leverage(
        confidence: float,
        score: float,
        risk_reward: float,
        volatility: float,
        market_score: float = 50
    ) -> float:
        """Calcule le leverage optimal - MODE AGRESSIF"""
        leverage = 1.0
        
        # Confiance (max +2.0 en mode agressif)
        if confidence > 75:
            leverage += (confidence - 75) / 20
        
        # Score (max +1.5)
        if score > 7:
            leverage += (score - 7) * 0.3
        
        # R/R (max +1.0)
        if risk_reward > 1.5:
            leverage += min(1.0, (risk_reward - 1.5) * 0.4)
        
        # Pénalité volatilité (réduite en paper)
        if volatility > 8:
            leverage -= (volatility - 8) * 0.1
        
        # Bornes: 1x à 5x
        leverage = max(1.0, min(5.0, leverage))
        
        return round(leverage, 2)


# ═══════════════════════════════════════════════════════════════════
# 📋 PARAMÈTRES POUR PASSAGE EN RÉEL (À UTILISER PLUS TARD)
# ═══════════════════════════════════════════════════════════════════
"""
QUAND TU PASSES EN RÉEL, MODIFIER CES VALEURS:

self.max_leverage = 2.0              # Réduire à 2x max
self.max_leveraged_positions = 1     # 1 seule position leverage
self.max_daily_leveraged = 3         # 3 trades max/jour

self.thresholds = {
    'min_confidence': 85,            # Plus strict
    'medium_confidence': 90,
    'high_confidence': 95,
    'min_score': 9,
    'min_risk_reward': 2.5,
}
"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 TEST LEVERAGE MANAGER - MODE PAPER TRADING AGRESSIF")
    print("=" * 60)
    
    manager = LeverageManager()
    
    # Test signal EXTREME
    signal_extreme = {
        'confidence': 96,
        'score': 11.5,
        'risk_reward': 3.5,
        'stop_loss_pct': 2.0
    }
    
    decision = manager.can_use_leverage(signal_extreme)
    
    print(f"\n🔥 Signal EXCEPTIONNEL:")
    print(f"   Confiance: 96%, Score: 11.5/12")
    print(f"   Can Leverage: {decision.can_leverage}")
    print(f"   Multiplier: {decision.multiplier}x")
    print(f"   Level: {decision.level.name}")
    print(f"   Stop ajusté: {decision.adjusted_stop_loss:.2f}%")
    print(f"\n   Raisons:")
    for r in decision.reasons:
        print(f"   {r}")
    
    # Test signal fort
    print("\n" + "=" * 60)
    signal_fort = {
        'confidence': 88,
        'score': 9.5,
        'risk_reward': 2.5,
        'stop_loss_pct': 2.0
    }
    
    decision2 = manager.can_use_leverage(signal_fort)
    print(f"\n🚀 Signal FORT:")
    print(f"   Confiance: 88%, Score: 9.5/12")
    print(f"   Multiplier: {decision2.multiplier}x")
    print(f"   Level: {decision2.level.name}")
