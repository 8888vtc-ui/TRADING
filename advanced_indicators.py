"""
📊 INDICATEURS TECHNIQUES AVANCÉS V1.0
=====================================
Nouveaux indicateurs pour améliorer le scoring:
- Ichimoku Cloud (Support/Résistance dynamiques)
- Fibonacci Retracements (Zones de rebond)
- MFI - Money Flow Index (RSI pondéré volume)
- CMF - Chaikin Money Flow (Pression institutionnel)
- Pivot Points (Support/Résistance classiques)
- VWAP Bands (Zones de valeur intraday)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


def safe_divide(n, d, default=0.0):
    """Division sécurisée"""
    try:
        if d == 0 or pd.isna(d) or np.isinf(d):
            return default
        r = n / d
        return default if pd.isna(r) or np.isinf(r) else r
    except:
        return default


def clean_series(s, default=0.0):
    """Nettoie une série"""
    return s.replace([np.inf, -np.inf], np.nan).fillna(default)


# ═══════════════════════════════════════════════════════════════════
# 1. ICHIMOKU CLOUD
# ═══════════════════════════════════════════════════════════════════

def calculate_ichimoku(df: pd.DataFrame) -> Dict:
    """
    Ichimoku Cloud - Support/Résistance dynamiques
    
    Composants:
    - Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    - Kijun-sen (Base Line): (26-period high + 26-period low) / 2
    - Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, décalé 26 périodes
    - Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, décalé 26 périodes
    - Chikou Span (Lagging Span): Close décalé 26 périodes en arrière
    
    Signaux:
    - Prix au-dessus du cloud = haussier
    - Prix dans le cloud = consolidation
    - Prix sous le cloud = baissier
    - Tenkan > Kijun = bullish
    - Kumo twist = changement de tendance
    """
    if len(df) < 52:
        return {'valid': False, 'signal': 'NEUTRAL', 'cloud_signal': 'NEUTRAL'}
    
    try:
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Tenkan-sen (9 périodes)
        nine_high = high.rolling(9).max()
        nine_low = low.rolling(9).min()
        tenkan = (nine_high + nine_low) / 2
        
        # Kijun-sen (26 périodes)
        twenty_six_high = high.rolling(26).max()
        twenty_six_low = low.rolling(26).min()
        kijun = (twenty_six_high + twenty_six_low) / 2
        
        # Senkou Span A (moyenne Tenkan/Kijun, décalé 26)
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        
        # Senkou Span B (52 périodes, décalé 26)
        fifty_two_high = high.rolling(52).max()
        fifty_two_low = low.rolling(52).min()
        senkou_b = ((fifty_two_high + fifty_two_low) / 2).shift(26)
        
        # Chikou Span (close décalé -26)
        chikou = close.shift(-26)
        
        # Valeurs actuelles
        current_close = close.iloc[-1]
        current_tenkan = tenkan.iloc[-1]
        current_kijun = kijun.iloc[-1]
        current_senkou_a = senkou_a.iloc[-1] if not pd.isna(senkou_a.iloc[-1]) else current_close
        current_senkou_b = senkou_b.iloc[-1] if not pd.isna(senkou_b.iloc[-1]) else current_close
        
        # Cloud (Kumo) bounds
        cloud_top = max(current_senkou_a, current_senkou_b)
        cloud_bottom = min(current_senkou_a, current_senkou_b)
        
        # Signals
        if current_close > cloud_top:
            cloud_signal = 'BULLISH'
            position = 'ABOVE_CLOUD'
        elif current_close < cloud_bottom:
            cloud_signal = 'BEARISH'
            position = 'BELOW_CLOUD'
        else:
            cloud_signal = 'NEUTRAL'
            position = 'IN_CLOUD'
        
        # TK Cross
        tk_cross = 'BULLISH' if current_tenkan > current_kijun else 'BEARISH' if current_tenkan < current_kijun else 'NEUTRAL'
        
        # Kumo twist (future)
        future_a = ((tenkan.iloc[-1] + kijun.iloc[-1]) / 2) if len(df) > 0 else current_senkou_a
        future_b = ((fifty_two_high.iloc[-1] + fifty_two_low.iloc[-1]) / 2) if len(df) > 0 else current_senkou_b
        kumo_twist = future_a > future_b  # True = bullish future cloud
        
        # Score Ichimoku (0-10)
        score = 5  # Base
        if cloud_signal == 'BULLISH':
            score += 2
        elif cloud_signal == 'BEARISH':
            score -= 2
        
        if tk_cross == 'BULLISH':
            score += 1.5
        elif tk_cross == 'BEARISH':
            score -= 1.5
        
        if kumo_twist:
            score += 1
        else:
            score -= 0.5
        
        # Chikou confirmation
        chikou_26 = chikou.iloc[-27] if len(chikou) > 27 and not pd.isna(chikou.iloc[-27]) else current_close
        if chikou_26 > close.iloc[-27] if len(close) > 27 else False:
            score += 0.5
        
        score = max(0, min(10, score))
        
        return {
            'valid': True,
            'tenkan': current_tenkan,
            'kijun': current_kijun,
            'senkou_a': current_senkou_a,
            'senkou_b': current_senkou_b,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'cloud_signal': cloud_signal,
            'position': position,
            'tk_cross': tk_cross,
            'kumo_twist': kumo_twist,
            'score': score,
            'signal': cloud_signal
        }
        
    except Exception as e:
        logger.error(f"Ichimoku error: {e}")
        return {'valid': False, 'signal': 'NEUTRAL', 'score': 5}


# ═══════════════════════════════════════════════════════════════════
# 2. FIBONACCI RETRACEMENTS
# ═══════════════════════════════════════════════════════════════════

def calculate_fibonacci(df: pd.DataFrame, lookback: int = 50) -> Dict:
    """
    Fibonacci Retracements
    
    Niveaux clés:
    - 0.236 (23.6%)
    - 0.382 (38.2%) - Support fort
    - 0.500 (50%) - Niveau psychologique
    - 0.618 (61.8%) - Golden ratio
    - 0.786 (78.6%)
    
    Signal: Prix près d'un niveau = zone de rebond potentielle
    """
    if len(df) < lookback:
        return {'valid': False, 'signal': 'NEUTRAL'}
    
    try:
        high = df['high'].iloc[-lookback:].max()
        low = df['low'].iloc[-lookback:].min()
        diff = high - low
        current = df['close'].iloc[-1]
        
        # Niveaux Fibonacci (retracement baissier)
        levels = {
            'fib_0': high,
            'fib_236': high - diff * 0.236,
            'fib_382': high - diff * 0.382,
            'fib_500': high - diff * 0.500,
            'fib_618': high - diff * 0.618,
            'fib_786': high - diff * 0.786,
            'fib_100': low,
        }
        
        # Trouver le niveau le plus proche
        closest_level = None
        min_distance = float('inf')
        
        for name, level in levels.items():
            distance = abs(current - level)
            if distance < min_distance:
                min_distance = distance
                closest_level = name
        
        # Distance en pourcentage du range
        distance_pct = safe_divide(min_distance, diff, 0.5) * 100
        
        # Signal
        near_support = distance_pct < 5  # Moins de 5% d'un niveau
        
        # Position relative
        position_pct = safe_divide(current - low, diff, 0.5) * 100
        
        # Score (0-10)
        score = 5
        if near_support and position_pct < 40:  # Près d'un support bas
            score += 2
        elif position_pct < 30:
            score += 1
        elif position_pct > 80:
            score -= 1.5
        
        if closest_level in ['fib_618', 'fib_500', 'fib_382'] and near_support:
            score += 1.5  # Golden levels
        
        score = max(0, min(10, score))
        
        return {
            'valid': True,
            'levels': levels,
            'current': current,
            'high': high,
            'low': low,
            'closest_level': closest_level,
            'distance_pct': distance_pct,
            'position_pct': position_pct,
            'near_support': near_support,
            'score': score,
            'signal': 'BULLISH' if near_support and position_pct < 50 else 'NEUTRAL'
        }
        
    except Exception as e:
        logger.error(f"Fibonacci error: {e}")
        return {'valid': False, 'signal': 'NEUTRAL', 'score': 5}


# ═══════════════════════════════════════════════════════════════════
# 3. MFI - MONEY FLOW INDEX
# ═══════════════════════════════════════════════════════════════════

def calculate_mfi(df: pd.DataFrame, period: int = 14) -> Dict:
    """
    Money Flow Index - RSI pondéré par volume
    
    Formule:
    - Typical Price = (High + Low + Close) / 3
    - Money Flow = Typical Price × Volume
    - Positive/Negative Money Flow selon direction TP
    - MFI = 100 - (100 / (1 + Money Ratio))
    
    Signaux:
    - < 20: Survendu (achat)
    - > 80: Suracheté (vente)
    - Divergences avec le prix
    """
    if len(df) < period + 1:
        return {'valid': False, 'value': 50, 'signal': 'NEUTRAL'}
    
    try:
        # Typical Price
        tp = (df['high'] + df['low'] + df['close']) / 3
        
        # Money Flow
        mf = tp * df['volume']
        
        # Positive/Negative
        tp_change = tp.diff()
        positive_mf = mf.where(tp_change > 0, 0)
        negative_mf = mf.where(tp_change < 0, 0)
        
        # Sum over period
        positive_sum = positive_mf.rolling(period).sum()
        negative_sum = abs(negative_mf.rolling(period).sum())
        
        # MFI
        mfi_values = []
        for i in range(len(df)):
            if i < period:
                mfi_values.append(50)
            else:
                ratio = safe_divide(positive_sum.iloc[i], negative_sum.iloc[i], 1)
                mfi = 100 - (100 / (1 + ratio))
                mfi_values.append(mfi)
        
        df_mfi = pd.Series(mfi_values, index=df.index)
        current_mfi = df_mfi.iloc[-1]
        prev_mfi = df_mfi.iloc[-2] if len(df_mfi) > 1 else current_mfi
        
        # Signal
        if current_mfi < 20:
            signal = 'OVERSOLD'
        elif current_mfi > 80:
            signal = 'OVERBOUGHT'
        elif current_mfi > prev_mfi and current_mfi < 60:
            signal = 'BULLISH'
        elif current_mfi < prev_mfi and current_mfi > 40:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        # Score (0-10)
        score = 5
        if 20 <= current_mfi <= 40:
            score += 2
        elif current_mfi < 20:
            score += 1.5  # Oversold = opportunity
        elif 40 < current_mfi < 60:
            score += 0.5
        elif current_mfi > 80:
            score -= 2
        elif current_mfi > 70:
            score -= 1
        
        # Momentum
        if current_mfi > prev_mfi:
            score += 0.5
        
        score = max(0, min(10, score))
        
        return {
            'valid': True,
            'value': round(current_mfi, 2),
            'prev_value': round(prev_mfi, 2),
            'signal': signal,
            'score': score
        }
        
    except Exception as e:
        logger.error(f"MFI error: {e}")
        return {'valid': False, 'value': 50, 'signal': 'NEUTRAL', 'score': 5}


# ═══════════════════════════════════════════════════════════════════
# 4. CMF - CHAIKIN MONEY FLOW
# ═══════════════════════════════════════════════════════════════════

def calculate_cmf(df: pd.DataFrame, period: int = 20) -> Dict:
    """
    Chaikin Money Flow - Pression achat/vente institutionnel
    
    Formule:
    - Money Flow Multiplier = ((Close - Low) - (High - Close)) / (High - Low)
    - Money Flow Volume = MFM × Volume
    - CMF = Sum(MFV, period) / Sum(Volume, period)
    
    Signaux:
    - > 0: Pression acheteuse
    - < 0: Pression vendeuse
    - > 0.25: Très bullish
    - < -0.25: Très bearish
    """
    if len(df) < period:
        return {'valid': False, 'value': 0, 'signal': 'NEUTRAL'}
    
    try:
        high = df['high']
        low = df['low']
        close = df['close']
        volume = df['volume']
        
        # Money Flow Multiplier (VECTORISÉ - protection div/0)
        hl_range = high - low
        mfm = np.where(
            (hl_range != 0) & (~hl_range.isna()),
            ((close - low) - (high - close)) / hl_range,
            0
        )
        mfm = pd.Series(mfm, index=df.index)
        
        # Money Flow Volume
        mfv = mfm * volume
        
        # CMF (rolling sum - plus efficace)
        sum_mfv = mfv.rolling(window=period).sum()
        sum_vol = volume.rolling(window=period).sum()
        
        df_cmf = np.where(
            (sum_vol != 0) & (~sum_vol.isna()),
            sum_mfv / sum_vol,
            0
        )
        df_cmf = pd.Series(df_cmf, index=df.index).fillna(0)
        current_cmf = df_cmf.iloc[-1]
        prev_cmf = df_cmf.iloc[-2] if len(df_cmf) > 1 else current_cmf
        
        # Signal
        if current_cmf > 0.25:
            signal = 'VERY_BULLISH'
        elif current_cmf > 0.1:
            signal = 'BULLISH'
        elif current_cmf < -0.25:
            signal = 'VERY_BEARISH'
        elif current_cmf < -0.1:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        # Score (0-10)
        score = 5
        if current_cmf > 0.25:
            score += 2.5
        elif current_cmf > 0.1:
            score += 1.5
        elif current_cmf > 0:
            score += 0.5
        elif current_cmf < -0.25:
            score -= 2
        elif current_cmf < -0.1:
            score -= 1
        
        # Momentum
        if current_cmf > prev_cmf:
            score += 0.5
        
        score = max(0, min(10, score))
        
        return {
            'valid': True,
            'value': round(current_cmf, 4),
            'prev_value': round(prev_cmf, 4),
            'signal': signal,
            'score': score
        }
        
    except Exception as e:
        logger.error(f"CMF error: {e}")
        return {'valid': False, 'value': 0, 'signal': 'NEUTRAL', 'score': 5}


# ═══════════════════════════════════════════════════════════════════
# 5. PIVOT POINTS
# ═══════════════════════════════════════════════════════════════════

def calculate_pivot_points(df: pd.DataFrame) -> Dict:
    """
    Pivot Points - Support/Résistance classiques
    
    Standard Pivot:
    - Pivot = (High + Low + Close) / 3
    - R1 = (2 × Pivot) - Low
    - S1 = (2 × Pivot) - High
    - R2 = Pivot + (High - Low)
    - S2 = Pivot - (High - Low)
    """
    if len(df) < 2:
        return {'valid': False, 'signal': 'NEUTRAL'}
    
    try:
        # Utiliser la bougie précédente pour calculer les pivots
        prev = df.iloc[-2]
        current_close = df['close'].iloc[-1]
        
        high = prev['high']
        low = prev['low']
        close = prev['close']
        
        # Pivot Point
        pivot = (high + low + close) / 3
        
        # Résistances
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        # Supports
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        # Position actuelle
        if current_close > r2:
            position = 'ABOVE_R2'
            signal = 'OVERBOUGHT'
        elif current_close > r1:
            position = 'ABOVE_R1'
            signal = 'BULLISH'
        elif current_close > pivot:
            position = 'ABOVE_PIVOT'
            signal = 'BULLISH'
        elif current_close > s1:
            position = 'ABOVE_S1'
            signal = 'NEUTRAL'
        elif current_close > s2:
            position = 'ABOVE_S2'
            signal = 'BEARISH'
        else:
            position = 'BELOW_S2'
            signal = 'OVERSOLD'
        
        # Distance au pivot le plus proche (%)
        levels = [('S3', s3), ('S2', s2), ('S1', s1), ('P', pivot), ('R1', r1), ('R2', r2), ('R3', r3)]
        closest = min(levels, key=lambda x: abs(current_close - x[1]))
        distance_pct = safe_divide(current_close - closest[1], closest[1], 0) * 100
        
        # Score (0-10)
        score = 5
        if position == 'ABOVE_S1':
            score += 1  # Bon support
        elif position == 'ABOVE_S2':
            score += 2  # Survente
        elif position == 'BELOW_S2':
            score += 1.5  # Très survendu
        elif position == 'ABOVE_R2':
            score -= 1.5  # Suracheté
        
        score = max(0, min(10, score))
        
        return {
            'valid': True,
            'pivot': round(pivot, 2),
            'r1': round(r1, 2),
            'r2': round(r2, 2),
            'r3': round(r3, 2),
            's1': round(s1, 2),
            's2': round(s2, 2),
            's3': round(s3, 2),
            'current': current_close,
            'position': position,
            'closest_level': closest[0],
            'distance_pct': round(distance_pct, 2),
            'signal': signal,
            'score': score
        }
        
    except Exception as e:
        logger.error(f"Pivot error: {e}")
        return {'valid': False, 'signal': 'NEUTRAL', 'score': 5}


# ═══════════════════════════════════════════════════════════════════
# ALL ADVANCED INDICATORS
# ═══════════════════════════════════════════════════════════════════

def calculate_all_advanced(df: pd.DataFrame) -> Dict:
    """
    Calcule TOUS les indicateurs avancés
    Retourne un score combiné et tous les détails
    """
    results = {
        'ichimoku': calculate_ichimoku(df),
        'fibonacci': calculate_fibonacci(df),
        'mfi': calculate_mfi(df),
        'cmf': calculate_cmf(df),
        'pivots': calculate_pivot_points(df),
    }
    
    # Score combiné (moyenne pondérée)
    weights = {
        'ichimoku': 0.25,
        'fibonacci': 0.20,
        'mfi': 0.20,
        'cmf': 0.20,
        'pivots': 0.15,
    }
    
    total_score = 0
    total_weight = 0
    
    for key, weight in weights.items():
        if results[key].get('valid', False):
            total_score += results[key].get('score', 5) * weight
            total_weight += weight
    
    if total_weight > 0:
        combined_score = total_score / total_weight
    else:
        combined_score = 5
    
    # Signal combiné
    signals = [r.get('signal', 'NEUTRAL') for r in results.values() if r.get('valid')]
    bullish = sum(1 for s in signals if 'BULLISH' in s)
    bearish = sum(1 for s in signals if 'BEARISH' in s)
    
    if bullish >= 3:
        combined_signal = 'BULLISH'
    elif bearish >= 3:
        combined_signal = 'BEARISH'
    elif bullish > bearish:
        combined_signal = 'SLIGHTLY_BULLISH'
    elif bearish > bullish:
        combined_signal = 'SLIGHTLY_BEARISH'
    else:
        combined_signal = 'NEUTRAL'
    
    results['combined'] = {
        'score': round(combined_score, 2),
        'signal': combined_signal,
        'bullish_count': bullish,
        'bearish_count': bearish,
    }
    
    logger.info(f"📊 Indicateurs avancés: Score {combined_score:.1f}/10 | {combined_signal}")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("📊 Module Indicateurs Avancés V1.0")
    print("   Ichimoku, Fibonacci, MFI, CMF, Pivot Points")

