"""
🚀 LEVERAGE MANAGER - Gestion Intelligente du Levier
====================================================
Utilise le leverage UNIQUEMENT quand les conditions sont OPTIMALES

RÈGLES STRICTES:
1. Confiance signal > 85%
2. Fear & Greed entre 40-60 (marché stable)
3. Pas de news majeures
4. Max 2x leverage (conservateur)
5. Stop loss OBLIGATOIRE réduit
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LeverageLevel(Enum):
    """Niveaux de leverage autorisés"""
    NONE = 1.0       # Pas de leverage
    LOW = 1.25       # 1.25x - Confiance moyenne-haute
    MEDIUM = 1.5     # 1.5x - Haute confiance
    HIGH = 2.0       # 2x - Confiance extrême (rare)


@dataclass
class LeverageDecision:
    """Résultat de la décision de leverage"""
    can_leverage: bool
    multiplier: float
    level: LeverageLevel
    reasons: list
    adjusted_stop_loss: float  # Stop plus serré avec leverage
    adjusted_position_size: float  # Position ajustée
    risk_score: float  # Score de risque 0-100


class LeverageManager:
    """
    Gestionnaire de Leverage Intelligent
    =====================================
    
    Ne prend du leverage QUE quand TOUT est aligné:
    - Signal très fort
    - Marché stable
    - Volatilité normale
    - Risk/Reward excellent
    """
    
    def __init__(self, market_checker=None):
        self.market_checker = market_checker
        
        # Seuils STRICTS pour leverage
        self.thresholds = {
            'min_confidence': 80,      # 80% minimum pour considérer leverage
            'high_confidence': 85,     # 85% pour 1.25x
            'very_high_confidence': 90, # 90% pour 1.5x
            'extreme_confidence': 95,   # 95% pour 2x (très rare)
            'min_score': 9,            # Score minimum 9/12
            'min_risk_reward': 2.5,    # R/R minimum 1:2.5
        }
        
        # Limites de sécurité
        self.max_leverage = 2.0
        self.max_leveraged_exposure = 0.30  # Max 30% du capital avec leverage
        self.max_leveraged_positions = 1    # 1 seule position leverage à la fois
        
        # Ajustements stops avec leverage
        self.stop_multipliers = {
            LeverageLevel.NONE: 1.0,
            LeverageLevel.LOW: 0.8,     # Stop 20% plus serré
            LeverageLevel.MEDIUM: 0.65, # Stop 35% plus serré
            LeverageLevel.HIGH: 0.5,    # Stop 50% plus serré
        }
        
        # Tracking
        self.leveraged_positions = 0
        self.daily_leveraged_trades = 0
        self.max_daily_leveraged = 3  # Max 3 trades leverage/jour
    
    def can_use_leverage(self, signal: Dict, market_conditions: Dict = None) -> LeverageDecision:
        """
        Détermine si on peut utiliser le leverage
        
        Args:
            signal: Signal de trading avec score, confiance, etc.
            market_conditions: Conditions de marché (Fear & Greed, etc.)
        
        Returns:
            LeverageDecision avec tous les détails
        """
        reasons = []
        can_leverage = True
        
        # Récupérer métriques du signal
        confidence = signal.get('confidence', 0)
        score = signal.get('score', 0)
        risk_reward = signal.get('risk_reward', 0)
        stop_loss_pct = signal.get('stop_loss_pct', 2)
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 1: Confiance minimum
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
        # CHECK 4: Conditions de marché
        # ═══════════════════════════════════════════════════════════
        if market_conditions:
            if not market_conditions.get('can_leverage', False):
                reasons.append("❌ Marché non favorable au leverage")
                can_leverage = False
            else:
                reasons.append("✅ Marché stable")
        elif self.market_checker:
            can_lev, _ = self.market_checker.can_use_leverage()
            if not can_lev:
                reasons.append("❌ Conditions marché défavorables")
                can_leverage = False
        
        # ═══════════════════════════════════════════════════════════
        # CHECK 5: Limites de positions leverage
        # ═══════════════════════════════════════════════════════════
        if self.leveraged_positions >= self.max_leveraged_positions:
            reasons.append(f"❌ Max positions leverage atteint ({self.leveraged_positions})")
            can_leverage = False
        
        if self.daily_leveraged_trades >= self.max_daily_leveraged:
            reasons.append(f"❌ Max trades leverage/jour atteint ({self.daily_leveraged_trades})")
            can_leverage = False
        
        # ═══════════════════════════════════════════════════════════
        # DÉTERMINER NIVEAU DE LEVERAGE
        # ═══════════════════════════════════════════════════════════
        if not can_leverage:
            level = LeverageLevel.NONE
            multiplier = 1.0
        elif confidence >= self.thresholds['extreme_confidence'] and score >= 11:
            level = LeverageLevel.HIGH
            multiplier = 2.0
            reasons.append(f"🚀 LEVERAGE 2x - Signal exceptionnel!")
        elif confidence >= self.thresholds['very_high_confidence'] and score >= 10:
            level = LeverageLevel.MEDIUM
            multiplier = 1.5
            reasons.append(f"🚀 LEVERAGE 1.5x - Signal très fort")
        elif confidence >= self.thresholds['high_confidence'] and score >= 9:
            level = LeverageLevel.LOW
            multiplier = 1.25
            reasons.append(f"🚀 LEVERAGE 1.25x - Signal fort")
        else:
            level = LeverageLevel.NONE
            multiplier = 1.0
            reasons.append("📊 Pas de leverage - Signal standard")
        
        # ═══════════════════════════════════════════════════════════
        # CALCUL AJUSTEMENTS
        # ═══════════════════════════════════════════════════════════
        stop_multiplier = self.stop_multipliers[level]
        adjusted_stop = stop_loss_pct * stop_multiplier
        
        # Score de risque (0 = safe, 100 = danger)
        risk_score = self._calculate_risk_score(signal, market_conditions, multiplier)
        
        return LeverageDecision(
            can_leverage=can_leverage and multiplier > 1.0,
            multiplier=multiplier,
            level=level,
            reasons=reasons,
            adjusted_stop_loss=adjusted_stop,
            adjusted_position_size=1.0,  # Sera calculé par risk manager
            risk_score=risk_score
        )
    
    def _calculate_risk_score(self, signal: Dict, market: Dict, multiplier: float) -> float:
        """Calcule un score de risque global"""
        score = 50  # Base
        
        # Confiance réduit le risque
        confidence = signal.get('confidence', 50)
        score -= (confidence - 50) * 0.3
        
        # Leverage augmente le risque
        score += (multiplier - 1) * 20
        
        # Conditions marché
        if market:
            fg = market.get('fear_greed', {}).get('value', 50)
            # Extrêmes augmentent risque
            score += abs(fg - 50) * 0.3
        
        return max(0, min(100, score))
    
    def apply_leverage(self, position_size: float, decision: LeverageDecision) -> Dict:
        """
        Applique le leverage à une taille de position
        
        Returns:
            Dict avec position ajustée et paramètres
        """
        if not decision.can_leverage:
            return {
                'position_size': position_size,
                'leverage': 1.0,
                'effective_exposure': position_size,
                'stop_loss_pct': None  # Garder le stop original
            }
        
        # Position effective avec leverage
        leveraged_size = position_size * decision.multiplier
        
        # On garde la même position mais avec exposure plus grande
        result = {
            'position_size': position_size,  # Capital réel utilisé
            'leverage': decision.multiplier,
            'effective_exposure': leveraged_size,  # Exposition effective
            'stop_loss_pct': decision.adjusted_stop_loss,
            'level': decision.level.name,
            'risk_score': decision.risk_score
        }
        
        logger.info(f"🚀 LEVERAGE APPLIQUÉ:")
        logger.info(f"   Position: ${position_size:.2f}")
        logger.info(f"   Leverage: {decision.multiplier}x")
        logger.info(f"   Exposition: ${leveraged_size:.2f}")
        logger.info(f"   Stop ajusté: {decision.adjusted_stop_loss:.2f}%")
        
        return result
    
    def record_leveraged_trade(self, pnl: float):
        """Enregistre un trade avec leverage"""
        self.daily_leveraged_trades += 1
        if pnl >= 0:
            logger.info(f"✅ Trade leverage gagnant: +${pnl:.2f}")
        else:
            logger.warning(f"❌ Trade leverage perdant: ${pnl:.2f}")
    
    def open_leveraged_position(self):
        """Marque une position leverage ouverte"""
        self.leveraged_positions += 1
    
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
            'leveraged_positions': self.leveraged_positions,
            'max_leveraged_positions': self.max_leveraged_positions,
            'daily_leveraged_trades': self.daily_leveraged_trades,
            'max_daily_leveraged': self.max_daily_leveraged,
            'max_leverage': self.max_leverage
        }


class SafeLeverageCalculator:
    """
    Calculateur de leverage sécurisé
    Détermine le leverage optimal basé sur plusieurs facteurs
    """
    
    @staticmethod
    def calculate_safe_leverage(
        confidence: float,
        score: float,
        risk_reward: float,
        volatility: float,
        market_score: float = 50
    ) -> float:
        """
        Calcule un leverage "safe" basé sur tous les facteurs
        
        Returns: float entre 1.0 et 2.0
        """
        # Base 1.0 (pas de leverage)
        leverage = 1.0
        
        # Confiance (max +0.4)
        if confidence > 80:
            leverage += (confidence - 80) / 100  # +0.01 par % au dessus de 80
        
        # Score (max +0.3)
        if score > 8:
            leverage += (score - 8) * 0.075
        
        # R/R (max +0.2)
        if risk_reward > 2:
            leverage += min(0.2, (risk_reward - 2) * 0.1)
        
        # Pénalité volatilité
        if volatility > 5:
            leverage -= (volatility - 5) * 0.05
        
        # Pénalité marché instable
        if market_score < 40 or market_score > 70:
            leverage -= 0.2
        
        # Bornes
        leverage = max(1.0, min(2.0, leverage))
        
        return round(leverage, 2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 TEST LEVERAGE MANAGER")
    print("=" * 50)
    
    manager = LeverageManager()
    
    # Test signal fort
    signal_fort = {
        'confidence': 92,
        'score': 10.5,
        'risk_reward': 3.0,
        'stop_loss_pct': 2.0
    }
    
    decision = manager.can_use_leverage(signal_fort)
    
    print(f"\n📊 Signal Fort:")
    print(f"   Can Leverage: {decision.can_leverage}")
    print(f"   Multiplier: {decision.multiplier}x")
    print(f"   Level: {decision.level.name}")
    print(f"   Risk Score: {decision.risk_score:.0f}")
    print(f"   Stop ajusté: {decision.adjusted_stop_loss:.2f}%")
    print(f"\n   Raisons:")
    for r in decision.reasons:
        print(f"   {r}")
    
    # Test signal faible
    print("\n" + "=" * 50)
    signal_faible = {
        'confidence': 70,
        'score': 7,
        'risk_reward': 1.5,
        'stop_loss_pct': 2.0
    }
    
    decision2 = manager.can_use_leverage(signal_faible)
    print(f"\n📊 Signal Faible:")
    print(f"   Can Leverage: {decision2.can_leverage}")
    print(f"   Multiplier: {decision2.multiplier}x")

