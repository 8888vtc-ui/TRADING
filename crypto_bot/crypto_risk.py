"""RISK MANAGER CRYPTO - AVEC SUPPORT SHORT"""
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
        self.base_risk_per_trade = 0.01
        self.max_positions = 5
        self.max_exposure = 0.80
        self.daily_pnl = 0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.positions = {}
        self.allowed_cryptos = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        self.unified_score = 50
        
        # Risk réduit pour SHORT (plus risqué)
        self.short_risk_multiplier = 0.7  # 30% moins de risque en short
        self.max_short_positions = 2  # Max 2 shorts simultanés
        self.current_shorts = 0
    
    def set_unified_score(self, score: int): 
        self.unified_score = score
    
    def get_risk_multiplier(self, is_short: bool = False) -> float:
        base_mult = 1.0
        if self.unified_score >= 90: base_mult = 3.0
        elif self.unified_score >= 80: base_mult = 2.0
        elif self.unified_score >= 70: base_mult = 1.5
        elif self.unified_score >= 55: base_mult = 1.0
        else: base_mult = 0.5
        
        # Réduire pour short
        if is_short:
            base_mult *= self.short_risk_multiplier
            logger.info(f"🔴 Risk mult SHORT: {base_mult:.2f}x (réduit)")
        
        return base_mult
    
    def get_account_info(self):
        try:
            a = self.api.get_account()
            pv = float(a.portfolio_value)
            return {
                'portfolio_value': pv, 
                'cash': float(a.cash), 
                'buying_power': float(a.buying_power), 
                'cash_ratio': safe_divide(float(a.cash), pv, 0.5),
                'shorting_enabled': getattr(a, 'shorting_enabled', True)
            }
        except: 
            return {'portfolio_value': 0, 'cash': 0, 'buying_power': 0, 'cash_ratio': 0.5, 'shorting_enabled': True}
    
    def get_positions(self):
        try: 
            positions = []
            for p in self.api.list_positions():
                if 'USD' in p.symbol:
                    qty = float(p.qty)
                    positions.append({
                        'symbol': p.symbol, 
                        'qty': qty,
                        'side': 'short' if qty < 0 else 'long',
                        'entry_price': float(p.avg_entry_price), 
                        'current_price': float(p.current_price), 
                        'market_value': abs(float(p.market_value)), 
                        'unrealized_pl': float(p.unrealized_pl), 
                        'unrealized_plpc': float(p.unrealized_plpc) * 100
                    })
            return positions
        except: 
            return []
    
    def can_trade(self, symbol, confidence, is_short: bool = False):
        if symbol not in self.allowed_cryptos: 
            return {'can_trade': False, 'reason': 'Non autorisé', 'max_position_value': 0}
        if self.consecutive_losses >= 5: 
            return {'can_trade': False, 'reason': 'Pause après pertes', 'max_position_value': 0}
        
        # Vérification spéciale SHORT
        if is_short:
            if self.unified_score > 55:  # Pas de short si marché OK
                return {'can_trade': False, 'reason': 'Score trop haut pour short', 'max_position_value': 0}
            if self.current_shorts >= self.max_short_positions:
                return {'can_trade': False, 'reason': 'Max shorts atteint', 'max_position_value': 0}
        else:
            if self.unified_score < 55:
                return {'can_trade': False, 'reason': f'Score bas ({self.unified_score})', 'max_position_value': 0}
        
        pv = self.get_account_info()['portfolio_value']
        if pv <= 0: 
            return {'can_trade': False, 'reason': 'Erreur compte', 'max_position_value': 0}
        
        positions = self.get_positions()
        if len(positions) >= self.max_positions: 
            return {'can_trade': False, 'reason': 'Max positions', 'max_position_value': 0}
        
        # Vérifier si déjà en position sur ce symbol
        for p in positions:
            if symbol.replace('/', '') in p['symbol']:
                # En short, on peut shorter si on est long (et vice versa pour hedge)
                if p['side'] == ('long' if is_short else 'short'):
                    continue  # Hedge autorisé
                return {'can_trade': False, 'reason': 'Déjà en position', 'max_position_value': 0}
        
        max_alloc = self.max_per_crypto.get(symbol, 0.20)
        if is_short:
            max_alloc *= 0.7  # 30% moins en short
        
        return {
            'can_trade': True, 
            'reason': 'OK', 
            'max_position_value': pv * max_alloc * self.get_risk_multiplier(is_short)
        }
    
    def calculate_position_size(self, symbol, price, stop_loss, confidence, is_short: bool = False):
        check = self.can_trade(symbol, confidence, is_short)
        if not check['can_trade']: 
            return {'qty': 0, 'reason': check['reason'], 'can_trade': False, 'side': 'short' if is_short else 'long'}
        
        pv = self.get_account_info()['portfolio_value']
        risk = pv * self.base_risk_per_trade * self.get_risk_multiplier(is_short)
        
        stop_pct = safe_divide(abs(price - stop_loss), price, 0.02)
        qty = safe_divide(min(safe_divide(risk, stop_pct, 0), check['max_position_value']), price, 0)
        
        if symbol == 'BTC/USD': qty = round(qty, 4)
        elif symbol == 'ETH/USD': qty = round(qty, 3)
        else: qty = round(qty, 2)
        
        if qty <= 0:
            return {'qty': 0, 'reason': 'Quantité nulle', 'can_trade': False, 'side': 'short' if is_short else 'long'}
        
        return {
            'can_trade': True, 
            'qty': qty, 
            'position_value': qty * price,
            'side': 'short' if is_short else 'long',
            'risk_multiplier': self.get_risk_multiplier(is_short)
        }
    
    def record_trade(self, pnl, side='long', trade_type='CLOSE'):
        self.daily_pnl += pnl
        self.daily_trades += 1
        
        if trade_type == 'OPEN':
            if side == 'short':
                self.current_shorts += 1
                logger.info(f"🔴 SHORT ouvert. Total shorts: {self.current_shorts}")
        elif trade_type == 'CLOSE':
            if side == 'short':
                self.current_shorts = max(0, self.current_shorts - 1)
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
    
    def reset_daily(self): 
        self.daily_pnl = 0
        self.daily_trades = 0
    
    def get_risk_status(self):
        a = self.get_account_info()
        p = self.get_positions()
        e = sum(x['market_value'] for x in p)
        longs = len([x for x in p if x['side'] == 'long'])
        shorts = len([x for x in p if x['side'] == 'short'])
        
        return {
            'portfolio_value': a['portfolio_value'], 
            'total_positions': len(p),
            'long_positions': longs,
            'short_positions': shorts,
            'exposure_pct': safe_divide(e, a['portfolio_value'], 0)*100, 
            'unified_score': self.unified_score,
            'risk_mult_long': f'{self.get_risk_multiplier(False):.1f}x',
            'risk_mult_short': f'{self.get_risk_multiplier(True):.1f}x',
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses
        }

