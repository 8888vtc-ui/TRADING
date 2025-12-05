"""
🔧 UTILITAIRES PARTAGÉS - BOTS TRADING
======================================
Module commun pour les deux bots (Swing et Scalping)

FONCTIONNALITÉS:
- Protection division par zéro
- Filtres pré-trade (spread, liquidité, gaps)
- Gestion des erreurs
- Constantes partagées
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import pytz

logger = logging.getLogger(__name__)

NY_TZ = pytz.timezone('America/New_York')
PARIS_TZ = pytz.timezone('Europe/Paris')


# ═══════════════════════════════════════════════════════════════════════════════
# PROTECTION MATHÉMATIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def safe_divide(numerator, denominator, default=0.0):
    """
    Division sécurisée - Protection contre division par zéro
    
    Args:
        numerator: Numérateur (peut être Series, float, int)
        denominator: Dénominateur (peut être Series, float, int)
        default: Valeur par défaut si division impossible
    
    Returns:
        Résultat de la division ou valeur par défaut
    """
    if isinstance(denominator, pd.Series):
        # Remplacer les 0 par NaN, puis diviser, puis remplir avec default
        safe_denom = denominator.replace(0, np.nan)
        result = numerator / safe_denom
        return result.fillna(default)
    
    elif isinstance(numerator, pd.Series):
        if denominator == 0 or (isinstance(denominator, float) and (np.isnan(denominator) or np.isinf(denominator))):
            return pd.Series([default] * len(numerator), index=numerator.index)
        return numerator / denominator
    
    else:
        try:
            if denominator == 0:
                return default
            if isinstance(denominator, float) and (np.isnan(denominator) or np.isinf(denominator)):
                return default
            result = numerator / denominator
            if np.isnan(result) or np.isinf(result):
                return default
            return result
        except (ZeroDivisionError, TypeError, ValueError):
            return default


def clean_series(series: pd.Series, default=0.0) -> pd.Series:
    """
    Nettoie une série pandas des valeurs NaN et Inf
    
    Args:
        series: Série pandas à nettoyer
        default: Valeur de remplacement
    
    Returns:
        Série nettoyée
    """
    if series is None:
        return pd.Series([default])
    series = series.replace([np.inf, -np.inf], np.nan)
    return series.fillna(default)


def safe_value(val, default=0.0):
    """
    Retourne une valeur sûre (pas NaN, pas Inf)
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        if np.isnan(val) or np.isinf(val):
            return default
    return val


def clamp(value, min_val, max_val):
    """Limite une valeur entre min et max"""
    return max(min_val, min(max_val, value))


# ═══════════════════════════════════════════════════════════════════════════════
# FILTRES PRÉ-TRADE
# ═══════════════════════════════════════════════════════════════════════════════

def check_spread(api, symbol: str, max_spread_pct: float = 0.15) -> Tuple[bool, float]:
    """
    Vérifie si le spread est acceptable pour trader
    
    Args:
        api: API Alpaca
        symbol: Symbole à vérifier
        max_spread_pct: Spread maximum accepté (%)
    
    Returns:
        Tuple: (is_ok, spread_pct)
    """
    try:
        quote = api.get_latest_quote(symbol)
        bid = float(quote.bid_price) if quote.bid_price else 0
        ask = float(quote.ask_price) if quote.ask_price else 0
        
        if bid <= 0 or ask <= 0:
            return False, 999
        
        spread_pct = safe_divide(ask - bid, bid, 999) * 100
        
        return spread_pct <= max_spread_pct, spread_pct
        
    except Exception as e:
        logger.warning(f"Erreur vérification spread {symbol}: {e}")
        return False, 999


def check_liquidity(api, symbol: str, min_avg_volume: int = 100000, 
                   timeframe: str = '1Min', bars: int = 20) -> Tuple[bool, float]:
    """
    Vérifie si la liquidité est suffisante
    
    Args:
        api: API Alpaca
        symbol: Symbole à vérifier
        min_avg_volume: Volume moyen minimum requis
        timeframe: Timeframe pour le calcul
        bars: Nombre de barres à analyser
    
    Returns:
        Tuple: (is_ok, avg_volume)
    """
    try:
        data = api.get_bars(symbol, timeframe, limit=bars).df
        
        if data.empty:
            return False, 0
        
        avg_volume = data['volume'].mean()
        
        return avg_volume >= min_avg_volume, avg_volume
        
    except Exception as e:
        logger.warning(f"Erreur vérification liquidité {symbol}: {e}")
        return False, 0


