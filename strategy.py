"""
📊 STRATÉGIE SWING TRADING V3.0
===============================
Version: 3.0 - Optimisée avec protections
Date: Décembre 2024

AMÉLIORATIONS V3.0:
✅ Protection division par zéro
✅ Take profit progressif (25% à chaque niveau)
✅ Stop adaptatif à la volatilité
✅ Filtrage par news sentiment
✅ Validation des données
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import ta
from alpaca_trade_api import TimeFrame
from typing import Dict, Optional, Tuple

# Import des utilitaires partagés
try:
    from shared_utils import (safe_divide, clean_series, safe_value, 
                             adjust_stop_for_volatility, check_take_profit_level,
                             SWING_TAKE_PROFIT_LEVELS)
except ImportError:
    # Fallback
    def safe_divide(n, d, default=0.0):
        try:
            if d == 0: return default
            return n / d
        except: return default
    
    def safe_value(v, default=0.0):
        if v is None or (isinstance(v, float) and np.isnan(v)): return default
        return v
    
    def clean_series(s, d=0.0):
        return s.fillna(d)
    
    def adjust_stop_for_volatility(base, atr, mn=0.01, mx=0.10):
        return base
    
    SWING_TAKE_PROFIT_LEVELS = [
        {'profit_pct': 5, 'sell_pct': 0.25},
        {'profit_pct': 10, 'sell_pct': 0.25},
        {'profit_pct': 15, 'sell_pct': 0.25},
        {'profit_pct': 20, 'sell_pct': 1.0},
    ]

logger = logging.getLogger(__name__)


class TradingStrategy:
    """
    Stratégie Swing Trading V3.0
    ============================
    Long uniquement avec indicateurs techniques optimisés
    """
    
    def __init__(self, api):
        self.api = api
        
        # ═══════════════════════════════════════════════════════════
        # PARAMÈTRES STRATÉGIE
        # ═══════════════════════════════════════════════════════════
        self.rsi_oversold = 35
        self.rsi_overbought = 70
        self.min_score = 5
        
        # Stop/TP (seront ajustés à la volatilité)
        self.base_stop_loss_pct = 0.03      # 3% base
        self.base_take_profit_pct = 0.10    # 10% base
        self.trailing_stop_pct = 0.03       # 3% trailing
        
        # Take profit progressif
        self.take_profit_levels = SWING_TAKE_PROFIT_LEVELS
        
        # News sentiment
        self.use_news_sentiment = True
        self.news_analyzer = None
        self._init_news_analyzer()
    
    def _init_news_analyzer(self):
        """Initialise l'analyseur de news"""
        try:
            from scalping_bot.news_sentiment import get_sentiment_analyzer
            self.news_analyzer = get_sentiment_analyzer()
            logger.info("📰 News sentiment activé")
        except:
            logger.info("📰 News sentiment non disponible")
            self.news_analyzer = None
    
    def get_historical_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Récupère les données historiques"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            bars = self.api.get_bars(
                symbol,
                TimeFrame.Day,
                start.strftime('%Y-%m-%d'),
                end.strftime('%Y-%m-%d'),
                limit=days,
                feed='iex'  # Données gratuites IEX
            )
            
            data = []
            for bar in bars:
                data.append({
                    'timestamp': bar.t,
                    'open': bar.o,
                    'high': bar.h,
                    'low': bar.l,
                    'close': bar.c,
                    'volume': bar.v
                })
            
            df = pd.DataFrame(data)
            if len(df) > 0:
                df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur données {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule tous les indicateurs avec protection division/0 (VECTORISÉ - Sans warnings)"""
        if len(df) < 50:
            return df
        
        # Force une copie explicite pour éviter les SettingWithCopyWarning
        df = df.copy()
        
        try:
            # RSI
            df['rsi'] = clean_series(ta.momentum.RSIIndicator(df['close'], window=14).rsi(), 50)
            
            # MACD
            macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
            df['macd'] = clean_series(macd.macd())
            df['macd_signal'] = clean_series(macd.macd_signal())
            df['macd_diff'] = clean_series(macd.macd_diff())
            
            # SMAs
            df['sma_20'] = clean_series(ta.trend.SMAIndicator(df['close'], window=20).sma_indicator())
            df['sma_50'] = clean_series(ta.trend.SMAIndicator(df['close'], window=50).sma_indicator())
            df['sma_200'] = clean_series(ta.trend.SMAIndicator(df['close'], window=200).sma_indicator())
            df['ema_20'] = clean_series(ta.trend.EMAIndicator(df['close'], window=20).ema_indicator())
            
            # Bollinger Bands avec protection
            bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bollinger.bollinger_hband()
            df['bb_middle'] = bollinger.bollinger_mavg()
            df['bb_lower'] = bollinger.bollinger_lband()
            
            # Position BB avec protection division/0 (VECTORISÉ - pas de boucle)
            bb_range = df['bb_upper'] - df['bb_lower']
            df['bb_position'] = np.where(
                (bb_range != 0) & (~bb_range.isna()),
                (df['close'] - df['bb_lower']) / bb_range,
                0.5
            )
            
            # ATR
            df['atr'] = clean_series(
                ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range(),
                df['close'].std()
            )
            
            # ATR en pourcentage (VECTORISÉ - pas de boucle)
            df['atr_pct'] = np.where(
                (df['close'] != 0) & (~df['close'].isna()),
                (df['atr'] / df['close']) * 100,
                2.0
            )
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], window=14, smooth_window=3)
            df['stoch_k'] = clean_series(stoch.stoch(), 50)
            df['stoch_d'] = clean_series(stoch.stoch_signal(), 50)
            
            # Volume SMA avec protection (VECTORISÉ - pas de boucle)
            df['volume_sma'] = df['volume'].rolling(window=20).mean().fillna(df['volume'].mean())
            df['volume_ratio'] = np.where(
                (df['volume_sma'] != 0) & (~df['volume_sma'].isna()),
                df['volume'] / df['volume_sma'],
                1.0
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs: {e}")
        
        return df
    
    def analyze(self, symbol: str) -> Dict:
        """Analyse un symbole et génère un signal"""
        result = {
            'symbol': symbol,
            'action': 'HOLD',
            'score': 0,
            'reasons': [],
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'take_profit_levels': [],
            'news_sentiment': 0
        }
        
        # Récupérer les données
        df = self.get_historical_data(symbol)
        
        if len(df) < 50:
            result['reasons'].append("Données insuffisantes")
            return result
        
        # Calculer les indicateurs
        df = self.calculate_indicators(df)
        
        # Dernières bougies
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # ═══════════════════════════════════════════════════════════
        # NEWS SENTIMENT (NOUVEAU)
        # ═══════════════════════════════════════════════════════════
        news_sentiment = 0.0
        if self.news_analyzer and self.use_news_sentiment:
            try:
                should_trade, reason, sentiment = self.news_analyzer.should_trade(symbol)
                news_sentiment = sentiment
                result['news_sentiment'] = sentiment
                
                if not should_trade and sentiment < -0.3:
                    result['reasons'].append(f"📰 News négatives ({sentiment:.2f})")
                    return result
            except:
                pass
        
        score = 0
        reasons = []
        
        # ═══════════════════════════════════════════════════════════
        # CONDITIONS OBLIGATOIRES
        # ═══════════════════════════════════════════════════════════
        
        # 1. Tendance haussière (Prix > SMA 200)
        sma_200 = safe_value(last.get('sma_200'), 0)
        close = safe_value(last.get('close'), 0)
        
        if sma_200 > 0 and close > sma_200:
            score += 2
            reasons.append("✅ Prix > SMA200 (tendance ↑)")
        else:
            result['reasons'].append("❌ Tendance baissière")
            return result
        
        # 2. Golden Cross (SMA 50 > SMA 200)
        sma_50 = safe_value(last.get('sma_50'), 0)
        if sma_50 > 0 and sma_200 > 0 and sma_50 > sma_200:
            score += 1
            reasons.append("✅ Golden Cross")
        
        # ═══════════════════════════════════════════════════════════
        # SIGNAUX DE DÉCLENCHEMENT
        # ═══════════════════════════════════════════════════════════
        
        # 3. RSI
        rsi = safe_value(last.get('rsi'), 50)
        prev_rsi = safe_value(prev.get('rsi'), 50)
        
        if prev_rsi < self.rsi_oversold and rsi > self.rsi_oversold:
            score += 2
            reasons.append(f"✅ RSI rebond survente ({rsi:.1f})")
        elif rsi < 40:
            score += 1
            reasons.append(f"✅ RSI bas ({rsi:.1f})")
        
        # 4. MACD
        macd_diff = safe_value(last.get('macd_diff'), 0)
        prev_macd_diff = safe_value(prev.get('macd_diff'), 0)
        
        if prev_macd_diff < 0 and macd_diff > 0:
            score += 3
            reasons.append("✅ Croisement MACD haussier")
        elif macd_diff > 0:
            score += 1
            reasons.append("✅ MACD positif")
        
        # 5. Bollinger Bands
        bb_position = safe_value(last.get('bb_position'), 0.5)
        if bb_position < 0.2:
            score += 2
            reasons.append("✅ Prix près BB basse")
        elif bb_position < 0.4:
            score += 1
            reasons.append("✅ Prix sous BB moyenne")
        
        # 6. Volume
        volume_ratio = safe_value(last.get('volume_ratio'), 1)
        if volume_ratio > 1.5:
            score += 1
            reasons.append(f"✅ Volume +{(volume_ratio-1)*100:.0f}%")
        
        # 7. Stochastic
        stoch_k = safe_value(last.get('stoch_k'), 50)
        if stoch_k < 25:
            score += 1
            reasons.append(f"✅ Stoch bas ({stoch_k:.1f})")
        
        # 8. EMA 20
        ema_20 = safe_value(last.get('ema_20'), 0)
        if ema_20 > 0 and close > ema_20:
            score += 1
            reasons.append("✅ Prix > EMA20")
        
        # 9. News sentiment bonus
        if news_sentiment > 0.3:
            score += 1
            reasons.append(f"📰 News positives (+{news_sentiment:.2f})")
        
        # ═══════════════════════════════════════════════════════════
        # DÉCISION
        # ═══════════════════════════════════════════════════════════
        
        result['score'] = score
        result['reasons'] = reasons
        result['entry_price'] = close
        
        if score >= self.min_score:
            result['action'] = 'BUY'
            
            # ATR et volatilité
            atr = safe_value(last.get('atr'), close * 0.02)
            atr_pct = safe_value(last.get('atr_pct'), 2.0)
            
            # Stop adaptatif à la volatilité
            stop_pct = adjust_stop_for_volatility(self.base_stop_loss_pct, atr_pct, 0.02, 0.08)
            
            # Stop basé sur ATR
            atr_stop = close - (2 * atr)
            pct_stop = close * (1 - stop_pct)
            result['stop_loss'] = max(atr_stop, pct_stop)
            
            # Take profit adaptatif (ajusté selon conditions marché)
            # hold_multiplier est passé depuis le bot principal
            hold_mult = getattr(self, 'hold_multiplier', 1.0)
            
            tp_pct = stop_pct * 3 * hold_mult  # Ratio 1:3 * hold_multiplier
            result['take_profit'] = close * (1 + tp_pct)
            
            # Niveaux de take profit progressif (ajustés selon marché)
            # Si marché porteur (hold_mult > 1), on laisse courir plus longtemps
            base_levels = [5, 10, 15, 20]
            adjusted_levels = [l * hold_mult for l in base_levels]
            
            result['take_profit_levels'] = [
                {'pct': adjusted_levels[0], 'price': close * (1 + adjusted_levels[0]/100), 'sell': 0.20},
                {'pct': adjusted_levels[1], 'price': close * (1 + adjusted_levels[1]/100), 'sell': 0.25},
                {'pct': adjusted_levels[2], 'price': close * (1 + adjusted_levels[2]/100), 'sell': 0.25},
                {'pct': adjusted_levels[3], 'price': close * (1 + adjusted_levels[3]/100), 'sell': 1.0},
            ]
            
            if hold_mult > 1:
                logger.info(f"   📍 Hold {hold_mult}x: TP ajustés à {adjusted_levels[0]:.0f}%/{adjusted_levels[1]:.0f}%/{adjusted_levels[2]:.0f}%/{adjusted_levels[3]:.0f}%")
            
            logger.info(f"🎯 SIGNAL {symbol}: Score {score} | Stop {stop_pct*100:.1f}%")
        
        return result
    
    def check_take_profit(self, position, already_sold_pct: float = 0) -> Optional[Dict]:
        """
        Vérifie si un niveau de take profit est atteint
        
        Args:
            position: Position Alpaca
            already_sold_pct: Pourcentage déjà vendu
        
        Returns:
            Dict avec action à effectuer ou None
        """
        current = float(position.current_price)
        entry = float(position.avg_entry_price)
        
        profit_pct = safe_divide(current - entry, entry, 0) * 100
        
        for level in self.take_profit_levels:
            if profit_pct >= level['profit_pct']:
                to_sell = level['sell_pct'] - already_sold_pct
                if to_sell > 0:
                    return {
                        'action': 'SELL_PARTIAL' if to_sell < 1 else 'SELL_ALL',
                        'sell_pct': to_sell,
                        'profit_pct': profit_pct,
                        'reason': f"Take Profit +{profit_pct:.1f}%"
                    }
        
        return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Récupère le prix actuel"""
        try:
            quote = self.api.get_latest_trade(symbol)
            return quote.price
        except Exception as e:
            logger.error(f"Erreur prix {symbol}: {e}")
            return None


if __name__ == "__main__":
    print("✅ Stratégie Swing V3.0 chargée")
    print(f"   Score min: 5")
    print(f"   Stop base: 3%")
    print(f"   Take profit progressif: 5%, 10%, 15%, 20%")
