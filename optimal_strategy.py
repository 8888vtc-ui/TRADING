"""
🏆 STRATÉGIE OPTIMALE UNIFIÉE V1.0
==================================
Combine intelligemment:
- APIs Informatives (Fear & Greed, VIX, Market Cap)
- Indicateurs Techniques (RSI, MACD, BB, EMA, ADX, Volume)
- Leverage Adaptatif
- Hold Duration Adaptatif
- Risk Management Dynamique

SCORING UNIFIÉ: 0-100 points
- 30 points: Market Intelligence (APIs)
- 40 points: Indicateurs Techniques
- 15 points: Volume & Momentum
- 15 points: Confirmation Multi-Timeframe

RÉSULTAT: Trade Score → Décision optimale
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class OptimalStrategy:
    """
    🏆 STRATÉGIE OPTIMALE - Combine APIs + Indicateurs + Leverage
    """
    
    def __init__(self):
        # ═══════════════════════════════════════════════════════════
        # POIDS DU SCORING UNIFIÉ
        # ═══════════════════════════════════════════════════════════
        self.weights = {
            'market_intel': 0.30,      # 30% - APIs informatives
            'technical': 0.40,          # 40% - Indicateurs techniques
            'volume_momentum': 0.15,    # 15% - Volume & Momentum
            'confirmation': 0.15,       # 15% - Confirmation multi-source
        }
        
        # ═══════════════════════════════════════════════════════════
        # SEUILS OPTIMAUX (basés sur backtests)
        # ═══════════════════════════════════════════════════════════
        self.thresholds = {
            # Score global
            'min_trade': 55,            # Score min pour trader
            'confident_trade': 70,      # Score pour trade confiant
            'strong_trade': 80,         # Score pour trade fort
            'exceptional_trade': 90,    # Score exceptionnel
            
            # Fear & Greed optimal
            'fg_buy_zone': (25, 55),    # Zone d'achat optimale
            'fg_danger': (0, 15),       # Danger - trop de peur
            'fg_overbought': (80, 100), # Suracheté
            
            # VIX optimal
            'vix_optimal': (12, 20),    # Zone VIX optimale
            'vix_caution': (20, 30),    # Zone prudente
            'vix_danger': (30, 100),    # Zone danger
            
            # RSI optimal
            'rsi_oversold': 30,         # Survendu
            'rsi_overbought': 70,       # Suracheté
            'rsi_buy_zone': (35, 55),   # Zone d'achat optimale
            
            # ADX pour tendance
            'adx_strong': 25,           # Tendance forte
            'adx_very_strong': 40,      # Tendance très forte
        }
        
        # ═══════════════════════════════════════════════════════════
        # LEVERAGE OPTIMAL (basé sur score)
        # ═══════════════════════════════════════════════════════════
        self.leverage_matrix = {
            # (score_min, score_max): leverage
            (90, 100): 5.0,  # Exceptionnel → 5x
            (80, 90): 3.0,   # Fort → 3x
            (70, 80): 2.0,   # Confiant → 2x
            (60, 70): 1.5,   # Bon → 1.5x
            (55, 60): 1.0,   # Acceptable → 1x
            (0, 55): 0,      # Pas de trade
        }
        
        # ═══════════════════════════════════════════════════════════
        # HOLD DURATION (basé sur conditions)
        # ═══════════════════════════════════════════════════════════
        self.hold_matrix = {
            # (market_score_min, market_score_max): hold_multiplier
            (80, 100): 2.5,   # Marché super → Hold très long
            (70, 80): 2.0,    # Marché excellent → Hold long
            (60, 70): 1.5,    # Marché bon → Hold moyen+
            (50, 60): 1.0,    # Marché normal → Hold normal
            (0, 50): 0.6,     # Marché risqué → Sortie rapide
        }
        
        # ═══════════════════════════════════════════════════════════
        # STOP LOSS OPTIMAL
        # ═══════════════════════════════════════════════════════════
        self.stop_matrix = {
            # leverage: stop_loss_pct
            5.0: 0.006,   # 5x → 0.6% stop (très serré)
            3.0: 0.01,    # 3x → 1% stop
            2.0: 0.015,   # 2x → 1.5% stop
            1.5: 0.02,    # 1.5x → 2% stop
            1.0: 0.025,   # 1x → 2.5% stop
        }
        
        logger.info("🏆 Stratégie Optimale Unifiée V1.0 initialisée")
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: MARKET INTELLIGENCE (30%)
    # ═══════════════════════════════════════════════════════════════
    def score_market_intel(self, market_data: Dict) -> Tuple[float, list]:
        """Score basé sur les APIs informatives"""
        score = 0
        reasons = []
        
        # Fear & Greed (max 12 points)
        fg = market_data.get('fear_greed', {}).get('value', 50)
        if 25 <= fg <= 55:
            score += 12
            reasons.append(f"✅ F&G optimal ({fg}): +12")
        elif 55 < fg <= 70:
            score += 8
            reasons.append(f"✅ F&G neutre ({fg}): +8")
        elif fg > 70:
            score += 2
            reasons.append(f"⚠️ F&G élevé ({fg}): +2")
        elif 15 < fg < 25:
            score += 10  # Contrarian opportunity
            reasons.append(f"✅ F&G peur ({fg}): +10 contrarian")
        else:
            score += 0
            reasons.append(f"❌ F&G extrême ({fg}): +0")
        
        # VIX (max 10 points)
        vix = market_data.get('vix', {}).get('value', 20)
        if 12 <= vix <= 20:
            score += 10
            reasons.append(f"✅ VIX optimal ({vix}): +10")
        elif 20 < vix <= 25:
            score += 6
            reasons.append(f"⚠️ VIX moyen ({vix}): +6")
        elif vix > 30:
            score += 0
            reasons.append(f"❌ VIX danger ({vix}): +0")
        else:
            score += 8
            reasons.append(f"✅ VIX bas ({vix}): +8")
        
        # Market Cap Change (max 8 points)
        mc_change = market_data.get('market', {}).get('market_cap_change_24h', 0)
        if mc_change > 3:
            score += 8
            reasons.append(f"✅ MC +{mc_change:.1f}%: +8")
        elif mc_change > 0:
            score += 5
            reasons.append(f"✅ MC +{mc_change:.1f}%: +5")
        elif mc_change > -3:
            score += 3
            reasons.append(f"⚠️ MC {mc_change:.1f}%: +3")
        else:
            score += 0
            reasons.append(f"❌ MC {mc_change:.1f}%: +0")
        
        # Normaliser sur 30 points max
        return min(30, score), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: INDICATEURS TECHNIQUES (40%)
    # ═══════════════════════════════════════════════════════════════
    def score_technical(self, indicators: Dict) -> Tuple[float, list]:
        """Score basé sur les indicateurs techniques"""
        score = 0
        reasons = []
        
        # RSI (max 10 points)
        rsi = indicators.get('rsi', 50)
        if 35 <= rsi <= 55:
            score += 10
            reasons.append(f"✅ RSI zone achat ({rsi:.0f}): +10")
        elif 55 < rsi < 70:
            score += 6
            reasons.append(f"✅ RSI momentum ({rsi:.0f}): +6")
        elif rsi <= 30:
            score += 8  # Oversold = opportunity
            reasons.append(f"✅ RSI survendu ({rsi:.0f}): +8")
        else:
            score += 2
            reasons.append(f"⚠️ RSI suracheté ({rsi:.0f}): +2")
        
        # MACD (max 8 points)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_hist = indicators.get('macd_hist', 0)
        
        if macd > macd_signal and macd_hist > 0:
            score += 8
            reasons.append("✅ MACD haussier: +8")
        elif macd > macd_signal:
            score += 5
            reasons.append("✅ MACD positif: +5")
        else:
            score += 2
            reasons.append("⚠️ MACD neutre: +2")
        
        # EMA Alignment (max 8 points)
        ema_9 = indicators.get('ema_9', 0)
        ema_21 = indicators.get('ema_21', 0)
        ema_55 = indicators.get('ema_55', 0)
        price = indicators.get('close', 0)
        
        if price > ema_9 > ema_21 > ema_55:
            score += 8
            reasons.append("✅ EMA alignées haussier: +8")
        elif price > ema_21 > ema_55:
            score += 5
            reasons.append("✅ EMA haussier: +5")
        elif price > ema_55:
            score += 3
            reasons.append("✅ Prix > EMA55: +3")
        else:
            score += 0
            reasons.append("❌ EMA baissier: +0")
        
        # ADX - Force de tendance (max 8 points)
        adx = indicators.get('adx', 20)
        if adx >= 40:
            score += 8
            reasons.append(f"✅ ADX très fort ({adx:.0f}): +8")
        elif adx >= 25:
            score += 6
            reasons.append(f"✅ ADX fort ({adx:.0f}): +6")
        elif adx >= 20:
            score += 4
            reasons.append(f"✅ ADX moyen ({adx:.0f}): +4")
        else:
            score += 1
            reasons.append(f"⚠️ ADX faible ({adx:.0f}): +1")
        
        # Bollinger Position (max 6 points)
        bb_pos = indicators.get('bb_position', 0.5)
        if 0.2 <= bb_pos <= 0.4:
            score += 6
            reasons.append(f"✅ BB bas ({bb_pos:.2f}): +6")
        elif 0.4 < bb_pos <= 0.6:
            score += 4
            reasons.append(f"✅ BB milieu ({bb_pos:.2f}): +4")
        elif bb_pos > 0.85:
            score += 1
            reasons.append(f"⚠️ BB haut ({bb_pos:.2f}): +1")
        else:
            score += 3
            reasons.append(f"✅ BB OK ({bb_pos:.2f}): +3")
        
        return min(40, score), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: VOLUME & MOMENTUM (15%)
    # ═══════════════════════════════════════════════════════════════
    def score_volume_momentum(self, indicators: Dict) -> Tuple[float, list]:
        """Score basé sur volume et momentum"""
        score = 0
        reasons = []
        
        # Volume ratio (max 8 points)
        vol_ratio = indicators.get('volume_ratio', 1)
        if vol_ratio >= 2:
            score += 8
            reasons.append(f"✅ Volume explosif ({vol_ratio:.1f}x): +8")
        elif vol_ratio >= 1.5:
            score += 6
            reasons.append(f"✅ Volume élevé ({vol_ratio:.1f}x): +6")
        elif vol_ratio >= 1.2:
            score += 4
            reasons.append(f"✅ Volume OK ({vol_ratio:.1f}x): +4")
        elif vol_ratio >= 0.8:
            score += 2
            reasons.append(f"⚠️ Volume moyen ({vol_ratio:.1f}x): +2")
        else:
            score += 0
            reasons.append(f"❌ Volume faible ({vol_ratio:.1f}x): +0")
        
        # Momentum / ROC (max 7 points)
        momentum = indicators.get('momentum', 0)
        if momentum > 5:
            score += 7
            reasons.append(f"✅ Momentum fort (+{momentum:.1f}%): +7")
        elif momentum > 2:
            score += 5
            reasons.append(f"✅ Momentum positif (+{momentum:.1f}%): +5")
        elif momentum > 0:
            score += 3
            reasons.append(f"✅ Momentum neutre (+{momentum:.1f}%): +3")
        else:
            score += 1
            reasons.append(f"⚠️ Momentum négatif ({momentum:.1f}%): +1")
        
        return min(15, score), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: CONFIRMATION MULTI-SOURCE (15%)
    # ═══════════════════════════════════════════════════════════════
    def score_confirmation(self, market_data: Dict, indicators: Dict) -> Tuple[float, list]:
        """Score de confirmation multi-source"""
        score = 0
        reasons = []
        confirmations = 0
        
        # 1. API + RSI alignés
        fg = market_data.get('fear_greed', {}).get('value', 50)
        rsi = indicators.get('rsi', 50)
        if (fg < 50 and rsi < 50) or (fg > 50 and rsi > 50):
            confirmations += 1
            reasons.append("✅ F&G et RSI alignés")
        
        # 2. Tendance + Volume
        adx = indicators.get('adx', 20)
        vol_ratio = indicators.get('volume_ratio', 1)
        if adx > 25 and vol_ratio > 1.2:
            confirmations += 1
            reasons.append("✅ Tendance + Volume confirmés")
        
        # 3. EMA + MACD alignés
        ema_aligned = indicators.get('close', 0) > indicators.get('ema_21', 0)
        macd_positive = indicators.get('macd_hist', 0) > 0
        if ema_aligned and macd_positive:
            confirmations += 1
            reasons.append("✅ EMA et MACD alignés")
        
        # 4. Market Cap + Prix
        mc_change = market_data.get('market', {}).get('market_cap_change_24h', 0)
        price_change = indicators.get('momentum', 0)
        if (mc_change > 0 and price_change > 0):
            confirmations += 1
            reasons.append("✅ Market Cap et Prix alignés")
        
        # 5. VIX faible + Momentum positif
        vix = market_data.get('vix', {}).get('value', 20)
        if vix < 22 and indicators.get('momentum', 0) > 0:
            confirmations += 1
            reasons.append("✅ VIX bas + Momentum positif")
        
        # Calculer score (max 15 points)
        score = confirmations * 3
        reasons.insert(0, f"📊 {confirmations}/5 confirmations")
        
        return min(15, score), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORE TOTAL UNIFIÉ
    # ═══════════════════════════════════════════════════════════════
    def calculate_unified_score(self, market_data: Dict, indicators: Dict) -> Dict:
        """
        Calcule le score unifié final
        Combine APIs + Indicateurs + Volume + Confirmations
        """
        # Calculer chaque composant
        market_score, market_reasons = self.score_market_intel(market_data)
        tech_score, tech_reasons = self.score_technical(indicators)
        volume_score, volume_reasons = self.score_volume_momentum(indicators)
        confirm_score, confirm_reasons = self.score_confirmation(market_data, indicators)
        
        # Score total
        total_score = market_score + tech_score + volume_score + confirm_score
        
        # Déterminer leverage optimal
        leverage = 0
        for (min_s, max_s), lev in self.leverage_matrix.items():
            if min_s <= total_score < max_s:
                leverage = lev
                break
        
        # Déterminer hold duration
        market_intel_raw = market_data.get('score', 50)
        hold_mult = 1.0
        for (min_s, max_s), hold in self.hold_matrix.items():
            if min_s <= market_intel_raw < max_s:
                hold_mult = hold
                break
        
        # Déterminer stop loss
        stop_loss = self.stop_matrix.get(leverage, 0.025)
        
        # Take profit basé sur hold
        take_profit = stop_loss * 3 * hold_mult  # Ratio 1:3 * hold
        
        # Décision finale
        if total_score >= self.thresholds['exceptional_trade']:
            decision = "🔥🔥🔥 TRADE EXCEPTIONNEL"
            action = "STRONG_BUY"
        elif total_score >= self.thresholds['strong_trade']:
            decision = "🔥🔥 TRADE FORT"
            action = "BUY"
        elif total_score >= self.thresholds['confident_trade']:
            decision = "🔥 TRADE CONFIANT"
            action = "BUY"
        elif total_score >= self.thresholds['min_trade']:
            decision = "✅ TRADE ACCEPTABLE"
            action = "BUY"
        else:
            decision = "❌ PAS DE TRADE"
            action = "HOLD"
        
        result = {
            'total_score': total_score,
            'decision': decision,
            'action': action,
            'components': {
                'market_intel': {'score': market_score, 'max': 30, 'reasons': market_reasons},
                'technical': {'score': tech_score, 'max': 40, 'reasons': tech_reasons},
                'volume_momentum': {'score': volume_score, 'max': 15, 'reasons': volume_reasons},
                'confirmation': {'score': confirm_score, 'max': 15, 'reasons': confirm_reasons},
            },
            'leverage': leverage,
            'hold_multiplier': hold_mult,
            'stop_loss_pct': stop_loss * 100,
            'take_profit_pct': take_profit * 100,
            'risk_reward': 3 * hold_mult,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log
        logger.info(f"🏆 SCORE UNIFIÉ: {total_score}/100")
        logger.info(f"   {decision}")
        logger.info(f"   Market Intel: {market_score}/30 | Tech: {tech_score}/40")
        logger.info(f"   Volume: {volume_score}/15 | Confirm: {confirm_score}/15")
        logger.info(f"   Leverage: {leverage}x | Hold: {hold_mult}x")
        logger.info(f"   Stop: {stop_loss*100:.1f}% | TP: {take_profit*100:.1f}%")
        
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # POSITION SIZING OPTIMAL
    # ═══════════════════════════════════════════════════════════════
    def calculate_optimal_position(self, score_result: Dict, capital: float, price: float) -> Dict:
        """Calcule la position optimale basée sur le score"""
        
        score = score_result['total_score']
        leverage = score_result['leverage']
        stop_pct = score_result['stop_loss_pct'] / 100
        
        # Risk par trade basé sur score
        if score >= 90:
            risk_pct = 0.03  # 3% si exceptionnel
        elif score >= 80:
            risk_pct = 0.02  # 2% si fort
        elif score >= 70:
            risk_pct = 0.015  # 1.5% si confiant
        else:
            risk_pct = 0.01  # 1% sinon
        
        # Capital à risquer
        risk_amount = capital * risk_pct
        
        # Taille position basée sur stop
        if stop_pct > 0:
            position_value = risk_amount / stop_pct
        else:
            position_value = risk_amount * 50
        
        # Appliquer leverage
        effective_exposure = position_value * leverage
        
        # Limiter à 50% du capital max
        max_position = capital * 0.5
        position_value = min(position_value, max_position)
        effective_exposure = min(effective_exposure, capital * leverage * 0.5)
        
        # Quantité
        qty = position_value / price if price > 0 else 0
        
        return {
            'capital': capital,
            'risk_pct': risk_pct * 100,
            'risk_amount': risk_amount,
            'position_value': position_value,
            'leverage': leverage,
            'effective_exposure': effective_exposure,
            'quantity': qty,
            'stop_loss_price': price * (1 - stop_pct),
            'take_profit_price': price * (1 + score_result['take_profit_pct'] / 100)
        }


# ═══════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════════
_optimal_strategy = None

def get_optimal_strategy() -> OptimalStrategy:
    global _optimal_strategy
    if _optimal_strategy is None:
        _optimal_strategy = OptimalStrategy()
    return _optimal_strategy


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
    
    print("🏆 TEST STRATÉGIE OPTIMALE UNIFIÉE")
    print("=" * 60)
    
    strategy = OptimalStrategy()
    
    # Simuler des données
    market_data = {
        'fear_greed': {'value': 45},
        'vix': {'value': 18},
        'market': {'market_cap_change_24h': 2.5},
        'score': 72
    }
    
    indicators = {
        'rsi': 42,
        'macd': 0.5,
        'macd_signal': 0.3,
        'macd_hist': 0.2,
        'ema_9': 100,
        'ema_21': 98,
        'ema_55': 95,
        'close': 102,
        'adx': 32,
        'bb_position': 0.35,
        'volume_ratio': 1.6,
        'momentum': 3.5
    }
    
    result = strategy.calculate_unified_score(market_data, indicators)
    
    print(f"\n📊 Résultat:")
    print(f"   Score Total: {result['total_score']}/100")
    print(f"   Décision: {result['decision']}")
    print(f"   Leverage: {result['leverage']}x")
    print(f"   Hold: {result['hold_multiplier']}x")
    
    # Test position sizing
    position = strategy.calculate_optimal_position(result, 10000, 100)
    print(f"\n💰 Position Optimale (capital $10,000):")
    print(f"   Risque: {position['risk_pct']}% = ${position['risk_amount']:.2f}")
    print(f"   Position: ${position['position_value']:.2f}")
    print(f"   Leverage {position['leverage']}x → Exposition: ${position['effective_exposure']:.2f}")

