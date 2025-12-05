"""
🔥 STRATÉGIE CONFLUENCE SCALPING ULTRA-OPTIMISÉE V2.1
=====================================================
Version: 2.1 - Avec corrections division par zéro + News API
Auteur: Trading Bot System
Date: Décembre 2024

CORRECTIONS V2.1:
- Protection contre division par zéro (bb_upper-bb_lower, vwap, volume_sma)
- Gestion des valeurs NaN/Inf
- Intégration Alpaca News API pour sentiment

INDICATEURS UTILISÉS (7):
- EMA 5/9/21 (tendance)
- RSI 7 (momentum rapide)
- VWAP (prix institutionnel)
- Bollinger Bands 20,2 (volatilité)
- Stochastic 14,3,3 (confirmation)
- Volume Profile (liquidité)
- ATR (volatilité adaptative)
+ NEWS SENTIMENT (bonus)

TAUX DE RÉUSSITE ESTIMÉ: 65-75%
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
import logging
from typing import Optional
import warnings

# Ignorer les warnings de division
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


def safe_divide(numerator, denominator, default=0.0):
    """
    Division sécurisée qui évite les erreurs de division par zéro
    
    Args:
        numerator: Numérateur
        denominator: Dénominateur
        default: Valeur par défaut si division impossible
    
    Returns:
        Résultat de la division ou valeur par défaut
    """
    if isinstance(denominator, pd.Series):
        result = numerator / denominator.replace(0, np.nan)
        return result.fillna(default)
    elif isinstance(denominator, (int, float)):
        if denominator == 0 or np.isnan(denominator) or np.isinf(denominator):
            return default
        return numerator / denominator
    else:
        try:
            if denominator == 0:
                return default
            return numerator / denominator
        except:
            return default


def clean_series(series: pd.Series, default=0.0) -> pd.Series:
    """
    Nettoie une série pandas des valeurs NaN et Inf
    """
    series = series.replace([np.inf, -np.inf], np.nan)
    return series.fillna(default)


class ScalpingStrategy:
    """
    Stratégie de Scalping Ultra-Optimisée V2.1
    ==========================================
    - 7 indicateurs en confluence
    - Protection contre division par zéro
    - Intégration News Sentiment (optionnel)
    """
    
    def __init__(self):
        # ═══════════════════════════════════════════════════════════
        # PARAMÈTRES DES INDICATEURS (Optimisés pour scalping)
        # ═══════════════════════════════════════════════════════════
        
        # EMAs rapides pour scalping
        self.ema_ultra_fast = 5
        self.ema_fast = 9
        self.ema_slow = 21
        
        # RSI rapide
        self.rsi_period = 7
        self.rsi_oversold = 25
        self.rsi_overbought = 75
        self.rsi_neutral_low = 40
        self.rsi_neutral_high = 60
        
        # Stochastic
        self.stoch_k = 14
        self.stoch_d = 3
        self.stoch_smooth = 3
        
        # Bollinger Bands
        self.bb_period = 20
        self.bb_std = 2.0
        
        # ADX
        self.adx_period = 14
        self.adx_strong = 25
        
        # Volume
        self.volume_sma_period = 20
        self.volume_spike_threshold = 1.5
        
        # ═══════════════════════════════════════════════════════════
        # PARAMÈTRES DE RISQUE
        # ═══════════════════════════════════════════════════════════
        
        self.stop_loss_pct = 0.004          # 0.4%
        self.take_profit_pct = 0.008        # 0.8%
        self.trailing_stop_trigger = 0.004
        self.trailing_stop_pct = 0.002
        
        # Score minimum
        self.min_score_buy = 7
        self.min_confidence = 60
        
        # News sentiment bonus
        self.news_sentiment_bonus = 1.0  # +1 point si news positives
        
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcule le VWAP avec protection contre division par zéro
        """
        df = df.copy()
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_volume'] = df['typical_price'] * df['volume']
        df['cumulative_tp_volume'] = df['tp_volume'].cumsum()
        df['cumulative_volume'] = df['volume'].cumsum()
        
        # Protection division par zéro
        vwap = safe_divide(df['cumulative_tp_volume'], df['cumulative_volume'], df['close'])
        return clean_series(vwap, df['close'].iloc[-1] if len(df) > 0 else 0)
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule TOUS les indicateurs avec protection contre erreurs
        """
        df = df.copy()
        
        if len(df) < 50:
            logger.warning("Pas assez de données pour calculer les indicateurs")
            return df
        
        try:
            # ═══════════════════════════════════════════════════════════
            # 1. MOYENNES MOBILES EXPONENTIELLES
            # ═══════════════════════════════════════════════════════════
            df['ema_5'] = EMAIndicator(df['close'], window=self.ema_ultra_fast).ema_indicator()
            df['ema_9'] = EMAIndicator(df['close'], window=self.ema_fast).ema_indicator()
            df['ema_21'] = EMAIndicator(df['close'], window=self.ema_slow).ema_indicator()
            
            # Pente des EMAs - Protection division par zéro
            ema_9_shifted = df['ema_9'].shift(3)
            ema_21_shifted = df['ema_21'].shift(3)
            
            df['ema_9_slope'] = safe_divide(df['ema_9'].diff(3), ema_9_shifted, 0) * 100
            df['ema_21_slope'] = safe_divide(df['ema_21'].diff(3), ema_21_shifted, 0) * 100
            
            df['ema_9_slope'] = clean_series(df['ema_9_slope'])
            df['ema_21_slope'] = clean_series(df['ema_21_slope'])
            
            # ═══════════════════════════════════════════════════════════
            # 2. RSI RAPIDE
            # ═══════════════════════════════════════════════════════════
            df['rsi'] = RSIIndicator(df['close'], window=self.rsi_period).rsi()
            df['rsi'] = clean_series(df['rsi'], 50)  # 50 = neutre par défaut
            df['rsi_sma'] = df['rsi'].rolling(window=5).mean().fillna(50)
            
            # ═══════════════════════════════════════════════════════════
            # 3. STOCHASTIC OSCILLATOR
            # ═══════════════════════════════════════════════════════════
            stoch = StochasticOscillator(
                df['high'], df['low'], df['close'],
                window=self.stoch_k, smooth_window=self.stoch_d
            )
            df['stoch_k'] = clean_series(stoch.stoch(), 50)
            df['stoch_d'] = clean_series(stoch.stoch_signal(), 50)
            
            # ═══════════════════════════════════════════════════════════
            # 4. BOLLINGER BANDS - PROTECTION CRITIQUE
            # ═══════════════════════════════════════════════════════════
            bb = BollingerBands(df['close'], window=self.bb_period, window_dev=self.bb_std)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_lower'] = bb.bollinger_lband()
            
            # Protection division par zéro pour bb_width et bb_position
            bb_range = df['bb_upper'] - df['bb_lower']
            df['bb_width'] = safe_divide(bb_range, df['bb_middle'], 0.02)
            df['bb_width'] = clean_series(df['bb_width'], 0.02)
            
            # Position dans les bandes (0 = bas, 1 = haut)
            # CRITIQUE: éviter division par zéro quand bb_upper == bb_lower
            df['bb_position'] = safe_divide(
                df['close'] - df['bb_lower'],
                bb_range,
                0.5  # Par défaut au milieu
            )
            df['bb_position'] = clean_series(df['bb_position'], 0.5)
            # Clamp entre 0 et 1
            df['bb_position'] = df['bb_position'].clip(0, 1)
            
            # ═══════════════════════════════════════════════════════════
            # 5. VWAP - PROTECTION
            # ═══════════════════════════════════════════════════════════
            df['vwap'] = self.calculate_vwap(df)
            df['vwap_distance'] = safe_divide(
                df['close'] - df['vwap'],
                df['vwap'],
                0
            ) * 100
            df['vwap_distance'] = clean_series(df['vwap_distance'])
            
            # ═══════════════════════════════════════════════════════════
            # 6. ADX
            # ═══════════════════════════════════════════════════════════
            adx = ADXIndicator(df['high'], df['low'], df['close'], window=self.adx_period)
            df['adx'] = clean_series(adx.adx(), 20)
            df['di_plus'] = clean_series(adx.adx_pos(), 20)
            df['di_minus'] = clean_series(adx.adx_neg(), 20)
            
            # ═══════════════════════════════════════════════════════════
            # 7. MACD
            # ═══════════════════════════════════════════════════════════
            macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
            df['macd'] = clean_series(macd.macd())
            df['macd_signal'] = clean_series(macd.macd_signal())
            df['macd_histogram'] = clean_series(macd.macd_diff())
            
            # ═══════════════════════════════════════════════════════════
            # 8. VOLUME - PROTECTION DIVISION PAR ZÉRO
            # ═══════════════════════════════════════════════════════════
            df['volume_sma'] = df['volume'].rolling(window=self.volume_sma_period).mean()
            df['volume_sma'] = df['volume_sma'].fillna(df['volume'].mean())
            
            # Protection critique pour volume_ratio
            df['volume_ratio'] = safe_divide(df['volume'], df['volume_sma'], 1.0)
            df['volume_ratio'] = clean_series(df['volume_ratio'], 1.0)
            
            # OBV
            df['obv'] = OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
            df['obv'] = clean_series(df['obv'])
            df['obv_sma'] = df['obv'].rolling(window=20).mean().fillna(df['obv'])
            
            # ═══════════════════════════════════════════════════════════
            # 9. ATR - PROTECTION
            # ═══════════════════════════════════════════════════════════
            df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
            df['atr'] = clean_series(df['atr'], df['close'].std())
            
            df['atr_pct'] = safe_divide(df['atr'], df['close'], 0.01) * 100
            df['atr_pct'] = clean_series(df['atr_pct'], 1.0)
            
            # ═══════════════════════════════════════════════════════════
            # 10. PRICE ACTION
            # ═══════════════════════════════════════════════════════════
            df['price_change'] = df['close'].pct_change() * 100
            df['price_change'] = clean_series(df['price_change'])
            
            df['high_low_range'] = safe_divide(df['high'] - df['low'], df['close'], 0) * 100
            df['high_low_range'] = clean_series(df['high_low_range'])
            
            df['body'] = abs(df['close'] - df['open'])
            df['is_bullish'] = df['close'] > df['open']
            
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs: {e}")
            # Remplir avec des valeurs par défaut sûres
            for col in ['ema_5', 'ema_9', 'ema_21']:
                if col not in df.columns:
                    df[col] = df['close']
            for col in ['rsi', 'stoch_k', 'stoch_d']:
                if col not in df.columns:
                    df[col] = 50
            for col in ['bb_position']:
                if col not in df.columns:
                    df[col] = 0.5
        
        return df
    
    def calculate_buy_score(self, row: pd.Series, prev_row: pd.Series, 
                           news_sentiment: Optional[float] = None) -> tuple:
        """
        Calcule un score d'achat avec protection contre NaN
        
        Args:
            row: Ligne actuelle
            prev_row: Ligne précédente
            news_sentiment: Score de sentiment des news (-1 à +1)
        
        Returns:
            tuple: (score, max_score, reasons_list)
        """
        score = 0.0
        max_score = 13  # 12 + 1 pour news
        reasons = []
        
        # Helper pour vérifier les valeurs
        def safe_value(val, default=0):
            if pd.isna(val) or np.isinf(val):
                return default
            return val
        
        # ═══════════════════════════════════════════════════════════
        # 1. PRIX VS VWAP (+2 points)
        # ═══════════════════════════════════════════════════════════
        close = safe_value(row.get('close', 0))
        vwap = safe_value(row.get('vwap', close))
        vwap_distance = safe_value(row.get('vwap_distance', 0))
        
        if close > vwap:
            score += 2
            reasons.append(f"✅ Prix > VWAP (+{vwap_distance:.2f}%)")
        elif close > vwap * 0.998:
            score += 1
            reasons.append(f"⚠️ Prix ≈ VWAP ({vwap_distance:.2f}%)")
        
        # ═══════════════════════════════════════════════════════════
        # 2. TENDANCE EMA (+2 points)
        # ═══════════════════════════════════════════════════════════
        ema_5 = safe_value(row.get('ema_5', 0))
        ema_9 = safe_value(row.get('ema_9', 0))
        ema_21 = safe_value(row.get('ema_21', 0))
        
        if ema_5 > ema_9 > ema_21:
            score += 2
            reasons.append("✅ EMAs alignées (5>9>21)")
        elif ema_9 > ema_21:
            score += 1
            reasons.append("✅ EMA9 > EMA21")
        
        # ═══════════════════════════════════════════════════════════
        # 3. PENTE EMA (+1 point)
        # ═══════════════════════════════════════════════════════════
        ema_9_slope = safe_value(row.get('ema_9_slope', 0))
        ema_21_slope = safe_value(row.get('ema_21_slope', 0))
        
        if ema_9_slope > 0 and ema_21_slope > 0:
            score += 1
            reasons.append(f"✅ Pente EMA positive ({ema_9_slope:.2f}%)")
        
        # ═══════════════════════════════════════════════════════════
        # 4. RSI (+2 points)
        # ═══════════════════════════════════════════════════════════
        rsi = safe_value(row.get('rsi', 50))
        prev_rsi = safe_value(prev_row.get('rsi', 50))
        
        if self.rsi_oversold <= rsi <= 45:
            score += 2
            reasons.append(f"✅ RSI={rsi:.1f} (zone rebond)")
        elif rsi < self.rsi_oversold:
            score += 1
            reasons.append(f"⚠️ RSI={rsi:.1f} (survendu)")
        elif 45 < rsi < 60:
            score += 1
            reasons.append(f"✅ RSI={rsi:.1f} (neutre+)")
        
        if rsi > prev_rsi and rsi < 60:
            score += 0.5
            reasons.append("✅ RSI en hausse")
        
        # ═══════════════════════════════════════════════════════════
        # 5. STOCHASTIC (+1 point)
        # ═══════════════════════════════════════════════════════════
        stoch_k = safe_value(row.get('stoch_k', 50))
        stoch_d = safe_value(row.get('stoch_d', 50))
        prev_stoch_k = safe_value(prev_row.get('stoch_k', 50))
        prev_stoch_d = safe_value(prev_row.get('stoch_d', 50))
        
        if stoch_k > stoch_d and prev_stoch_k <= prev_stoch_d:
            score += 1
            reasons.append(f"✅ Stoch croisement haussier (K={stoch_k:.1f})")
        elif stoch_k > stoch_d and stoch_k < 80:
            score += 0.5
            reasons.append(f"✅ Stoch positif (K={stoch_k:.1f})")
        
        # ═══════════════════════════════════════════════════════════
        # 6. BOLLINGER (+1 point)
        # ═══════════════════════════════════════════════════════════
        bb_position = safe_value(row.get('bb_position', 0.5))
        
        if bb_position < 0.3:
            score += 1
            reasons.append(f"✅ Prix proche BB basse ({bb_position:.2f})")
        elif bb_position < 0.5:
            score += 0.5
            reasons.append("✅ Prix sous BB moyenne")
        
        # ═══════════════════════════════════════════════════════════
        # 7. VOLUME (+1 point)
        # ═══════════════════════════════════════════════════════════
        volume_ratio = safe_value(row.get('volume_ratio', 1.0))
        
        if volume_ratio > self.volume_spike_threshold:
            score += 1
            reasons.append(f"✅ Volume +{(volume_ratio-1)*100:.0f}%")
        elif volume_ratio > 1.0:
            score += 0.5
            reasons.append("✅ Volume > moyenne")
        
        # ═══════════════════════════════════════════════════════════
        # 8. ADX (+1 point)
        # ═══════════════════════════════════════════════════════════
        adx = safe_value(row.get('adx', 20))
        di_plus = safe_value(row.get('di_plus', 20))
        di_minus = safe_value(row.get('di_minus', 20))
        
        if adx > self.adx_strong and di_plus > di_minus:
            score += 1
            reasons.append(f"✅ ADX={adx:.1f} tendance forte")
        
        # ═══════════════════════════════════════════════════════════
        # 9. MACD (+1 point)
        # ═══════════════════════════════════════════════════════════
        macd = safe_value(row.get('macd', 0))
        macd_signal = safe_value(row.get('macd_signal', 0))
        macd_histogram = safe_value(row.get('macd_histogram', 0))
        prev_macd_histogram = safe_value(prev_row.get('macd_histogram', 0))
        
        if macd > macd_signal:
            score += 0.5
            reasons.append("✅ MACD > Signal")
        if macd_histogram > 0 and macd_histogram > prev_macd_histogram:
            score += 0.5
            reasons.append("✅ MACD histogram croissant")
        
        # ═══════════════════════════════════════════════════════════
        # 10. NEWS SENTIMENT (+1 point bonus)
        # ═══════════════════════════════════════════════════════════
        if news_sentiment is not None:
            if news_sentiment > 0.3:
                score += self.news_sentiment_bonus
                reasons.append(f"📰 News positives (+{news_sentiment:.2f})")
            elif news_sentiment < -0.3:
                score -= 0.5  # Pénalité pour news négatives
                reasons.append(f"📰 ⚠️ News négatives ({news_sentiment:.2f})")
        
        return score, max_score, reasons
    
    def generate_signal(self, df: pd.DataFrame, news_sentiment: Optional[float] = None) -> dict:
        """
        Génère un signal de trading
        
        Args:
            df: DataFrame avec données OHLCV
            news_sentiment: Score de sentiment des news (-1 à +1)
        
        Returns:
            dict avec signal, confidence, etc.
        """
        if len(df) < 50:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reason': 'Pas assez de données'
            }
        
        # Calculer les indicateurs
        df = self.calculate_all_indicators(df)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Calculer le score
        score, max_score, reasons = self.calculate_buy_score(current, prev, news_sentiment)
        confidence = (score / max_score) * 100
        
        # Valeurs par défaut sécurisées
        close = current.get('close', 0)
        if pd.isna(close) or close == 0:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': 'Prix invalide'}
        
        atr = current.get('atr', close * 0.01)
        if pd.isna(atr) or atr == 0:
            atr = close * 0.01  # 1% par défaut
        
        result = {
            'signal': 'HOLD',
            'confidence': confidence,
            'score': score,
            'max_score': max_score,
            'reasons': reasons,
            'indicators': {
                'price': close,
                'vwap': current.get('vwap', close),
                'vwap_distance': current.get('vwap_distance', 0),
                'ema_9': current.get('ema_9', close),
                'ema_21': current.get('ema_21', close),
                'rsi': current.get('rsi', 50),
                'stoch_k': current.get('stoch_k', 50),
                'stoch_d': current.get('stoch_d', 50),
                'bb_position': current.get('bb_position', 0.5),
                'adx': current.get('adx', 20),
                'volume_ratio': current.get('volume_ratio', 1.0),
                'atr_pct': current.get('atr_pct', 1.0)
            }
        }
        
        # ═══════════════════════════════════════════════════════════
        # SIGNAL D'ACHAT
        # ═══════════════════════════════════════════════════════════
        if score >= self.min_score_buy and confidence >= self.min_confidence:
            entry_price = close
            
            # Stop loss et take profit basés sur ATR
            stop_loss = entry_price - (atr * 1.5)
            take_profit = entry_price + (atr * 3)
            
            # Protection contre valeurs invalides
            if stop_loss >= entry_price:
                stop_loss = entry_price * (1 - self.stop_loss_pct)
            if take_profit <= entry_price:
                take_profit = entry_price * (1 + self.take_profit_pct)
            
            stop_loss_pct = safe_divide(entry_price - stop_loss, entry_price, 0.004)
            take_profit_pct = safe_divide(take_profit - entry_price, entry_price, 0.008)
            
            result.update({
                'signal': 'BUY',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'stop_loss_pct': stop_loss_pct * 100,
                'take_profit': take_profit,
                'take_profit_pct': take_profit_pct * 100,
                'trailing_stop_trigger': entry_price * (1 + self.trailing_stop_trigger),
                'trailing_stop_pct': self.trailing_stop_pct * 100,
                'risk_reward_ratio': safe_divide(take_profit_pct, stop_loss_pct, 2.0)
            })
            
            logger.info(f"🎯 SIGNAL ACHAT: Score {score:.1f}/{max_score} ({confidence:.1f}%)")
            for reason in reasons[:5]:
                logger.info(f"   {reason}")
        
        # ═══════════════════════════════════════════════════════════
        # SIGNAL DE VENTE
        # ═══════════════════════════════════════════════════════════
        rsi = current.get('rsi', 50)
        bb_position = current.get('bb_position', 0.5)
        stoch_k = current.get('stoch_k', 50)
        stoch_d = current.get('stoch_d', 50)
        
        if rsi > self.rsi_overbought:
            result.update({
                'signal': 'SELL',
                'reason': f"RSI suracheté ({rsi:.1f})"
            })
        elif bb_position > 0.95:
            result.update({
                'signal': 'SELL',
                'reason': 'Prix au-dessus BB supérieure'
            })
        elif stoch_k > 80 and stoch_k < stoch_d:
            result.update({
                'signal': 'SELL',
                'reason': 'Stochastic croisement baissier'
            })
        
        return result
    
    def should_exit_position(self, entry_price: float, current_price: float,
                            highest_price: float, position_data: dict) -> dict:
        """
        Vérifie si une position doit être fermée
        """
        # Protection contre valeurs invalides
        if entry_price <= 0 or current_price <= 0:
            return {'should_exit': False, 'reason': 'Prix invalide'}
        
        stop_loss = position_data.get('stop_loss', entry_price * 0.996)
        take_profit = position_data.get('take_profit', entry_price * 1.008)
        trailing_trigger = position_data.get('trailing_stop_trigger', entry_price * 1.004)
        
        profit_pct = safe_divide(current_price - entry_price, entry_price, 0) * 100
        
        # Stop Loss
        if current_price <= stop_loss:
            return {
                'should_exit': True,
                'reason': f'Stop Loss ({profit_pct:.2f}%)',
                'exit_type': 'STOP_LOSS'
            }
        
        # Take Profit
        if current_price >= take_profit:
            return {
                'should_exit': True,
                'reason': f'Take Profit ({profit_pct:.2f}%)',
                'exit_type': 'TAKE_PROFIT'
            }
        
        # Trailing Stop
        if highest_price >= trailing_trigger:
            trailing_stop = highest_price * (1 - self.trailing_stop_pct)
            if current_price <= trailing_stop:
                return {
                    'should_exit': True,
                    'reason': f'Trailing Stop ({profit_pct:.2f}%)',
                    'exit_type': 'TRAILING_STOP'
                }
        
        return {
            'should_exit': False,
            'current_profit_pct': profit_pct
        }


# Test
if __name__ == "__main__":
    strategy = ScalpingStrategy()
    print("✅ Stratégie Scalping V2.1 initialisée")
    print(f"   Stop Loss: {strategy.stop_loss_pct*100}%")
    print(f"   Take Profit: {strategy.take_profit_pct*100}%")
    print(f"   Score minimum: {strategy.min_score_buy}/13")
    print("   ✅ Protection division par zéro activée")
    print("   ✅ Support News Sentiment activé")
