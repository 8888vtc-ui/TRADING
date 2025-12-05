"""
🔴 PANIC SHORT STRATEGY - Profiter des chutes du marché
=======================================================

QUAND SHORTER?
- Fear & Greed < 20 (PANIQUE)
- Market Cap 24h < -3% (forte baisse)
- BTC en chute > 3%
- Volume en hausse (confirmation)

SIGNAUX SHORT:
- RSI > 70 puis cassure sous 70 (retournement)
- MACD cross baissier
- Prix sous EMA 21
- Volume spike sur baisse
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def safe_divide(n, d, default=0.0):
    try:
        if d == 0 or pd.isna(d) or np.isinf(d): return default
        r = n / d
        return default if pd.isna(r) or np.isinf(r) else r
    except: return default

class PanicShortStrategy:
    """Stratégie de SHORT en mode PANIC"""
    
    def __init__(self, api):
        self.api = api
        self.symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        
        # Seuils PANIC
        self.panic_fg_threshold = 20      # F&G < 20
        self.panic_mc_threshold = -3      # Market Cap < -3%
        self.min_drop_for_short = -2      # Crypto doit déjà baisser > 2%
        
        # Indicateurs SHORT
        self.rsi_overbought = 70          # RSI était > 70
        self.rsi_sell_signal = 65         # RSI casse sous 65 = vendre
        self.volume_spike_mult = 1.5      # Volume 1.5x average
        
        # Take Profit / Stop Loss
        self.short_take_profits = [
            {'drop_pct': 3, 'close_pct': 0.30},   # -3% → ferme 30%
            {'drop_pct': 5, 'close_pct': 0.30},   # -5% → ferme 30%
            {'drop_pct': 8, 'close_pct': 0.40},   # -8% → ferme tout
        ]
        self.short_stop_loss_pct = 2.5    # Stop si remonte de 2.5%
        
        # État
        self.panic_mode = False
        self.fear_greed = 50
        self.market_change = 0
    
    def update_market_conditions(self, fear_greed: int, market_change_24h: float):
        """Met à jour les conditions de marché"""
        self.fear_greed = fear_greed
        self.market_change = market_change_24h
        
        old_panic = self.panic_mode
        self.panic_mode = (fear_greed < self.panic_fg_threshold and market_change_24h < self.panic_mc_threshold)
        
        if self.panic_mode and not old_panic:
            logger.warning("=" * 60)
            logger.warning("🚨🚨🚨 MODE PANIC SHORT ACTIVÉ!")
            logger.warning(f"   Fear & Greed: {fear_greed} (< {self.panic_fg_threshold})")
            logger.warning(f"   Market Cap 24h: {market_change_24h:.1f}% (< {self.panic_mc_threshold}%)")
            logger.warning("   → Recherche d'opportunités SHORT")
            logger.warning("=" * 60)
    
    def get_historical_data(self, symbol: str, bars: int = 100) -> pd.DataFrame:
        """Récupère les données historiques"""
        try:
            from alpaca_trade_api.rest import TimeFrame
            from datetime import datetime, timedelta
            
            end = datetime.now()
            start = end - timedelta(hours=bars)
            
            data = self.api.get_crypto_bars(
                symbol.replace('/', ''),
                TimeFrame.Hour,
                start.strftime('%Y-%m-%d'),
                end.strftime('%Y-%m-%d')
            ).df
            
            if len(data) == 0:
                return pd.DataFrame()
            
            data = data.reset_index()
            return data
            
        except Exception as e:
            logger.error(f"Erreur données {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calcule les indicateurs pour SHORT"""
        if len(df) < 20:
            return {}
        
        close = df['close']
        volume = df['volume']
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = safe_divide(gain.iloc[-1], loss.iloc[-1], 1)
        rsi = 100 - (100 / (1 + rs))
        rsi_prev = 100 - (100 / (1 + safe_divide(gain.iloc[-2], loss.iloc[-2], 1)))
        
        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_hist = macd - signal
        
        # EMAs
        ema9 = close.ewm(span=9).mean().iloc[-1]
        ema21 = close.ewm(span=21).mean().iloc[-1]
        
        # Volume
        vol_sma = volume.rolling(20).mean().iloc[-1]
        vol_ratio = safe_divide(volume.iloc[-1], vol_sma, 1)
        
        # Momentum (changement %)
        price_change_1h = safe_divide(close.iloc[-1] - close.iloc[-2], close.iloc[-2], 0) * 100
        price_change_4h = safe_divide(close.iloc[-1] - close.iloc[-5], close.iloc[-5], 0) * 100 if len(close) > 5 else 0
        
        return {
            'close': close.iloc[-1],
            'rsi': rsi,
            'rsi_prev': rsi_prev,
            'macd': macd.iloc[-1],
            'macd_signal': signal.iloc[-1],
            'macd_hist': macd_hist.iloc[-1],
            'macd_hist_prev': macd_hist.iloc[-2] if len(macd_hist) > 1 else 0,
            'ema9': ema9,
            'ema21': ema21,
            'volume_ratio': vol_ratio,
            'price_change_1h': price_change_1h,
            'price_change_4h': price_change_4h,
        }
    
    def analyze_short_opportunity(self, symbol: str) -> Dict:
        """Analyse une opportunité de SHORT"""
        
        if not self.panic_mode:
            return {'action': 'NONE', 'reason': 'Pas en mode PANIC'}
        
        df = self.get_historical_data(symbol)
        if len(df) < 20:
            return {'action': 'NONE', 'reason': 'Données insuffisantes'}
        
        ind = self.calculate_indicators(df)
        if not ind:
            return {'action': 'NONE', 'reason': 'Erreur indicateurs'}
        
        score = 0
        signals = []
        
        # ═══════════════════════════════════════════════════════════
        # SIGNAUX SHORT
        # ═══════════════════════════════════════════════════════════
        
        # 1. RSI retournement (était haut, redescend)
        if ind['rsi_prev'] > self.rsi_overbought and ind['rsi'] < self.rsi_sell_signal:
            score += 3
            signals.append(f"✅ RSI retournement: {ind['rsi_prev']:.0f} → {ind['rsi']:.0f}")
        elif ind['rsi'] > 60:  # RSI encore élevé
            score += 1
            signals.append(f"⚠️ RSI élevé: {ind['rsi']:.0f}")
        
        # 2. MACD bearish cross
        if ind['macd'] < ind['macd_signal'] and ind['macd_hist'] < 0:
            if ind['macd_hist'] < ind['macd_hist_prev']:
                score += 3
                signals.append("✅ MACD cross baissier accélérant")
            else:
                score += 2
                signals.append("✅ MACD baissier")
        
        # 3. Prix sous EMAs
        if ind['close'] < ind['ema9'] < ind['ema21']:
            score += 3
            signals.append("✅ Prix sous EMA9 < EMA21 (baissier)")
        elif ind['close'] < ind['ema21']:
            score += 2
            signals.append("✅ Prix sous EMA21")
        
        # 4. Volume élevé (confirmation de la vente)
        if ind['volume_ratio'] >= self.volume_spike_mult:
            score += 2
            signals.append(f"✅ Volume spike: {ind['volume_ratio']:.1f}x")
        
        # 5. Momentum baissier
        if ind['price_change_4h'] < -3:
            score += 2
            signals.append(f"✅ Momentum 4h fort: {ind['price_change_4h']:.1f}%")
        elif ind['price_change_4h'] < -1:
            score += 1
            signals.append(f"⚠️ Momentum 4h: {ind['price_change_4h']:.1f}%")
        
        # 6. BONUS: Panique extrême
        if self.fear_greed < 15:
            score += 2
            signals.append(f"🔴 PANIQUE EXTRÊME F&G={self.fear_greed}")
        
        # ═══════════════════════════════════════════════════════════
        # DÉCISION
        # ═══════════════════════════════════════════════════════════
        
        max_score = 15
        confidence = (score / max_score) * 100
        
        # Calculer stop et target
        entry = ind['close']
        stop_loss = entry * (1 + self.short_stop_loss_pct / 100)  # Stop au-dessus
        take_profit = entry * (1 - 5 / 100)  # Target -5%
        
        result = {
            'symbol': symbol,
            'action': 'NONE',
            'score': score,
            'confidence': confidence,
            'signals': signals,
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'indicators': ind,
            'panic_mode': True,
            'fear_greed': self.fear_greed
        }
        
        if score >= 8:
            result['action'] = 'SHORT'
            result['strength'] = 'STRONG'
            logger.info(f"🔴🔴🔴 SIGNAL SHORT FORT: {symbol} | Score: {score}/{max_score}")
        elif score >= 6:
            result['action'] = 'SHORT'
            result['strength'] = 'MODERATE'
            logger.info(f"🔴🔴 SIGNAL SHORT MODÉRÉ: {symbol} | Score: {score}/{max_score}")
        elif score >= 4:
            result['action'] = 'SHORT'
            result['strength'] = 'WEAK'
            logger.info(f"🔴 SIGNAL SHORT FAIBLE: {symbol} | Score: {score}/{max_score}")
        
        for sig in signals:
            logger.info(f"   {sig}")
        
        return result
    
    def should_exit_short(self, entry_price: float, current_price: float, lowest_price: float) -> Dict:
        """Vérifie si on doit fermer le short"""
        
        # Profit depuis l'entrée (en short, profit = entry - current)
        profit_pct = safe_divide(entry_price - current_price, entry_price, 0) * 100
        
        # Drawup depuis le plus bas (rebond)
        drawup_pct = safe_divide(current_price - lowest_price, lowest_price, 0) * 100
        
        # Stop loss si remonte trop
        if profit_pct < -self.short_stop_loss_pct:
            return {
                'exit': True,
                'reason': f'🛑 STOP LOSS SHORT: +{-profit_pct:.1f}% (remontée)',
                'close_pct': 1.0
            }
        
        # Trailing stop: si rebondit de 2% depuis le plus bas
        if drawup_pct > 2 and profit_pct > 1:
            return {
                'exit': True,
                'reason': f'📈 Trailing stop SHORT: rebond {drawup_pct:.1f}% depuis bas',
                'close_pct': 1.0
            }
        
        # Take profits progressifs
        for tp in self.short_take_profits:
            if profit_pct >= tp['drop_pct']:
                return {
                    'exit': True,
                    'reason': f'💰 Take Profit SHORT: -{tp["drop_pct"]}% atteint',
                    'close_pct': tp['close_pct']
                }
        
        return {'exit': False}
    
    def scan_all_short_opportunities(self) -> list:
        """Scanne tous les symbols pour opportunités SHORT"""
        opportunities = []
        
        if not self.panic_mode:
            logger.info("📊 Pas en mode PANIC - pas de scan SHORT")
            return opportunities
        
        logger.info("🔴 SCAN SHORT EN COURS...")
        
        for symbol in self.symbols:
            result = self.analyze_short_opportunity(symbol)
            if result['action'] == 'SHORT':
                opportunities.append(result)
        
        # Trier par score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        if opportunities:
            logger.info(f"🔴 {len(opportunities)} opportunités SHORT trouvées!")
        else:
            logger.info("📊 Pas d'opportunité SHORT actuellement")
        
        return opportunities