def check_premarket_gap(api, symbol: str, max_gap_pct: float = 3.0) -> Tuple[bool, float, str]:
    """
    Vérifie le gap pré-market (pour swing trading)
    
    Args:
        api: API Alpaca
        symbol: Symbole à vérifier
        max_gap_pct: Gap maximum accepté (%)
    
    Returns:
        Tuple: (is_ok, gap_pct, direction)
    """
    try:
        # Prix de fermeture hier
        bars = api.get_bars(symbol, '1Day', limit=2).df
        
        if len(bars) < 2:
            return True, 0, "N/A"
        
        prev_close = bars['close'].iloc[-2]
        
        # Prix actuel
        quote = api.get_latest_quote(symbol)
        current = float(quote.ask_price) if quote.ask_price else prev_close
        
        gap_pct = safe_divide(current - prev_close, prev_close, 0) * 100
        direction = "UP" if gap_pct > 0 else "DOWN"
        
        return abs(gap_pct) <= max_gap_pct, gap_pct, direction
        
    except Exception as e:
        logger.warning(f"Erreur vérification gap {symbol}: {e}")
        return True, 0, "N/A"


def is_market_open(api) -> bool:
    """Vérifie si le marché est ouvert"""
    try:
        clock = api.get_clock()
        return clock.is_open
    except:
        return False


def get_market_hours(api) -> Dict:
    """Retourne les horaires du marché"""
    try:
        clock = api.get_clock()
        return {
            'is_open': clock.is_open,
            'next_open': clock.next_open,
            'next_close': clock.next_close
        }
    except Exception as e:
        logger.error(f"Erreur horaires marché: {e}")
        return {'is_open': False}


# ═══════════════════════════════════════════════════════════════════════════════
# DIVERSIFICATION SECTORIELLE
# ═══════════════════════════════════════════════════════════════════════════════

# Symboles diversifiés par secteur
SYMBOLS_BY_SECTOR = {
    'tech': ['AAPL', 'MSFT', 'NVDA', 'GOOGL'],
    'etf': ['QQQ', 'SPY', 'IWM'],
    'finance': ['JPM', 'V', 'MA'],
    'health': ['UNH', 'JNJ', 'PFE'],
    'consumer': ['AMZN', 'COST', 'WMT'],
    'energy': ['XOM', 'CVX'],
    'industrial': ['CAT', 'BA']
}

# Symboles haute volatilité pour scalping
SCALPING_SYMBOLS = ['TSLA', 'NVDA', 'AMD', 'QQQ', 'SPY', 'META', 'AAPL', 'MSFT']

# Symboles stables pour swing
SWING_SYMBOLS = ['QQQ', 'SPY', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'V', 'JNJ']


def get_diversified_symbols(max_per_sector: int = 2) -> List[str]:
    """
    Retourne une liste de symboles diversifiés
    
    Args:
        max_per_sector: Maximum de symboles par secteur
    
    Returns:
        Liste de symboles diversifiés
    """
    symbols = []
    for sector, sector_symbols in SYMBOLS_BY_SECTOR.items():
        symbols.extend(sector_symbols[:max_per_sector])
    return symbols


def get_sector(symbol: str) -> str:
    """Retourne le secteur d'un symbole"""
    for sector, symbols in SYMBOLS_BY_SECTOR.items():
        if symbol in symbols:
            return sector
    return 'unknown'


def count_positions_by_sector(positions: List, symbols_by_sector: Dict = None) -> Dict[str, int]:
    """
    Compte les positions par secteur
    
    Args:
        positions: Liste des positions
        symbols_by_sector: Dictionnaire secteurs -> symboles
    
    Returns:
        Dict avec le compte par secteur
    """
    if symbols_by_sector is None:
        symbols_by_sector = SYMBOLS_BY_SECTOR
    
    counts = {sector: 0 for sector in symbols_by_sector.keys()}
    counts['unknown'] = 0
    
    for pos in positions:
        symbol = pos.symbol if hasattr(pos, 'symbol') else pos
        sector = get_sector(symbol)
        counts[sector] = counts.get(sector, 0) + 1
    
    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# TAKE PROFIT PROGRESSIF
# ═══════════════════════════════════════════════════════════════════════════════

# Niveaux de take profit pour swing trading
SWING_TAKE_PROFIT_LEVELS = [
    {'profit_pct': 5, 'sell_pct': 0.25, 'action': 'SELL_25'},
    {'profit_pct': 10, 'sell_pct': 0.25, 'action': 'SELL_25'},
    {'profit_pct': 15, 'sell_pct': 0.25, 'action': 'SELL_25'},
    {'profit_pct': 20, 'sell_pct': 1.0, 'action': 'SELL_ALL'},
]

# Niveaux pour scalping (plus serrés)
SCALPING_TAKE_PROFIT_LEVELS = [
    {'profit_pct': 0.5, 'sell_pct': 0.5, 'action': 'SELL_50'},
    {'profit_pct': 0.8, 'sell_pct': 1.0, 'action': 'SELL_ALL'},
]


