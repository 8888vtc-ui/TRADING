"""
🏆 STRATÉGIE OPTIMALE UNIFIÉE V2.0
==================================
SYSTÈME COMPLET combinant:

MARKET INTELLIGENCE (35 points):
├── Fear & Greed Index: 12 pts
├── VIX: 8 pts
├── DXY (Dollar): 5 pts
├── Market Cap 24h: 5 pts
└── Calendrier Éco: 5 pts (bonus/malus)

INDICATEURS TECHNIQUES (40 points):
├── Tendance (EMA/Ichimoku): 12 pts
├── Momentum (RSI/MACD): 10 pts
├── Support/Résistance (Fib/Pivots): 10 pts
└── Force (ADX): 8 pts

VOLUME & FLOW (15 points):
├── Volume Ratio: 5 pts
├── MFI: 5 pts
└── CMF: 5 pts

CONFIRMATIONS (10 points):
└── Multi-source alignment: 10 pts

RÉSULTAT → Score 0-100 → Leverage + Risk + Hold automatiques
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

# Imports locaux
try:
    from market_intelligence_v2 import get_market_intelligence_v2
    from advanced_indicators import calculate_all_advanced, calculate_ichimoku, calculate_fibonacci, calculate_mfi, calculate_cmf, calculate_pivot_points
except ImportError:
    logger.warning("Imports optionnels non disponibles")


def safe_divide(n, d, default=0.0):
    try:
        if d == 0 or pd.isna(d) or np.isinf(d):
            return default
        r = n / d
        return default if pd.isna(r) or np.isinf(r) else r
    except:
        return default


class OptimalStrategyV2:
    """
    🏆 STRATÉGIE OPTIMALE V2.0
    Combine APIs + Indicateurs Standards + Indicateurs Avancés + Leverage
    """
    
    def __init__(self):
        # ═══════════════════════════════════════════════════════════
        # POIDS DU SCORING V2.0
        # ═══════════════════════════════════════════════════════════
        self.weights = {
            'market_intel': 35,      # APIs informatives
            'technical': 40,          # Indicateurs techniques
            'volume_flow': 15,        # Volume & Money Flow
            'confirmation': 10,       # Confirmations multi-sources
        }
        
        # ═══════════════════════════════════════════════════════════
        # SEUILS DE DÉCISION
        # ═══════════════════════════════════════════════════════════
        self.thresholds = {
            'exceptional': 85,
            'strong': 75,
            'confident': 65,
            'acceptable': 55,
            'min_trade': 45,
        }
        
        # ═══════════════════════════════════════════════════════════
        # LEVERAGE MATRIX
        # ═══════════════════════════════════════════════════════════
        self.leverage_matrix = {
            (85, 101): 5.0,
            (75, 85): 3.0,
            (65, 75): 2.0,
            (55, 65): 1.5,
            (45, 55): 1.0,
            (0, 45): 0,
        }
        
        # ═══════════════════════════════════════════════════════════
        # STOP LOSS BY LEVERAGE
        # ═══════════════════════════════════════════════════════════
        self.stop_matrix = {
            5.0: 0.006,
            3.0: 0.01,
            2.0: 0.015,
            1.5: 0.02,
            1.0: 0.025,
        }
        
        # ═══════════════════════════════════════════════════════════
        # HOLD MULTIPLIER
        # ═══════════════════════════════════════════════════════════
        self.hold_matrix = {
            (85, 101): 2.5,
            (75, 85): 2.0,
            (65, 75): 1.5,
            (55, 65): 1.0,
            (0, 55): 0.7,
        }
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        logger.info("🏆 Stratégie Optimale V2.0 initialisée")
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: MARKET INTELLIGENCE (35 points)
    # ═══════════════════════════════════════════════════════════════
    
    def score_market_intel(self, market_data: Dict) -> Tuple[float, List[str]]:
        """Score basé sur les APIs informatives (35 points max)"""
        score = 0
        reasons = []
        
        # 1. Fear & Greed (12 points)
        fg = market_data.get('fear_greed', {}).get('value', 50)
        if 25 <= fg <= 55:
            score += 12
            reasons.append(f"✅ F&G optimal ({fg}): +12")
        elif 55 < fg <= 70:
            score += 8
            reasons.append(f"✅ F&G neutre ({fg}): +8")
        elif fg > 80:
            score += 2
            reasons.append(f"⚠️ F&G extrême cupidité ({fg}): +2")
        elif 15 < fg < 25:
            score += 10
            reasons.append(f"✅ F&G peur contrarian ({fg}): +10")
        else:
            score += 0
            reasons.append(f"❌ F&G danger ({fg}): +0")
        
        # 2. VIX (8 points)
        vix = market_data.get('vix', {}).get('value', 20)
        if vix <= 18:
            score += 8
            reasons.append(f"✅ VIX optimal ({vix}): +8")
        elif vix <= 22:
            score += 6
            reasons.append(f"✅ VIX OK ({vix}): +6")
        elif vix <= 28:
            score += 3
            reasons.append(f"⚠️ VIX élevé ({vix}): +3")
        else:
            score += 0
            reasons.append(f"❌ VIX danger ({vix}): +0")
        
        # 3. DXY (5 points)
        dxy = market_data.get('dxy', {}).get('value', 103)
        dxy_signal = market_data.get('dxy', {}).get('signal', 'NEUTRAL')
        if dxy_signal == 'BULLISH':
            score += 5
            reasons.append(f"✅ DXY faible ({dxy}): +5")
        elif dxy_signal == 'NEUTRAL':
            score += 3
            reasons.append(f"✅ DXY neutre ({dxy}): +3")
        else:
            score += 0
            reasons.append(f"⚠️ DXY fort ({dxy}): +0")
        
        # 4. Market Cap Change (5 points)
        mc_change = market_data.get('market', {}).get('market_cap_change_24h', 0)
        if mc_change > 3:
            score += 5
            reasons.append(f"✅ MC +{mc_change:.1f}%: +5")
        elif mc_change > 0:
            score += 3
            reasons.append(f"✅ MC +{mc_change:.1f}%: +3")
        elif mc_change > -3:
            score += 1
            reasons.append(f"⚠️ MC {mc_change:.1f}%: +1")
        else:
            score += 0
            reasons.append(f"❌ MC {mc_change:.1f}%: +0")
        
        # 5. Calendrier (5 points bonus/malus)
        calendar = market_data.get('calendar', {})
        if calendar.get('block_trading'):
            score -= 35  # Bloque tout
            reasons.append(f"🚫 Event éco: {calendar.get('reason')}")
        else:
            score += 5
            reasons.append("✅ Calendrier OK: +5")
        
        return max(0, min(35, score)), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: INDICATEURS TECHNIQUES (40 points)
    # ═══════════════════════════════════════════════════════════════
    
    def score_technical(self, indicators: Dict, advanced: Dict) -> Tuple[float, List[str]]:
        """Score basé sur indicateurs techniques (40 points max)"""
        score = 0
        reasons = []
        
        # 1. TENDANCE - EMA + Ichimoku (12 points)
        close = indicators.get('close', 0)
        ema_9 = indicators.get('ema_9', 0)
        ema_21 = indicators.get('ema_21', 0)
        ema_55 = indicators.get('ema_55', 0)
        
        if close > ema_9 > ema_21 > ema_55:
            score += 6
            reasons.append("✅ EMAs alignées haussier: +6")
        elif close > ema_21 > ema_55:
            score += 4
            reasons.append("✅ EMAs haussier: +4")
        elif close > ema_55:
            score += 2
            reasons.append("✅ Prix > EMA55: +2")
        
        # Ichimoku
        ichimoku = advanced.get('ichimoku', {})
        if ichimoku.get('valid'):
            ich_score = ichimoku.get('score', 5)
            if ichimoku.get('cloud_signal') == 'BULLISH':
                score += 4
                reasons.append(f"✅ Ichimoku bullish: +4")
            elif ichimoku.get('cloud_signal') == 'NEUTRAL':
                score += 2
                reasons.append(f"⚠️ Ichimoku neutre: +2")
            
            if ichimoku.get('tk_cross') == 'BULLISH':
                score += 2
                reasons.append("✅ TK cross haussier: +2")
        
        # 2. MOMENTUM - RSI + MACD (10 points)
        rsi = indicators.get('rsi', 50)
        if 30 <= rsi <= 45:
            score += 5
            reasons.append(f"✅ RSI rebond ({rsi:.0f}): +5")
        elif 45 < rsi < 60:
            score += 4
            reasons.append(f"✅ RSI momentum ({rsi:.0f}): +4")
        elif rsi < 30:
            score += 3
            reasons.append(f"✅ RSI survendu ({rsi:.0f}): +3")
        elif rsi > 70:
            score += 1
            reasons.append(f"⚠️ RSI suracheté ({rsi:.0f}): +1")
        
        macd_hist = indicators.get('macd_hist', 0)
        if macd_hist > 0:
            score += 3
            reasons.append("✅ MACD positif: +3")
        elif macd_hist > indicators.get('macd_hist_prev', -1):
            score += 2
            reasons.append("✅ MACD en hausse: +2")
        
        # 3. SUPPORT/RÉSISTANCE - Fibonacci + Pivots (10 points)
        fib = advanced.get('fibonacci', {})
        if fib.get('valid'):
            if fib.get('near_support') and fib.get('position_pct', 50) < 50:
                score += 5
                reasons.append(f"✅ Près Fib support: +5")
            elif fib.get('position_pct', 50) < 40:
                score += 3
                reasons.append(f"✅ Zone Fib basse: +3")
        
        pivots = advanced.get('pivots', {})
        if pivots.get('valid'):
            position = pivots.get('position', '')
            if 'S1' in position or 'S2' in position:
                score += 5
                reasons.append(f"✅ Sur support pivot: +5")
            elif position == 'ABOVE_PIVOT':
                score += 3
                reasons.append("✅ Au-dessus pivot: +3")
        
        # 4. FORCE - ADX (8 points)
        adx = indicators.get('adx', 20)
        if adx >= 35:
            score += 8
            reasons.append(f"✅ ADX très fort ({adx:.0f}): +8")
        elif adx >= 25:
            score += 6
            reasons.append(f"✅ ADX fort ({adx:.0f}): +6")
        elif adx >= 20:
            score += 4
            reasons.append(f"✅ ADX moyen ({adx:.0f}): +4")
        
        return max(0, min(40, score)), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: VOLUME & FLOW (15 points)
    # ═══════════════════════════════════════════════════════════════
    
    def score_volume_flow(self, indicators: Dict, advanced: Dict) -> Tuple[float, List[str]]:
        """Score basé sur volume et money flow (15 points max)"""
        score = 0
        reasons = []
        
        # 1. Volume Ratio (5 points)
        vol_ratio = indicators.get('volume_ratio', 1)
        if vol_ratio >= 2:
            score += 5
            reasons.append(f"✅ Volume explosif ({vol_ratio:.1f}x): +5")
        elif vol_ratio >= 1.5:
            score += 4
            reasons.append(f"✅ Volume élevé ({vol_ratio:.1f}x): +4")
        elif vol_ratio >= 1.2:
            score += 3
            reasons.append(f"✅ Volume OK ({vol_ratio:.1f}x): +3")
        elif vol_ratio >= 0.8:
            score += 1
            reasons.append(f"⚠️ Volume faible ({vol_ratio:.1f}x): +1")
        
        # 2. MFI (5 points)
        mfi = advanced.get('mfi', {})
        if mfi.get('valid'):
            mfi_val = mfi.get('value', 50)
            if 20 <= mfi_val <= 40:
                score += 5
                reasons.append(f"✅ MFI rebond ({mfi_val:.0f}): +5")
            elif mfi_val < 20:
                score += 4
                reasons.append(f"✅ MFI survendu ({mfi_val:.0f}): +4")
            elif 40 < mfi_val < 60:
                score += 3
                reasons.append(f"✅ MFI neutre ({mfi_val:.0f}): +3")
            elif mfi_val > 80:
                score += 1
                reasons.append(f"⚠️ MFI suracheté ({mfi_val:.0f}): +1")
        
        # 3. CMF (5 points)
        cmf = advanced.get('cmf', {})
        if cmf.get('valid'):
            cmf_val = cmf.get('value', 0)
            if cmf_val > 0.2:
                score += 5
                reasons.append(f"✅ CMF très positif ({cmf_val:.2f}): +5")
            elif cmf_val > 0.1:
                score += 4
                reasons.append(f"✅ CMF positif ({cmf_val:.2f}): +4")
            elif cmf_val > 0:
                score += 3
                reasons.append(f"✅ CMF OK ({cmf_val:.2f}): +3")
            elif cmf_val > -0.1:
                score += 1
                reasons.append(f"⚠️ CMF léger négatif ({cmf_val:.2f}): +1")
        
        return max(0, min(15, score)), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORING: CONFIRMATIONS (10 points)
    # ═══════════════════════════════════════════════════════════════
    
    def score_confirmations(self, market_data: Dict, indicators: Dict, advanced: Dict) -> Tuple[float, List[str]]:
        """Score de confirmation multi-source (10 points max)"""
        score = 0
        reasons = []
        confirmations = 0
        
        # 1. API + Technique alignés
        fg = market_data.get('fear_greed', {}).get('value', 50)
        rsi = indicators.get('rsi', 50)
        if (fg < 50 and rsi < 50) or (fg > 50 and rsi > 50):
            confirmations += 1
            reasons.append("✅ F&G et RSI alignés")
        
        # 2. Ichimoku + EMA
        ichimoku = advanced.get('ichimoku', {})
        if ichimoku.get('cloud_signal') == 'BULLISH' and indicators.get('close', 0) > indicators.get('ema_21', 0):
            confirmations += 1
            reasons.append("✅ Ichimoku + EMA alignés")
        
        # 3. Volume + Momentum
        if indicators.get('volume_ratio', 1) > 1.2 and indicators.get('adx', 20) > 25:
            confirmations += 1
            reasons.append("✅ Volume + ADX confirmés")
        
        # 4. MFI + CMF alignés
        mfi = advanced.get('mfi', {})
        cmf = advanced.get('cmf', {})
        if mfi.get('valid') and cmf.get('valid'):
            if mfi.get('value', 50) < 60 and cmf.get('value', 0) > 0:
                confirmations += 1
                reasons.append("✅ MFI + CMF alignés")
        
        # 5. Support multiple (Fib + Pivot)
        fib = advanced.get('fibonacci', {})
        pivots = advanced.get('pivots', {})
        if fib.get('near_support') or 'S' in pivots.get('position', ''):
            confirmations += 1
            reasons.append("✅ Support confirmé (Fib/Pivot)")
        
        score = confirmations * 2  # 2 points par confirmation
        reasons.insert(0, f"📊 {confirmations}/5 confirmations")
        
        return max(0, min(10, score)), reasons
    
    # ═══════════════════════════════════════════════════════════════
    # SCORE TOTAL UNIFIÉ V2.0
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_unified_score(self, market_data: Dict, indicators: Dict, df: pd.DataFrame = None) -> Dict:
        """
        Calcule le score unifié V2.0 (0-100)
        Combine: APIs + Indicateurs + Avancés + Confirmations
        """
        start = time.time()
        
        # Calculer indicateurs avancés si df fourni
        advanced = {}
        if df is not None and len(df) > 50:
            try:
                advanced = calculate_all_advanced(df)
            except:
                advanced = {}
        
        # Calculer chaque composant
        market_score, market_reasons = self.score_market_intel(market_data)
        tech_score, tech_reasons = self.score_technical(indicators, advanced)
        volume_score, volume_reasons = self.score_volume_flow(indicators, advanced)
        confirm_score, confirm_reasons = self.score_confirmations(market_data, indicators, advanced)
        
        # Score total
        total_score = market_score + tech_score + volume_score + confirm_score
        total_score = max(0, min(100, total_score))
        
        # Déterminer leverage
        leverage = 0
        for (min_s, max_s), lev in self.leverage_matrix.items():
            if min_s <= total_score < max_s:
                leverage = lev
                break
        
        # Déterminer hold multiplier
        hold_mult = 1.0
        for (min_s, max_s), hold in self.hold_matrix.items():
            if min_s <= total_score < max_s:
                hold_mult = hold
                break
        
        # Stop loss
        stop_loss = self.stop_matrix.get(leverage, 0.025)
        
        # Take profit (ratio 1:3 × hold)
        take_profit = stop_loss * 3 * hold_mult
        
        # Décision
        if total_score >= self.thresholds['exceptional']:
            decision = "🔥🔥🔥 TRADE EXCEPTIONNEL"
            action = "STRONG_BUY"
        elif total_score >= self.thresholds['strong']:
            decision = "🔥🔥 TRADE FORT"
            action = "BUY"
        elif total_score >= self.thresholds['confident']:
            decision = "🔥 TRADE CONFIANT"
            action = "BUY"
        elif total_score >= self.thresholds['acceptable']:
            decision = "✅ TRADE ACCEPTABLE"
            action = "BUY"
        elif total_score >= self.thresholds['min_trade']:
            decision = "⚠️ TRADE PRUDENT"
            action = "BUY"
        else:
            decision = "❌ PAS DE TRADE"
            action = "HOLD"
        
        elapsed = time.time() - start
        
        result = {
            'total_score': total_score,
            'decision': decision,
            'action': action,
            'components': {
                'market_intel': {'score': market_score, 'max': 35, 'reasons': market_reasons},
                'technical': {'score': tech_score, 'max': 40, 'reasons': tech_reasons},
                'volume_flow': {'score': volume_score, 'max': 15, 'reasons': volume_reasons},
                'confirmation': {'score': confirm_score, 'max': 10, 'reasons': confirm_reasons},
            },
            'leverage': leverage,
            'hold_multiplier': hold_mult,
            'stop_loss_pct': stop_loss * 100,
            'take_profit_pct': take_profit * 100,
            'risk_reward': 3 * hold_mult,
            'advanced_indicators': advanced.get('combined', {}),
            'calculation_time_ms': elapsed * 1000,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log
        logger.info(f"\n🏆 SCORE UNIFIÉ V2.0: {total_score}/100")
        logger.info(f"   {decision}")
        logger.info(f"   Market: {market_score}/35 | Tech: {tech_score}/40")
        logger.info(f"   Volume: {volume_score}/15 | Confirm: {confirm_score}/10")
        logger.info(f"   Leverage: {leverage}x | Hold: {hold_mult}x")
        logger.info(f"   Stop: {stop_loss*100:.1f}% | TP: {take_profit*100:.1f}%")
        logger.info(f"   ⚡ Calculé en {elapsed*1000:.0f}ms")
        
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # POSITION SIZING
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_optimal_position(self, score_result: Dict, capital: float, price: float) -> Dict:
        """Calcule la position optimale"""
        score = score_result['total_score']
        leverage = score_result['leverage']
        stop_pct = score_result['stop_loss_pct'] / 100
        
        # Risk par trade
        if score >= 85:
            risk_pct = 0.03
        elif score >= 75:
            risk_pct = 0.025
        elif score >= 65:
            risk_pct = 0.02
        elif score >= 55:
            risk_pct = 0.015
        else:
            risk_pct = 0.01
        
        risk_amount = capital * risk_pct
        
        if stop_pct > 0:
            position_value = risk_amount / stop_pct
        else:
            position_value = risk_amount * 50
        
        # Appliquer leverage
        effective_exposure = position_value * leverage
        
        # Limiter à 50% capital
        max_position = capital * 0.5
        position_value = min(position_value, max_position)
        effective_exposure = min(effective_exposure, capital * leverage * 0.5)
        
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
_optimal_v2 = None

def get_optimal_strategy_v2() -> OptimalStrategyV2:
    global _optimal_v2
    if _optimal_v2 is None:
        _optimal_v2 = OptimalStrategyV2()
    return _optimal_v2


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
    
    print("\n🏆 TEST STRATÉGIE OPTIMALE V2.0")
    print("=" * 60)
    
    strategy = OptimalStrategyV2()
    
    # Données simulées
    market_data = {
        'fear_greed': {'value': 42},
        'vix': {'value': 17},
        'dxy': {'value': 102, 'signal': 'BULLISH'},
        'market': {'market_cap_change_24h': 2.5},
        'calendar': {'block_trading': False}
    }
    
    indicators = {
        'close': 100,
        'ema_9': 99,
        'ema_21': 97,
        'ema_55': 94,
        'rsi': 38,
        'macd_hist': 0.5,
        'macd_hist_prev': 0.3,
        'adx': 28,
        'volume_ratio': 1.6,
    }
    
    result = strategy.calculate_unified_score(market_data, indicators)
    
    print(f"\n📊 Résultat Final:")
    print(f"   Score: {result['total_score']}/100")
    print(f"   {result['decision']}")
    print(f"   Leverage: {result['leverage']}x")
    print(f"   Hold: {result['hold_multiplier']}x")

