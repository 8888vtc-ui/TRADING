"""
🛡️ GESTIONNAIRE DE RISQUE CRYPTO - MODE PAPER TRADING AGRESSIF
==============================================================
⚠️ PARAMÈTRES AGRESSIFS POUR TEST EN PAPER TRADING

Risque par trade: 1-2% (au lieu de 0.5%)
Positions max: 5 (au lieu de 3)
Exposition max: 80% (au lieu de 60%)

À RÉDUIRE AVANT PASSAGE EN RÉEL!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


def safe_divide(n, d, default=0.0):
    """Division sécurisée"""
    try:
        if d == 0 or pd.isna(d) or np.isinf(d): return default
        r = n / d
        return default if pd.isna(r) or np.isinf(r) else r
    except: return default


class CryptoRiskManager:
    """
    🚀 RISK MANAGER - MODE PAPER TRADING AGRESSIF
    =============================================
    
    ⚠️ Ces paramètres sont pour TESTER les limites
    À réduire avant passage en réel!
    """
    
    def __init__(self, api):
        self.api = api
        
        logger.info("🚀 RISK MANAGER - MODE PAPER TRADING AGRESSIF")
        
        # ═══════════════════════════════════════════════════════════
        # 🔥 PARAMÈTRES AGRESSIFS (PAPER TRADING)
        # ═══════════════════════════════════════════════════════════
        
        # Allocation par crypto (plus généreuse)
        self.max_per_crypto = {
            'BTC/USD': 0.50,    # Max 50% en BTC
            'ETH/USD': 0.45,    # Max 45% en ETH
            'SOL/USD': 0.30,    # Max 30% en SOL
            'AVAX/USD': 0.20,   # Max 20% en AVAX
            'default': 0.20
        }
        
        # 🔥 Risque par trade AUGMENTÉ
        self.risk_per_trade = 0.015   # 1.5% du capital par trade (vs 0.5%)
        self.max_daily_risk = 0.08    # 8% perte max par jour (vs 2%)
        
        # 🔥 Limites AUGMENTÉES
        self.max_positions = 5        # 5 positions (vs 3)
        self.max_exposure = 0.80      # 80% exposé (vs 60%)
        self.min_cash = 0.15          # 15% cash min (vs 30%)
        
        # Protection (gardée pour éviter catastrophe)
        self.max_consecutive_losses = 5   # 5 pertes avant pause (vs 3)
        self.cooldown_after_loss = 15     # 15 min cooldown (vs 30)
        
        # Tracking
        self.daily_pnl = 0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.positions = {}
        
        # Cryptos autorisées
        self.allowed_cryptos = [
            'BTC/USD',
            'ETH/USD',
            'SOL/USD',
        ]
        
        logger.info(f"   Risque/trade: {self.risk_per_trade*100}%")
        logger.info(f"   Max positions: {self.max_positions}")
        logger.info(f"   Max exposition: {self.max_exposure*100}%")
    
    def get_account_info(self) -> Dict:
        """Récupère les infos du compte"""
        try:
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            cash = float(account.cash)
            
            return {
                'portfolio_value': portfolio_value,
                'cash': cash,
                'buying_power': float(account.buying_power),
                'cash_ratio': safe_divide(cash, portfolio_value, 0.5),
                'is_pattern_day_trader': account.pattern_day_trader
            }
        except Exception as e:
            logger.error(f"Erreur compte: {e}")
            return {'portfolio_value': 0, 'cash': 0, 'buying_power': 0}
    
    def get_positions(self) -> List[Dict]:
        """Récupère les positions crypto"""
        try:
            positions = self.api.list_positions()
            crypto_positions = []
            
            for pos in positions:
                symbol = pos.symbol
                if symbol in self.allowed_cryptos or '/USD' in symbol or 'USD' in symbol:
                    crypto_positions.append({
                        'symbol': symbol,
                        'qty': float(pos.qty),
                        'entry_price': float(pos.avg_entry_price),
                        'current_price': float(pos.current_price),
                        'market_value': float(pos.market_value),
                        'unrealized_pl': float(pos.unrealized_pl),
                        'unrealized_plpc': float(pos.unrealized_plpc) * 100
                    })
            
            return crypto_positions
        except Exception as e:
            logger.error(f"Erreur positions: {e}")
            return []
    
    def can_trade(self, symbol: str, signal_confidence: float) -> Dict:
        """Vérifie si on peut trader - MODE AGRESSIF"""
        result = {
            'can_trade': False,
            'reason': '',
            'max_position_value': 0
        }
        
        # Vérifier si crypto autorisée
        if symbol not in self.allowed_cryptos:
            result['reason'] = f"{symbol} non autorisée"
            return result
        
        # Vérifier pertes consécutives
        if self.consecutive_losses >= self.max_consecutive_losses:
            result['reason'] = f"Pause après {self.consecutive_losses} pertes"
            return result
        
        # Cooldown après perte
        if self.last_loss_time:
            minutes_since = (datetime.now() - self.last_loss_time).seconds / 60
            if minutes_since < self.cooldown_after_loss:
                result['reason'] = f"Cooldown: {self.cooldown_after_loss - minutes_since:.0f} min"
                return result
        
        # Vérifier perte journalière
        account = self.get_account_info()
        portfolio_value = account['portfolio_value']
        
        if portfolio_value <= 0:
            result['reason'] = "Erreur compte"
            return result
        
        daily_loss_pct = safe_divide(-self.daily_pnl, portfolio_value, 0)
        if daily_loss_pct >= self.max_daily_risk:
            result['reason'] = f"Limite perte jour ({daily_loss_pct*100:.1f}%)"
            return result
        
        # Vérifier cash minimum
        cash_ratio = account['cash_ratio']
        if cash_ratio < self.min_cash:
            result['reason'] = f"Cash insuffisant ({cash_ratio*100:.1f}%)"
            return result
        
        # Vérifier nombre de positions
        positions = self.get_positions()
        if len(positions) >= self.max_positions:
            result['reason'] = f"Max positions ({len(positions)}/{self.max_positions})"
            return result
        
        # Vérifier si déjà en position
        for pos in positions:
            if pos['symbol'] == symbol or symbol.replace('/', '') in pos['symbol']:
                result['reason'] = f"Déjà en position sur {symbol}"
                return result
        
        # Vérifier exposition totale
        total_exposure = sum(p['market_value'] for p in positions)
        exposure_ratio = safe_divide(total_exposure, portfolio_value, 0)
        if exposure_ratio >= self.max_exposure:
            result['reason'] = f"Exposition max ({exposure_ratio*100:.1f}%)"
            return result
        
        # Confiance minimum (abaissé pour paper)
        min_confidence = 55  # 55% au lieu de 65%
        if signal_confidence < min_confidence:
            result['reason'] = f"Confiance ({signal_confidence:.0f}% < {min_confidence}%)"
            return result
        
        # TOUT EST OK
        max_crypto = self.max_per_crypto.get(symbol, self.max_per_crypto['default'])
        max_position = portfolio_value * max_crypto
        
        # Bonus si haute confiance
        if signal_confidence >= 85:
            max_position *= 1.2
        
        remaining_exposure = (self.max_exposure * portfolio_value) - total_exposure
        max_position = min(max_position, remaining_exposure)
        
        result['can_trade'] = True
        result['max_position_value'] = max_position
        result['reason'] = f"OK - Max: ${max_position:.2f}"
        
        return result
    
    def calculate_position_size(self, symbol: str, price: float, 
                               stop_loss: float, confidence: float) -> Dict:
        """Calcule la taille de position - MODE AGRESSIF"""
        check = self.can_trade(symbol, confidence)
        
        if not check['can_trade']:
            return {'qty': 0, 'reason': check['reason'], 'can_trade': False}
        
        account = self.get_account_info()
        portfolio_value = account['portfolio_value']
        
        # 🔥 Risque augmenté en paper trading
        risk_amount = portfolio_value * self.risk_per_trade
        
        # Bonus risque si haute confiance
        if confidence >= 90:
            risk_amount *= 1.5
        elif confidence >= 80:
            risk_amount *= 1.2
        
        stop_distance = abs(price - stop_loss)
        stop_pct = safe_divide(stop_distance, price, 0.02)
        
        if stop_distance > 0:
            position_value = safe_divide(risk_amount, stop_pct, 0)
        else:
            position_value = risk_amount * 10
        
        position_value = min(position_value, check['max_position_value'])
        
        qty = safe_divide(position_value, price, 0)
        
        # Arrondir
        if symbol == 'BTC/USD':
            qty = round(qty, 4)
            min_qty = 0.0001
        elif symbol == 'ETH/USD':
            qty = round(qty, 3)
            min_qty = 0.001
        else:
            qty = round(qty, 2)
            min_qty = 0.01
        
        if qty < min_qty:
            return {'qty': 0, 'reason': f"Quantité trop faible", 'can_trade': False}
        
        actual_value = qty * price
        actual_risk = qty * stop_distance
        
        logger.info(f"📊 Position {symbol} (MODE AGRESSIF):")
        logger.info(f"   Quantité: {qty} (~${actual_value:.2f})")
        logger.info(f"   Risque: ${actual_risk:.2f} ({stop_pct*100:.2f}%)")
        
        return {
            'can_trade': True,
            'qty': qty,
            'position_value': actual_value,
            'risk_amount': actual_risk,
            'risk_pct': stop_pct * 100,
            'reason': f"Position: {qty} {symbol}"
        }
    
    def record_trade(self, pnl: float, trade_type: str = 'CLOSE'):
        """Enregistre un trade"""
        self.daily_pnl += pnl
        self.daily_trades += 1
        
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()
            logger.warning(f"❌ Perte #{self.consecutive_losses}: ${pnl:.2f}")
        else:
            self.consecutive_losses = 0
            self.last_loss_time = None
            logger.info(f"✅ Gain: +${pnl:.2f}")
    
    def reset_daily(self):
        """Reset journalier"""
        logger.info(f"📊 Résumé: PnL ${self.daily_pnl:.2f}, Trades: {self.daily_trades}")
        self.daily_pnl = 0
        self.daily_trades = 0
    
    def get_risk_status(self) -> Dict:
        """Statut complet"""
        account = self.get_account_info()
        positions = self.get_positions()
        
        total_exposure = sum(p['market_value'] for p in positions)
        total_pnl = sum(p['unrealized_pl'] for p in positions)
        
        return {
            'mode': '🔥 PAPER TRADING AGRESSIF',
            'portfolio_value': account['portfolio_value'],
            'cash': account['cash'],
            'cash_ratio': account['cash_ratio'] * 100,
            'num_positions': len(positions),
            'max_positions': self.max_positions,
            'exposure': total_exposure,
            'exposure_pct': safe_divide(total_exposure, account['portfolio_value'], 0) * 100,
            'max_exposure_pct': self.max_exposure * 100,
            'unrealized_pnl': total_pnl,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'consecutive_losses': self.consecutive_losses,
            'positions': positions
        }
    
    def check_all_exits(self, strategy) -> List[Dict]:
        """Vérifie sorties"""
        exits = []
        positions = self.get_positions()
        
        for pos in positions:
            symbol = pos['symbol']
            entry = pos['entry_price']
            current = pos['current_price']
            highest = self.positions.get(symbol, {}).get('highest', current)
            
            if current > highest:
                if symbol not in self.positions:
                    self.positions[symbol] = {}
                self.positions[symbol]['highest'] = current
                highest = current
            
            exit_check = strategy.should_exit(
                entry, current, highest, symbol,
                self.positions.get(symbol, {})
            )
            
            if exit_check.get('exit'):
                exits.append({
                    'symbol': symbol,
                    'qty': pos['qty'],
                    'entry': entry,
                    'current': current,
                    'pnl': pos['unrealized_pl'],
                    'pnl_pct': pos['unrealized_plpc'],
                    'reason': exit_check.get('reason'),
                    'type': exit_check.get('type')
                })
        
        return exits


class CryptoVolatilityFilter:
    """Filtre volatilité - MODE AGRESSIF"""
    
    def __init__(self):
        # Plus permissif en paper trading
        self.max_hourly_move = 8.0    # 8% (vs 5%)
        self.max_daily_move = 20.0    # 20% (vs 15%)
    
    def is_safe_to_trade(self, df: pd.DataFrame) -> Dict:
        """Vérifie volatilité - plus permissif en paper"""
        if len(df) < 2:
            return {'safe': False, 'reason': 'Données insuffisantes'}
        
        current = df['close'].iloc[-1]
        hourly = df['close'].iloc[-60] if len(df) >= 60 else df['close'].iloc[0]
        daily = df['close'].iloc[-1440] if len(df) >= 1440 else df['close'].iloc[0]
        
        hourly_change = abs(safe_divide(current - hourly, hourly, 0)) * 100
        daily_change = abs(safe_divide(current - daily, daily, 0)) * 100
        
        if hourly_change > self.max_hourly_move:
            return {'safe': False, 'reason': f"Volatilité horaire: {hourly_change:.1f}%"}
        
        if daily_change > self.max_daily_move:
            return {'safe': False, 'reason': f"Volatilité journalière: {daily_change:.1f}%"}
        
        return {'safe': True, 'hourly_change': hourly_change, 'daily_change': daily_change}


# ═══════════════════════════════════════════════════════════════════
# 📋 PARAMÈTRES CONSERVATEURS (POUR PASSAGE EN RÉEL)
# ═══════════════════════════════════════════════════════════════════
"""
QUAND TU PASSES EN RÉEL, MODIFIER:

self.risk_per_trade = 0.005   # 0.5%
self.max_daily_risk = 0.02    # 2%
self.max_positions = 3
self.max_exposure = 0.60
self.min_cash = 0.30
self.max_consecutive_losses = 3
"""


if __name__ == "__main__":
    print("🚀 Risk Manager - MODE PAPER TRADING AGRESSIF")
    print(f"   Risque par trade: 1.5%")
    print(f"   Perte max journalière: 8%")
    print(f"   Max positions: 5")
    print(f"   Exposition max: 80%")
