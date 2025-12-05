"""
🛡️ GESTIONNAIRE DE RISQUE CRYPTO - MODE PAPER TRADING AGRESSIF
"""

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
        self.max_daily_risk = 0.08
        self.max_positions = 5
        self.max_exposure = 0.80
        self.min_cash = 0.15
        self.max_consecutive_losses = 5
        self.cooldown_after_loss = 15
        self.daily_pnl = 0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.positions = {}
        self.allowed_cryptos = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        logger.info(f"🚀 RISK: {self.risk_per_trade*100}%/trade, {self.max_positions} positions max")
    
    def get_account_info(self) -> Dict:
        try:
            account = self.api.get_account()
            pv = float(account.portfolio_value)
            cash = float(account.cash)
            return {'portfolio_value': pv, 'cash': cash, 'buying_power': float(account.buying_power), 'cash_ratio': safe_divide(cash, pv, 0.5)}
        except Exception as e:
            logger.error(f"Erreur compte: {e}")
            return {'portfolio_value': 0, 'cash': 0, 'buying_power': 0, 'cash_ratio': 0.5}
    
    def get_positions(self) -> List[Dict]:
        try:
            positions = self.api.list_positions()
            return [{'symbol': p.symbol, 'qty': float(p.qty), 'entry_price': float(p.avg_entry_price), 'current_price': float(p.current_price), 'market_value': float(p.market_value), 'unrealized_pl': float(p.unrealized_pl), 'unrealized_plpc': float(p.unrealized_plpc) * 100} for p in positions if 'USD' in p.symbol]
        except:
            return []
    
    def can_trade(self, symbol: str, confidence: float) -> Dict:
        if symbol not in self.allowed_cryptos:
            return {'can_trade': False, 'reason': 'Non autorisé', 'max_position_value': 0}
        if self.consecutive_losses >= self.max_consecutive_losses:
            return {'can_trade': False, 'reason': 'Pause pertes', 'max_position_value': 0}
        account = self.get_account_info()
        pv = account['portfolio_value']
        if pv <= 0:
            return {'can_trade': False, 'reason': 'Erreur compte', 'max_position_value': 0}
        positions = self.get_positions()
        if len(positions) >= self.max_positions:
            return {'can_trade': False, 'reason': 'Max positions', 'max_position_value': 0}
        for p in positions:
            if symbol.replace('/', '') in p['symbol']:
                return {'can_trade': False, 'reason': 'Déjà en position', 'max_position_value': 0}
        max_pos = pv * self.max_per_crypto.get(symbol, 0.20)
        if confidence >= 85: max_pos *= 1.2
        return {'can_trade': True, 'reason': 'OK', 'max_position_value': max_pos}
    
    def calculate_position_size(self, symbol: str, price: float, stop_loss: float, confidence: float) -> Dict:
        check = self.can_trade(symbol, confidence)
        if not check['can_trade']:
            return {'qty': 0, 'reason': check['reason'], 'can_trade': False}
        account = self.get_account_info()
        risk = account['portfolio_value'] * self.risk_per_trade
        if confidence >= 90: risk *= 1.5
        elif confidence >= 80: risk *= 1.2
        stop_dist = abs(price - stop_loss)
        stop_pct = safe_divide(stop_dist, price, 0.02)
        pos_value = min(safe_divide(risk, stop_pct, 0), check['max_position_value'])
        qty = safe_divide(pos_value, price, 0)
        if symbol == 'BTC/USD': qty = round(qty, 4)
        elif symbol == 'ETH/USD': qty = round(qty, 3)
        else: qty = round(qty, 2)
        if qty <= 0:
            return {'qty': 0, 'reason': 'Quantité nulle', 'can_trade': False}
        return {'can_trade': True, 'qty': qty, 'position_value': qty * price, 'risk_pct': stop_pct * 100}
    
    def record_trade(self, pnl: float, trade_type: str = 'CLOSE'):
        self.daily_pnl += pnl
        self.daily_trades += 1
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()
        else:
            self.consecutive_losses = 0
            self.last_loss_time = None
    
    def reset_daily(self):
        self.daily_pnl = 0
        self.daily_trades = 0
    
    def get_risk_status(self) -> Dict:
        account = self.get_account_info()
        positions = self.get_positions()
        exposure = sum(p['market_value'] for p in positions)
        return {
            'portfolio_value': account['portfolio_value'],
            'cash': account['cash'],
            'cash_ratio': account['cash_ratio'] * 100,
            'num_positions': len(positions),
            'max_positions': self.max_positions,
            'exposure': exposure,
            'exposure_pct': safe_divide(exposure, account['portfolio_value'], 0) * 100,
            'unrealized_pnl': sum(p['unrealized_pl'] for p in positions),
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'consecutive_losses': self.consecutive_losses,
            'positions': positions
        }
    
    def check_all_exits(self, strategy) -> List[Dict]:
        exits = []
        for pos in self.get_positions():
            symbol = pos['symbol']
            entry = pos['entry_price']
            current = pos['current_price']
            highest = self.positions.get(symbol, {}).get('highest', current)
            if current > highest:
                if symbol not in self.positions: self.positions[symbol] = {}
                self.positions[symbol]['highest'] = current
                highest = current
            exit_check = strategy.should_exit(entry, current, highest, symbol, self.positions.get(symbol, {}))
            if exit_check.get('exit'):
                exits.append({'symbol': symbol, 'qty': pos['qty'], 'pnl': pos['unrealized_pl'], 'pnl_pct': pos['unrealized_plpc'], 'reason': exit_check.get('reason')})
        return exits


class CryptoVolatilityFilter:
    def __init__(self):
        self.max_hourly_move = 8.0
        self.max_daily_move = 20.0
    
    def is_safe_to_trade(self, df: pd.DataFrame) -> Dict:
        if len(df) < 2:
            return {'safe': False, 'reason': 'Données insuffisantes'}
        current = df['close'].iloc[-1]
        hourly = df['close'].iloc[-60] if len(df) >= 60 else df['close'].iloc[0]
        hourly_change = abs(safe_divide(current - hourly, hourly, 0)) * 100
        if hourly_change > self.max_hourly_move:
            return {'safe': False, 'reason': f"Volatilité: {hourly_change:.1f}%"}
        return {'safe': True, 'hourly_change': hourly_change}
