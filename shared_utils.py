"""
🛠️ SHARED UTILITIES V2.0
========================
Fonctions utilitaires partagées entre tous les bots:
- safe_divide: Division sécurisée
- clean_series: Nettoyage des séries pandas
- safe_value: Valeur sécurisée
- clamp: Limiter une valeur
- adjust_stop_for_volatility: Stop adaptatif
- SWING_TAKE_PROFIT_LEVELS: Niveaux de take profit
"""

import pandas as pd
import numpy as np
import logging
from typing import Union, List, Dict

logger = logging.getLogger(__name__)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Division sécurisée avec protection contre:
    - Division par zéro
    - NaN
    - Inf
    """
    try:
        if denominator == 0:
            return default
        if pd.isna(denominator) or np.isinf(denominator):
            return default
        
        result = numerator / denominator
        
        if pd.isna(result) or np.isinf(result):
            return default
        
        return result
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def clean_series(series: pd.Series, default: float = 0.0) -> pd.Series:
    """
    Nettoie une série pandas:
    - Remplace inf par NaN
    - Remplace NaN par default
    """
    if series is None:
        return pd.Series([default])
    
    return series.replace([np.inf, -np.inf], np.nan).fillna(default)


def safe_value(value, default: float = 0.0) -> float:
    """
    Retourne une valeur sécurisée:
    - Si None → default
    - Si NaN → default
    - Si Inf → default
    """
    if value is None:
        return default
    
    try:
        if pd.isna(value) or np.isinf(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Limite une valeur entre min et max
    """
    return max(min_val, min(max_val, value))


def adjust_stop_for_volatility(
    base_stop_pct: float, 
    atr_pct: float, 
    min_stop: float = 0.01, 
    max_stop: float = 0.10
) -> float:
    """
    Ajuste le stop loss selon la volatilité (ATR)
    
    Args:
        base_stop_pct: Stop de base (ex: 0.03 pour 3%)
        atr_pct: ATR en pourcentage
        min_stop: Stop minimum
        max_stop: Stop maximum
    
    Returns:
        Stop ajusté
    """
    if atr_pct > 4:
        # Très volatile → stop plus large
        adjusted = base_stop_pct * 1.5
    elif atr_pct > 3:
        adjusted = base_stop_pct * 1.3
    elif atr_pct > 2:
        adjusted = base_stop_pct * 1.1
    elif atr_pct < 1:
        # Peu volatile → stop plus serré
        adjusted = base_stop_pct * 0.8
    else:
        adjusted = base_stop_pct
    
    return clamp(adjusted, min_stop, max_stop)


def check_take_profit_level(profit_pct: float, levels: List[Dict]) -> Dict:
    """
    Vérifie si un niveau de take profit est atteint
    
    Args:
        profit_pct: Profit actuel en %
        levels: Liste des niveaux [{profit_pct, sell_pct}, ...]
    
    Returns:
        Dict avec action à effectuer
    """
    for level in levels:
        if profit_pct >= level['profit_pct']:
            return {
                'reached': True,
                'level_pct': level['profit_pct'],
                'sell_pct': level['sell_pct'],
                'current_profit': profit_pct
            }
    
    return {'reached': False, 'current_profit': profit_pct}


# ═══════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════

SWING_TAKE_PROFIT_LEVELS = [
    {'profit_pct': 5, 'sell_pct': 0.25},
    {'profit_pct': 10, 'sell_pct': 0.25},
    {'profit_pct': 15, 'sell_pct': 0.25},
    {'profit_pct': 20, 'sell_pct': 1.0},
]

SCALPING_TAKE_PROFIT_LEVELS = [
    {'profit_pct': 0.5, 'sell_pct': 0.30},
    {'profit_pct': 0.8, 'sell_pct': 0.40},
    {'profit_pct': 1.2, 'sell_pct': 1.0},
]

CRYPTO_TAKE_PROFIT_LEVELS = [
    {'profit_pct': 3, 'sell_pct': 0.25},
    {'profit_pct': 5, 'sell_pct': 0.25},
    {'profit_pct': 8, 'sell_pct': 0.25},
    {'profit_pct': 12, 'sell_pct': 1.0},
]


# ═══════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════

def validate_dataframe(df: pd.DataFrame, min_rows: int = 50) -> bool:
    """Valide qu'un DataFrame est utilisable"""
    if df is None:
        return False
    if len(df) < min_rows:
        return False
    
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            return False
    
    return True


def validate_signal(signal: Dict) -> bool:
    """Valide qu'un signal est complet"""
    if signal is None:
        return False
    
    required = ['symbol', 'signal', 'entry_price', 'stop_loss']
    for key in required:
        if key not in signal:
            return False
        if signal.get('signal') == 'BUY' and signal.get(key) is None:
            return False
    
    return True


# ═══════════════════════════════════════════════════════════════════
# FORMATAGE
# ═══════════════════════════════════════════════════════════════════

def format_currency(value: float) -> str:
    """Formate un montant en dollars"""
    return f"${value:,.2f}"


def format_percent(value: float, decimals: int = 2) -> str:
    """Formate un pourcentage"""
    return f"{value:.{decimals}f}%"


def format_score(score: float, max_score: float = 100) -> str:
    """Formate un score avec emoji"""
    pct = (score / max_score) * 100
    if pct >= 85:
        emoji = "🔥🔥🔥"
    elif pct >= 70:
        emoji = "🔥🔥"
    elif pct >= 55:
        emoji = "🔥"
    elif pct >= 40:
        emoji = "✅"
    else:
        emoji = "❌"
    
    return f"{emoji} {score:.0f}/{max_score:.0f}"


if __name__ == "__main__":
    print("🛠️ Shared Utilities V2.0")
    print(f"   safe_divide(10, 0) = {safe_divide(10, 0)}")
    print(f"   clamp(150, 0, 100) = {clamp(150, 0, 100)}")
    print(f"   format_currency(1234.5) = {format_currency(1234.5)}")
