"""RISK MANAGER CRYPTO - PAPER TRADING AGRESSIF"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
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
        self.risk_per_trade = 0.015
        self.max_positions = 5
        self.max_exposure = 0.80
        self.daily_pnl = 0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.positions = {}
        self.allowed_cryptos = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        self.market_score = 50  # Score Market Intelligence
    
    def set_market_score(self, score: int):
        """Met à jour le score du marché"""
        self.market_score = score
    
    def get_account_info(self):
        try:
            a = self.api.get_account()
            pv = float(a.portfolio_value)
            return {'portfolio_value': pv, 'cash': float(a.cash), 'buying_power': float(a.buying_power), 'cash_ratio': safe_divide(float(a.cash), pv, 0.5)}
        except: return {'portfolio_value': 0, 'cash': 0, 'buying_power': 0, 'cash_ratio': 0.5}
    
    def get_positions(self):
        try:
            return [{'symbol': p.symbol, 'qty': float(p.qty), 'entry_price': float(p.avg_entry_price), 'current_price': float(p.current_price), 'market_value': float(p.market_value), 'unrealized_pl': float(p.unrealized_pl), 'unrealized_plpc': float(p.unrealized_plpc) * 100} for p in self.api.list_positions() if 'USD' in p.symbol]
        except: return []
    
    def can_trade(self, symbol, confidence):
        if symbol not in self.allowed_cryptos: return {'can_trade': False, 'reason': 'Non autorisé', 'max_position_value': 0}
        if self.consecutive_losses >= 5: return {'can_trade': False, 'reason': 'Pause', 'max_position_value': 0}
        pv = self.get_account_info()['portfolio_value']
        if pv <= 0: return {'can_trade': False, 'reason': 'Erreur', 'max_position_value': 0}
        positions = self.get_positions()
        if len(positions) >= self.max_positions: return {'can_trade': False, 'reason': 'Max', 'max_position_value': 0}
        for p in positions:
            if symbol.replace('/', '') in p['symbol']: return {'can_trade': False, 'reason': 'Déjà', 'max_position_value': 0}
        
        # BOOST si marché super
        market_mult = 1.3 if self.market_score >= 80 else 1.2 if self.market_score >= 70 else 1.0
        max_pos = pv * self.max_per_crypto.get(symbol, 0.20) * (1.2 if confidence >= 85 else 1) * market_mult
        return {'can_trade': True, 'reason': 'OK', 'max_position_value': max_pos}
    
    def calculate_position_size(self, symbol, price, stop_loss, confidence):
        check = self.can_trade(symbol, confidence)
        if not check['can_trade']: return {'qty': 0, 'reason': check['reason'], 'can_trade': False}
        
        # BOOST risque si marché super
        market_mult = 1.5 if self.market_score >= 80 else 1.2 if self.market_score >= 70 else 1.0
        risk = self.get_account_info()['portfolio_value'] * self.risk_per_trade * (1.5 if confidence >= 90 else 1.2 if confidence >= 80 else 1) * market_mult
        
        stop_pct = safe_divide(abs(price - stop_loss), price, 0.02)
        qty = safe_divide(min(safe_divide(risk, stop_pct, 0), check['max_position_value']), price, 0)
        if symbol == 'BTC/USD': qty = round(qty, 4)
        elif symbol == 'ETH/USD': qty = round(qty, 3)
        else: qty = round(qty, 2)
        return {'can_trade': True, 'qty': qty, 'position_value': qty * price} if qty > 0 else {'qty': 0, 'can_trade': False}
    
    def record_trade(self, pnl, t='CLOSE'):
        self.daily_pnl += pnl
        self.daily_trades += 1
        if pnl < 0: self.consecutive_losses += 1; self.last_loss_time = datetime.now()
        else: self.consecutive_losses = 0
    
    def reset_daily(self): self.daily_pnl = 0; self.daily_trades = 0
    
    def get_risk_status(self):
        a = self.get_account_info()
        p = self.get_positions()
        e = sum(x['market_value'] for x in p)
        return {'portfolio_value': a['portfolio_value'], 'cash': a['cash'], 'cash_ratio': a['cash_ratio']*100, 'num_positions': len(p), 'max_positions': self.max_positions, 'exposure': e, 'exposure_pct': safe_divide(e, a['portfolio_value'], 0)*100, 'unrealized_pnl': sum(x['unrealized_pl'] for x in p), 'daily_pnl': self.daily_pnl, 'daily_trades': self.daily_trades, 'consecutive_losses': self.consecutive_losses, 'positions': p, 'market_score': self.market_score}
    
    def check_all_exits(self, strategy):
        exits = []
        for pos in self.get_positions():
            s, e, c = pos['symbol'], pos['entry_price'], pos['current_price']
            h = self.positions.get(s, {}).get('highest', c)
            if c > h: self.positions.setdefault(s, {})['highest'] = c; h = c
            x = strategy.should_exit(e, c, h, s, self.positions.get(s, {}))
            if x.get('exit'): exits.append({'symbol': s, 'qty': pos['qty'], 'pnl': pos['unrealized_pl'], 'pnl_pct': pos['unrealized_plpc'], 'reason': x.get('reason')})
        return exits

class CryptoVolatilityFilter:
    def __init__(self): self.max_hourly_move = 8.0
    def is_safe_to_trade(self, df):
        if len(df) < 2: return {'safe': False, 'reason': 'Données insuffisantes'}
        c = df['close'].iloc[-1]
        h = df['close'].iloc[-60] if len(df) >= 60 else df['close'].iloc[0]
        ch = abs(safe_divide(c - h, h, 0)) * 100
        return {'safe': False, 'reason': f"Volatilité: {ch:.1f}%"} if ch > 8 else {'safe': True}
