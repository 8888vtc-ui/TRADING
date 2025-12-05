"""
🛡️ CRYPTO RISK MANAGER V2.0
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def safe_divide(n, d, default=0.0):
    try:
        if d == 0 or pd.isna(d) or np.isinf(d): return default
        r = n / d
        return default if pd.isna(r) or np.isinf(r) else r
    except: return default

class CryptoRiskManager:
    def __init__(self, api):
        self.api = api
        self.max_per_crypto = {'BTC/USD': 0.50, 'ETH/USD': 0.45, 'SOL/USD': 0.30, 'default': 0.20}
        self.base_risk_per_trade = 0.01
        self.max_positions = 5
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.positions = {}
        self.allowed_cryptos = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        self.unified_score = 50
    
    def set_unified_score(self, score: int): self.unified_score = max(0, min(100, score))
    
    def get_risk_multiplier(self, is_short=False):
        if self.unified_score >= 90: base = 3.0
        elif self.unified_score >= 80: base = 2.0
        elif self.unified_score >= 70: base = 1.5
        elif self.unified_score >= 55: base = 1.0
        else: base = 0.5
        return base * 0.7 if is_short else base
    
    def get_account_info(self):
        try:
            a = self.api.get_account()
            return {'portfolio_value': float(a.portfolio_value), 'cash': float(a.cash), 'buying_power': float(a.buying_power)}
        except: return {'portfolio_value': 0, 'cash': 0, 'buying_power': 0}
    
    def get_positions(self):
        try:
            return [{'symbol': p.symbol, 'qty': float(p.qty), 'side': 'short' if float(p.qty) < 0 else 'long', 'entry_price': float(p.avg_entry_price), 'current_price': float(p.current_price), 'market_value': abs(float(p.market_value)), 'unrealized_pl': float(p.unrealized_pl), 'unrealized_plpc': float(p.unrealized_plpc) * 100} for p in self.api.list_positions() if 'USD' in p.symbol]
        except: return []
    
    def can_trade(self, symbol, confidence, is_short=False):
        if symbol not in self.allowed_cryptos: return {'can_trade': False, 'reason': 'Non autorisé', 'max_position_value': 0}
        if self.consecutive_losses >= 5: return {'can_trade': False, 'reason': 'Pause', 'max_position_value': 0}
        pv = self.get_account_info()['portfolio_value']
        if pv <= 0: return {'can_trade': False, 'reason': 'Erreur', 'max_position_value': 0}
        if len(self.get_positions()) >= self.max_positions: return {'can_trade': False, 'reason': 'Max', 'max_position_value': 0}
        max_alloc = self.max_per_crypto.get(symbol, 0.20) * (0.7 if is_short else 1)
        return {'can_trade': True, 'reason': 'OK', 'max_position_value': pv * max_alloc * self.get_risk_multiplier(is_short)}
    
    def calculate_position_size(self, symbol, price, stop_loss, confidence, is_short=False):
        check = self.can_trade(symbol, confidence, is_short)
        if not check['can_trade']: return {'qty': 0, 'reason': check['reason'], 'can_trade': False}
        pv = self.get_account_info()['portfolio_value']
        risk = pv * self.base_risk_per_trade * self.get_risk_multiplier(is_short)
        stop_pct = safe_divide(abs(price - stop_loss), price, 0.02)
        qty = safe_divide(min(safe_divide(risk, stop_pct, 0), check['max_position_value']), price, 0)
        qty = round(qty, 4) if 'BTC' in symbol else round(qty, 3) if 'ETH' in symbol else round(qty, 2)
        return {'can_trade': True, 'qty': qty, 'position_value': qty * price} if qty > 0 else {'qty': 0, 'can_trade': False}
    
    def record_trade(self, pnl):
        self.daily_pnl += pnl
        if pnl < 0: self.consecutive_losses += 1
        else: self.consecutive_losses = 0
    
    def reset_daily(self): self.daily_pnl = 0

class CryptoVolatilityFilter:
    def is_safe_to_trade(self, df, for_short=False):
        if len(df) < 2: return {'safe': False}
        ch = safe_divide(df['close'].iloc[-1] - df['close'].iloc[0], df['close'].iloc[0], 0) * 100
        if for_short: return {'safe': ch < 0 and 2 < abs(ch) < 12}
        return {'safe': abs(ch) < 8}
