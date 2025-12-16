"""
🪙 STRATÉGIE CRYPTO CONSERVATRICE V1.0
======================================
Priorité: LIMITER LES RISQUES tout en capturant les opportunités

PHILOSOPHIE:
- Mieux vaut rater un trade que perdre de l'argent
- Patience > Agressivité
- Protection du capital avant tout

STRATÉGIE: MOMENTUM CONFIRMÉ
- On ne trade QUE quand tout est aligné
- Stops serrés et dynamiques
- Take profit progressif

CRYPTOS: BTC, ETH, SOL (les plus sûres)
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
import logging
from typing import Dict, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


def safe_divide(n, d, default=0.0):
    """Division sécurisée"""
    try:
        if d == 0 or pd.isna(d): return default
        r = n / d
        return default if pd.isna(r) or np.isinf(r) else r
    except: return default


def clean_series(s, default=0.0):
    """Nettoie une série"""
    return s.replace([np.inf, -np.inf], np.nan).fillna(default)


def safe_val(v, default=0.0):
    """Valeur sûre"""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return default
    return v


class CryptoStrategy:
    """
    Stratégie Crypto Conservatrice
    ==============================
    Score minimum élevé = moins de trades mais meilleure qualité
    """
    
    def __init__(self):
        # ═══════════════════════════════════════════════════════════
        # INDICATEURS
        # ═══════════════════════════════════════════════════════════
        self.ema_fast = 9
        self.ema_mid = 21
        self.ema_slow = 55
        
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        self.bb_period = 20
        self.bb_std = 2.0
        
        self.adx_period = 14
        self.adx_strong = 25
        
        # ═══════════════════════════════════════════════════════════
        # PARAMÈTRES CONSERVATEURS (Risque limité)
        # ═══════════════════════════════════════════════════════════
        
        # Stops plus larges pour crypto (volatilité)
        # Stops ajustés volatilité (Mode Max Trading)
        self.stop_loss_pct = {
            'BTC': 0.020,   # 2.0% pour BTC
            'ETH': 0.025,   # 2.5% pour ETH
            'SOL': 0.035,   # 3.5% pour SOL
            'default': 0.03
        }
        
        # Take profit AGRESSIF (Laissez courir les gains)
        self.take_profit_pct = {
            'BTC': 0.045,   # 4.5% pour BTC
            'ETH': 0.060,   # 6.0% pour ETH
            'SOL': 0.075,   # 7.5% pour SOL
            'default': 0.06
        }
        
        # Score ÉLEVÉ = Moins de trades mais meilleure qualité
        self.min_score = 8          # Sur 12 (conservateur)
        self.min_confidence = 65    # 65% minimum
        self.max_score = 12
        
        # Filtres de sécurité
        self.min_volume_ratio = 1.2     # Volume 20% au-dessus de la moyenne
        self.max_spread_pct = 0.1       # Max 0.1% de spread
        self.min_adx = 20               # Tendance minimum requise
        
    def get_stop_loss(self, symbol: str) -> float:
        """Retourne le stop loss adapté au symbole"""
        base = symbol.split('/')[0] if '/' in symbol else symbol
        return self.stop_loss_pct.get(base, self.stop_loss_pct['default'])
    
    def get_take_profit(self, symbol: str) -> float:
        """Retourne le take profit adapté"""
        base = symbol.split('/')[0] if '/' in symbol else symbol
        return self.take_profit_pct.get(base, self.take_profit_pct['default'])
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule tous les indicateurs avec protection"""
        df = df.copy()
        
        if len(df) < 60:
            logger.warning("Données insuffisantes pour crypto")
            return df
        
        try:
            # EMAs
            df['ema_9'] = clean_series(EMAIndicator(df['close'], window=self.ema_fast).ema_indicator())
            df['ema_21'] = clean_series(EMAIndicator(df['close'], window=self.ema_mid).ema_indicator())
            df['ema_55'] = clean_series(EMAIndicator(df['close'], window=self.ema_slow).ema_indicator())
            
            # RSI
            df['rsi'] = clean_series(RSIIndicator(df['close'], window=self.rsi_period).rsi(), 50)
            
            # MACD
            macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
            df['macd'] = clean_series(macd.macd())
            df['macd_signal'] = clean_series(macd.macd_signal())
            df['macd_hist'] = clean_series(macd.macd_diff())
            
            # Bollinger Bands
            bb = BollingerBands(df['close'], window=self.bb_period, window_dev=self.bb_std)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_mid'] = bb.bollinger_mavg()
            
            # BB Position (VECTORISÉ - protection div/0)
            bb_range = df['bb_upper'] - df['bb_lower']
            raw_bb_pos = np.where(
                (bb_range != 0) & (~bb_range.isna()),
                (df['close'] - df['bb_lower']) / bb_range,
                0.5
            )
            df['bb_position'] = np.clip(raw_bb_pos, 0, 1)
            
            # ADX
            adx = ADXIndicator(df['high'], df['low'], df['close'], window=self.adx_period)
            df['adx'] = clean_series(adx.adx(), 20)
            df['di_plus'] = clean_series(adx.adx_pos(), 20)
            df['di_minus'] = clean_series(adx.adx_neg(), 20)
            
            # Stochastic
            stoch = StochasticOscillator(df['high'], df['low'], df['close'], window=14, smooth_window=3)
            df['stoch_k'] = clean_series(stoch.stoch(), 50)
            df['stoch_d'] = clean_series(stoch.stoch_signal(), 50)
            
            # ATR (VECTORISÉ)
            df['atr'] = clean_series(
                AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
            )
            df['atr_pct'] = np.where(
                (df['close'] != 0) & (~df['close'].isna()),
                (df['atr'] / df['close']) * 100,
                2.0
            )
            
            # Volume (VECTORISÉ)
            df['volume_sma'] = df['volume'].rolling(20).mean().fillna(df['volume'].mean())
            df['volume_ratio'] = np.where(
                (df['volume_sma'] != 0) & (~df['volume_sma'].isna()),
                df['volume'] / df['volume_sma'],
                1.0
            )
            
            # Momentum (ROC)
            df['momentum'] = df['close'].pct_change(10) * 100
            df['momentum'] = clean_series(df['momentum'])
            
        except Exception as e:
            logger.error(f"Erreur indicateurs crypto: {e}")
        
        return df
    
    def calculate_score(self, row: pd.Series, prev: pd.Series) -> Tuple[float, list]:
        """
        Calcule le score de trading CONSERVATEUR
        Plus strict que pour les actions
        """
        score = 0.0
        reasons = []
        
        def sv(v, d=0): return safe_val(v, d)
        
        # ═══════════════════════════════════════════════════════════
        # 1. TENDANCE CLAIRE (Obligatoire) - 3 points
        # ═══════════════════════════════════════════════════════════
        ema_9 = sv(row.get('ema_9'))
        ema_21 = sv(row.get('ema_21'))
        ema_55 = sv(row.get('ema_55'))
        close = sv(row.get('close'))
        
        if close > ema_9 > ema_21 > ema_55:
            score += 3
            reasons.append("✅ Tendance haussière forte (Prix>EMA9>21>55)")
        elif close > ema_21 > ema_55:
            score += 2
            reasons.append("✅ Tendance haussière (Prix>EMA21>55)")
        elif close > ema_55:
            score += 1
            reasons.append("⚠️ Au-dessus EMA55")
        else:
            reasons.append("❌ Pas de tendance haussière")
            return 0, reasons  # STOP - Pas de trade sans tendance
        
        # ═══════════════════════════════════════════════════════════
        # 2. ADX - Force de tendance (Obligatoire) - 2 points
        # ═══════════════════════════════════════════════════════════
        adx = sv(row.get('adx'), 15)
        di_plus = sv(row.get('di_plus'), 20)
        di_minus = sv(row.get('di_minus'), 20)
        
        if adx < self.min_adx:
            reasons.append(f"❌ ADX trop faible ({adx:.0f} < {self.min_adx})")
            return score, reasons  # Pas assez de tendance
        
        if adx > 30 and di_plus > di_minus:
            score += 2
            reasons.append(f"✅ ADX fort ({adx:.0f}) + DI+ > DI-")
        elif adx > self.min_adx and di_plus > di_minus:
            score += 1
            reasons.append(f"✅ ADX OK ({adx:.0f})")
        
        # ═══════════════════════════════════════════════════════════
        # 3. RSI - Zone favorable - 2 points
        # ═══════════════════════════════════════════════════════════
        rsi = sv(row.get('rsi'), 50)
        prev_rsi = sv(prev.get('rsi'), 50)
        
        if 35 <= rsi <= 55:
            score += 2
            reasons.append(f"✅ RSI zone rebond ({rsi:.0f})")
        elif 55 < rsi < 65:
            score += 1
            reasons.append(f"✅ RSI momentum ({rsi:.0f})")
        elif rsi >= 70:
            reasons.append(f"⚠️ RSI suracheté ({rsi:.0f})")
            score -= 1  # Pénalité
        
        # RSI en hausse
        if rsi > prev_rsi and rsi < 65:
            score += 0.5
            reasons.append("✅ RSI en hausse")
        
        # ═══════════════════════════════════════════════════════════
        # 4. MACD - Confirmation - 2 points
        # ═══════════════════════════════════════════════════════════
        macd = sv(row.get('macd'))
        macd_signal = sv(row.get('macd_signal'))
        macd_hist = sv(row.get('macd_hist'))
        prev_macd_hist = sv(prev.get('macd_hist'))
        
        if macd > macd_signal and macd_hist > 0:
            score += 1.5
            reasons.append("✅ MACD haussier")
        if macd_hist > prev_macd_hist and macd_hist > 0:
            score += 0.5
            reasons.append("✅ MACD accélère")
        
        # ═══════════════════════════════════════════════════════════
        # 5. VOLUME - Confirmation (Important pour crypto) - 1 point
        # ═══════════════════════════════════════════════════════════
        volume_ratio = sv(row.get('volume_ratio'), 1)
        
        if volume_ratio < self.min_volume_ratio:
            reasons.append(f"⚠️ Volume faible ({volume_ratio:.2f}x)")
            score -= 0.5
        elif volume_ratio > 1.5:
            score += 1
            reasons.append(f"✅ Volume élevé ({volume_ratio:.1f}x)")
        elif volume_ratio > 1.2:
            score += 0.5
            reasons.append(f"✅ Volume OK ({volume_ratio:.1f}x)")
        
        # ═══════════════════════════════════════════════════════════
        # 6. BOLLINGER - Position - 1 point
        # ═══════════════════════════════════════════════════════════
        bb_pos = sv(row.get('bb_position'), 0.5)
        
        if bb_pos < 0.4:
            score += 1
            reasons.append(f"✅ Prix bas des BB ({bb_pos:.2f})")
        elif bb_pos > 0.85:
            reasons.append(f"⚠️ Prix haut des BB ({bb_pos:.2f})")
            score -= 0.5
        
        # ═══════════════════════════════════════════════════════════
        # 7. STOCHASTIC - Confirmation - 1 point
        # ═══════════════════════════════════════════════════════════
        stoch_k = sv(row.get('stoch_k'), 50)
        stoch_d = sv(row.get('stoch_d'), 50)
        
        if stoch_k > stoch_d and stoch_k < 75:
            score += 0.5
            reasons.append(f"✅ Stoch haussier ({stoch_k:.0f})")
        if stoch_k < 30:
            score += 0.5
            reasons.append("✅ Stoch survendu")
        
        return score, reasons
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Génère un signal de trading conservateur"""
        
        if len(df) < 60:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Données insuffisantes'}
        
        df = self.calculate_indicators(df)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        score, reasons = self.calculate_score(current, prev)
        confidence = (score / self.max_score) * 100
        
        close = safe_val(current.get('close'), 0)
        if close <= 0:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Prix invalide'}
        
        atr_pct = safe_val(current.get('atr_pct'), 2)
        
        result = {
            'signal': 'HOLD',
            'symbol': symbol,
            'confidence': confidence,
            'score': score,
            'max_score': self.max_score,
            'reasons': reasons,
            'price': close,
            'atr_pct': atr_pct,
            'indicators': {
                'rsi': safe_val(current.get('rsi'), 50),
                'adx': safe_val(current.get('adx'), 20),
                'macd_hist': safe_val(current.get('macd_hist'), 0),
                'volume_ratio': safe_val(current.get('volume_ratio'), 1),
                'bb_position': safe_val(current.get('bb_position'), 0.5)
            }
        }
        
        # SIGNAL ACHAT (CONSERVATEUR)
        if score >= self.min_score and confidence >= self.min_confidence:
            stop_pct = self.get_stop_loss(symbol)
            tp_pct = self.get_take_profit(symbol)
            
            # Ajuster selon volatilité
            if atr_pct > 4:
                stop_pct *= 1.3
                tp_pct *= 1.3
            
            stop_loss = close * (1 - stop_pct)
            take_profit = close * (1 + tp_pct)
            
            result.update({
                'signal': 'BUY',
                'entry_price': close,
                'stop_loss': stop_loss,
                'stop_loss_pct': stop_pct * 100,
                'take_profit': take_profit,
                'take_profit_pct': tp_pct * 100,
                'risk_reward': safe_divide(tp_pct, stop_pct, 2)
            })
            
            logger.info(f"🪙 SIGNAL {symbol}: Score {score:.1f}/{self.max_score} ({confidence:.0f}%)")
            for r in reasons[:5]:
                logger.info(f"   {r}")
        
        # Signal de vente
        elif safe_val(current.get('rsi'), 50) > 75:
            result.update({'signal': 'SELL', 'reason': 'RSI suracheté'})
        elif safe_val(current.get('bb_position'), 0.5) > 0.95:
            result.update({'signal': 'SELL', 'reason': 'Prix > BB haute'})
        
        return result
    
    def should_exit(self, entry: float, current: float, highest: float,
                   symbol: str, position_data: Dict) -> Dict:
        """Vérifie si on doit sortir"""
        if entry <= 0 or current <= 0:
            return {'exit': False}
        
        stop = position_data.get('stop_loss', entry * 0.98)
        tp = position_data.get('take_profit', entry * 1.04)
        
        profit_pct = safe_divide(current - entry, entry, 0) * 100
        
        # Stop Loss
        if current <= stop:
            return {'exit': True, 'reason': f'Stop Loss ({profit_pct:.2f}%)', 'type': 'STOP'}
        
        # Take Profit
        if current >= tp:
            return {'exit': True, 'reason': f'Take Profit ({profit_pct:.2f}%)', 'type': 'TP'}
        
        # Trailing Stop (après +2%)
        if profit_pct > 2:
            trail_stop = highest * 0.985  # 1.5% trailing
            if current <= trail_stop:
                return {'exit': True, 'reason': f'Trailing ({profit_pct:.2f}%)', 'type': 'TRAIL'}
        
        return {'exit': False, 'profit_pct': profit_pct}


if __name__ == "__main__":
    s = CryptoStrategy()
    print("🪙 Stratégie Crypto Conservatrice V1.0")
    print(f"   Score minimum: {s.min_score}/{s.max_score}")
    print(f"   Stops: BTC {s.stop_loss_pct['BTC']*100}%, ETH {s.stop_loss_pct['ETH']*100}%")
    print(f"   TP: BTC {s.take_profit_pct['BTC']*100}%, ETH {s.take_profit_pct['ETH']*100}%")