class CryptoVolatilityFilter:
    def __init__(self): 
        self.max_hourly_move = 8.0
    
    def is_safe_to_trade(self, df, for_short: bool = False):
        if len(df) < 2: 
            return {'safe': False, 'reason': 'Données insuffisantes'}
        
        c = df['close'].iloc[-1]
        h = df['close'].iloc[-60] if len(df) >= 60 else df['close'].iloc[0]
        ch = safe_divide(c - h, h, 0) * 100  # Garde le signe pour direction
        abs_ch = abs(ch)
        
        # Pour SHORT, on VEUT de la volatilité baissière
        if for_short:
            if ch > 0:  # Marché monte
                return {'safe': False, 'reason': f"Marché haussier ({ch:+.1f}%) - pas de short"}
            if abs_ch < 2:  # Pas assez de mouvement
                return {'safe': False, 'reason': f"Volatilité insuffisante ({abs_ch:.1f}%)"}
            if abs_ch > 12:  # Trop volatile même pour short
                return {'safe': False, 'reason': f"Trop volatile ({abs_ch:.1f}%) - risque rebond"}
            return {'safe': True, 'reason': f"Short OK - baisse {ch:.1f}%"}
        
        # Pour LONG
        if abs_ch > 8:
            return {'safe': False, 'reason': f"Volatilité: {abs_ch:.1f}%"}
        return {'safe': True}
