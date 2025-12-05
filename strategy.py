"""
📊 STRATÉGIE DE TRADING
========================
Stratégie Long uniquement avec indicateurs techniques
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import ta
from alpaca_trade_api import TimeFrame

logger = logging.getLogger(__name__)


class TradingStrategy:
    """Stratégie de trading basée sur les indicateurs techniques"""
    
    def __init__(self, api):
        """Initialise la stratégie"""
        self.api = api
        
        # Paramètres de la stratégie
        self.rsi_oversold = 35          # RSI survente
        self.rsi_overbought = 70        # RSI surachat
        self.min_score = 5              # Score minimum pour acheter
        self.stop_loss_pct = 0.05       # Stop loss 5%
        self.take_profit_pct = 0.15     # Take profit 15%
        self.trailing_stop_pct = 0.03   # Trailing stop 3%
    
    def get_historical_data(self, symbol, days=100):
        """Récupère les données historiques"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            bars = self.api.get_bars(
                symbol,
                TimeFrame.Day,
                start.strftime('%Y-%m-%d'),
                end.strftime('%Y-%m-%d'),
                limit=days
            )
            
            # Convertir en DataFrame
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
    
    def calculate_indicators(self, df):
        """Calcule tous les indicateurs techniques"""
        if len(df) < 50:
            return df
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        # Moyennes mobiles
        df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
        df['sma_200'] = ta.trend.SMAIndicator(df['close'], window=200).sma_indicator()
        df['ema_20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_middle'] = bollinger.bollinger_mavg()
        df['bb_lower'] = bollinger.bollinger_lband()
        
        # ATR (Average True Range)
        df['atr'] = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], window=14
        ).average_true_range()
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(
            df['high'], df['low'], df['close'], window=14, smooth_window=3
        )
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        # Volume moyen
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def analyze(self, symbol):
        """Analyse un symbole et génère un signal"""
        result = {
            'symbol': symbol,
            'action': 'HOLD',
            'score': 0,
            'reasons': [],
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0
        }
        
        # Récupérer les données
        df = self.get_historical_data(symbol)
        
        if len(df) < 50:
            result['reasons'].append("Données insuffisantes")
            return result
        
        # Calculer les indicateurs
        df = self.calculate_indicators(df)
        
        # Dernière bougie et précédente
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0
        reasons = []
        
        # ===== CONDITIONS OBLIGATOIRES =====
        
        # 1. Tendance haussière long terme (Prix > SMA 200)
        if pd.notna(last['sma_200']) and last['close'] > last['sma_200']:
            score += 2
            reasons.append("Prix > SMA200")
        else:
            # Si pas en tendance haussière, pas de trade
            result['reasons'].append("Tendance baissière (Prix < SMA200)")
            return result
        
        # 2. Golden Cross (SMA 50 > SMA 200)
        if pd.notna(last['sma_50']) and pd.notna(last['sma_200']):
            if last['sma_50'] > last['sma_200']:
                score += 1
                reasons.append("Golden Cross actif")
        
        # ===== SIGNAUX DE DÉCLENCHEMENT =====
        
        # 3. RSI sort de survente
        if pd.notna(last['rsi']) and pd.notna(prev['rsi']):
            if prev['rsi'] < self.rsi_oversold and last['rsi'] > self.rsi_oversold:
                score += 2
                reasons.append(f"RSI sort de survente ({last['rsi']:.1f})")
            elif last['rsi'] < 40:
                score += 1
                reasons.append(f"RSI bas ({last['rsi']:.1f})")
        
        # 4. Croisement MACD haussier
        if pd.notna(last['macd_diff']) and pd.notna(prev['macd_diff']):
            if prev['macd_diff'] < 0 and last['macd_diff'] > 0:
                score += 3
                reasons.append("Croisement MACD haussier")
            elif last['macd_diff'] > 0:
                score += 1
                reasons.append("MACD positif")
        
        # 5. Prix proche de la bande de Bollinger basse
        if pd.notna(last['bb_lower']):
            if last['close'] < last['bb_lower'] * 1.02:
                score += 2
                reasons.append("Prix près de BB basse")
        
        # 6. Volume supérieur à la moyenne
        if pd.notna(last['volume_sma']):
            if last['volume'] > last['volume_sma'] * 1.5:
                score += 1
                reasons.append("Volume élevé")
        
        # 7. Stochastic en zone de survente
        if pd.notna(last['stoch_k']):
            if last['stoch_k'] < 25:
                score += 1
                reasons.append(f"Stochastic bas ({last['stoch_k']:.1f})")
        
        # 8. Prix au-dessus de EMA 20 (momentum court terme)
        if pd.notna(last['ema_20']):
            if last['close'] > last['ema_20']:
                score += 1
                reasons.append("Prix > EMA20")
        
        # ===== DÉCISION =====
        
        result['score'] = score
        result['reasons'] = reasons
        result['entry_price'] = last['close']
        
        if score >= self.min_score:
            result['action'] = 'BUY'
            
            # Calculer stop loss (basé sur ATR)
            atr = last['atr'] if pd.notna(last['atr']) else last['close'] * 0.02
            atr_stop = last['close'] - (2 * atr)
            pct_stop = last['close'] * (1 - self.stop_loss_pct)
            result['stop_loss'] = max(atr_stop, pct_stop)
            
            # Take profit
            result['take_profit'] = last['close'] * (1 + self.take_profit_pct)
        
        return result
    
    def get_current_price(self, symbol):
        """Récupère le prix actuel"""
        try:
            quote = self.api.get_latest_trade(symbol)
            return quote.price
        except Exception as e:
            logger.error(f"Erreur prix {symbol}: {e}")
            return None