def check_take_profit_level(profit_pct: float, levels: List[Dict], 
                           already_sold_pct: float = 0) -> Optional[Dict]:
    """
    Vérifie si un niveau de take profit est atteint
    
    Args:
        profit_pct: Profit actuel en %
        levels: Liste des niveaux de take profit
        already_sold_pct: Pourcentage déjà vendu
    
    Returns:
        Dict avec l'action à effectuer ou None
    """
    total_to_sell = 0
    
    for level in levels:
        if profit_pct >= level['profit_pct']:
            total_to_sell = level['sell_pct']
    
    # Calculer ce qu'il reste à vendre
    remaining_to_sell = total_to_sell - already_sold_pct
    
    if remaining_to_sell > 0:
        return {
            'action': 'SELL',
            'sell_pct': remaining_to_sell,
            'reason': f"Take Profit {profit_pct:.1f}%"
        }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# VOLATILITÉ ADAPTATIVE
# ═══════════════════════════════════════════════════════════════════════════════

def adjust_stop_for_volatility(base_stop_pct: float, atr_pct: float, 
                               min_stop: float = 0.01, max_stop: float = 0.10) -> float:
    """
    Ajuste le stop loss en fonction de la volatilité
    
    Args:
        base_stop_pct: Stop de base (ex: 0.03 = 3%)
        atr_pct: ATR en pourcentage du prix
        min_stop: Stop minimum
        max_stop: Stop maximum
    
    Returns:
        Stop ajusté
    """
    # Si très volatile, augmenter le stop
    if atr_pct > 3.0:
        adjusted = base_stop_pct * 1.5
    elif atr_pct > 2.0:
        adjusted = base_stop_pct * 1.25
    # Si peu volatile, réduire le stop
    elif atr_pct < 1.0:
        adjusted = base_stop_pct * 0.75
    elif atr_pct < 0.5:
        adjusted = base_stop_pct * 0.5
    else:
        adjusted = base_stop_pct
    
    return clamp(adjusted, min_stop, max_stop)


def calculate_atr_percent(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calcule l'ATR en pourcentage du prix
    
    Args:
        df: DataFrame avec high, low, close
        period: Période ATR
    
    Returns:
        ATR en pourcentage
    """
    if len(df) < period:
        return 1.0  # Valeur par défaut
    
    try:
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        current_price = close.iloc[-1]
        atr_pct = safe_divide(atr, current_price, 0.01) * 100
        
        return atr_pct
        
    except Exception as e:
        logger.warning(f"Erreur calcul ATR%: {e}")
        return 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING FORMATÉ
# ═══════════════════════════════════════════════════════════════════════════════

def log_trade_entry(symbol: str, shares: int, price: float, stop: float, 
                   tp: float, reason: str = ""):
    """Log formaté pour une entrée de trade"""
    logger.info("=" * 50)
    logger.info(f"🚀 ACHAT: {symbol}")
    logger.info(f"   Actions: {shares} @ ${price:.2f}")
    logger.info(f"   Valeur: ${shares * price:,.2f}")
    logger.info(f"   Stop Loss: ${stop:.2f} ({safe_divide(price - stop, price, 0) * 100:.1f}%)")
    logger.info(f"   Take Profit: ${tp:.2f} ({safe_divide(tp - price, price, 0) * 100:.1f}%)")
    if reason:
        logger.info(f"   Raison: {reason}")
    logger.info("=" * 50)


def log_trade_exit(symbol: str, shares: int, entry: float, exit_price: float, 
                  reason: str = ""):
    """Log formaté pour une sortie de trade"""
    pnl = (exit_price - entry) * shares
    pnl_pct = safe_divide(exit_price - entry, entry, 0) * 100
    emoji = "💰" if pnl > 0 else "📉"
    
    logger.info("=" * 50)
    logger.info(f"{emoji} VENTE: {symbol}")
    logger.info(f"   Actions: {shares}")
    logger.info(f"   Entrée: ${entry:.2f} → Sortie: ${exit_price:.2f}")
    logger.info(f"   PnL: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
    if reason:
        logger.info(f"   Raison: {reason}")
    logger.info("=" * 50)


# Test du module
if __name__ == "__main__":
    print("✅ Module shared_utils chargé")
    print(f"   safe_divide(10, 0) = {safe_divide(10, 0, -1)}")
    print(f"   safe_divide(10, 2) = {safe_divide(10, 2)}")
    print(f"   Symboles diversifiés: {get_diversified_symbols(2)}")
    print(f"   Secteur AAPL: {get_sector('AAPL')}")
    print(f"   Adjust stop (ATR 3.5%): {adjust_stop_for_volatility(0.03, 3.5)}")

