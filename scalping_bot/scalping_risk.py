"""
🛡️ GESTIONNAIRE DE RISQUE SCALPING V3.0
========================================
Version: 3.0 - Protection maximale
Date: Décembre 2024

AMÉLIORATIONS:
✅ Protection division par zéro complète
✅ Validation de toutes les entrées
✅ Limites de position par secteur
✅ Suivi détaillé des performances
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import pytz
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from shared_utils import safe_divide, get_sector, count_positions_by_sector
except ImportError:
    def safe_divide(n, d, default=0.0):
        try:
            if d == 0: return default
            r = n / d
            return default if np.isnan(r) or np.isinf(r) else r
        except: return default
    
    def get_sector(s): return 'unknown'
    def count_positions_by_sector(p): return {}

logger = logging.getLogger(__name__)
NY_TZ = pytz.timezone('America/New_York')


class ScalpingRiskManager:
    """
    Gestionnaire de Risque Scalping V3.0
    ====================================
    """
    
    def __init__(self, initial_capital: float = 100000):
        # Validation
        if initial_capital <= 0 or np.isnan(initial_capital):
            initial_capital = 100000
            logger.warning("Capital invalide → $100,000")
        
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # ═══════════════════════════════════════════════════════════
        # LIMITES DE RISQUE
        # ═══════════════════════════════════════════════════════════
        self.risk_per_trade = 0.005      # 0.5% par trade
        self.max_risk_trade = 0.01       # 1% max absolu
        
        self.max_daily_loss = 0.02       # -2% max/jour
        self.max_daily_profit = 0.05     # +5% objectif
        self.max_trades_day = 20         # 20 trades max/jour
        self.max_consecutive_loss = 5    # 5 pertes → stop
        
        self.max_position_pct = 0.10     # 10% max par position
        self.max_positions = 3           # 3 positions max
        self.max_exposure = 0.25         # 25% max exposé
        self.max_per_sector = 2          # 2 positions max/secteur
        
        # ═══════════════════════════════════════════════════════════
        # STATS JOURNALIÈRES
        # ═══════════════════════════════════════════════════════════
        self.daily = {
            'date': None,
            'start_capital': initial_capital,
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'consec_losses': 0,
            'pnl': 0.0,
            'pnl_pct': 0.0,
            'best': 0.0,
            'worst': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0
        }
        
        self.positions: Dict[str, Dict] = {}
        self.history: List[Dict] = []
        self.trading_ok = True
        self.halt_reason = None
        
        # Performance tracking
        self.all_time_stats = {
            'total_trades': 0,
            'total_wins': 0,
            'total_pnl': 0.0,
            'best_day': 0.0,
            'worst_day': 0.0
        }
    
    def _reset_daily(self):
        """Reset quotidien"""
        today = datetime.now(NY_TZ).date()
        
        if self.daily['date'] != today:
            # Sauvegarder stats du jour précédent
            if self.daily['date'] is not None:
                if self.daily['pnl'] > self.all_time_stats['best_day']:
                    self.all_time_stats['best_day'] = self.daily['pnl']
                if self.daily['pnl'] < self.all_time_stats['worst_day']:
                    self.all_time_stats['worst_day'] = self.daily['pnl']
            
            logger.info(f"📊 Nouveau jour: {today}")
            self.daily = {
                'date': today,
                'start_capital': self.current_capital,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'consec_losses': 0,
                'pnl': 0.0,
                'pnl_pct': 0.0,
                'best': 0.0,
                'worst': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0
            }
            self.trading_ok = True
            self.halt_reason = None
    
    def can_trade(self) -> tuple:
        """Vérifie si on peut trader"""
        self._reset_daily()
        
        # Perte max
        if self.daily['pnl_pct'] <= -self.max_daily_loss * 100:
            self.trading_ok = False
            self.halt_reason = f"Perte max ({self.daily['pnl_pct']:.2f}%)"
            return False, self.halt_reason
        
        # Max trades
        if self.daily['trades'] >= self.max_trades_day:
            self.trading_ok = False
            self.halt_reason = f"Max trades ({self.max_trades_day})"
            return False, self.halt_reason
        
        # Pertes consécutives
        if self.daily['consec_losses'] >= self.max_consecutive_loss:
            self.trading_ok = False
            self.halt_reason = f"Pertes consécutives ({self.max_consecutive_loss})"
            return False, self.halt_reason
        
        # Max positions
        if len(self.positions) >= self.max_positions:
            return False, f"Max positions ({self.max_positions})"
        
        return True, "OK"
    
    def check_sector_limit(self, symbol: str) -> tuple:
        """Vérifie la limite par secteur"""
        sector = get_sector(symbol)
        sector_count = 0
        
        for pos_symbol in self.positions.keys():
            if get_sector(pos_symbol) == sector:
                sector_count += 1
        
        if sector_count >= self.max_per_sector:
            return False, f"Max {self.max_per_sector} positions en {sector}"
        
        return True, "OK"
    
    def calculate_size(self, entry: float, stop: float, symbol: str, 
                      volatility: float = 1.0) -> Dict:
        """Calcule la taille de position"""
        # Validations
        if entry <= 0 or np.isnan(entry):
            return {'ok': False, 'reason': 'Prix invalide', 'shares': 0}
        if stop <= 0 or np.isnan(stop):
            return {'ok': False, 'reason': 'Stop invalide', 'shares': 0}
        if stop >= entry:
            return {'ok': False, 'reason': 'Stop >= Prix', 'shares': 0}
        
        # Vérifier trading autorisé
        ok, reason = self.can_trade()
        if not ok:
            return {'ok': False, 'reason': reason, 'shares': 0}
        
        # Vérifier limite secteur
        ok, reason = self.check_sector_limit(symbol)
        if not ok:
            return {'ok': False, 'reason': reason, 'shares': 0}
        
        # Risque par action
        risk_per_share = abs(entry - stop)
        if risk_per_share <= 0:
            return {'ok': False, 'reason': 'Risque/action = 0', 'shares': 0}
        
        # Ajuster risque selon volatilité
        risk_pct = self.risk_per_trade
        if volatility > 2.5:
            risk_pct *= 0.5
        elif volatility > 1.5:
            risk_pct *= 0.75
        
        # Montant à risquer
        risk_amount = self.current_capital * risk_pct
        
        # Nombre d'actions
        shares = int(safe_divide(risk_amount, risk_per_share, 0))
        if shares < 1:
            return {'ok': False, 'reason': 'Trop petit', 'shares': 0}
        
        # Vérifier taille max
        value = shares * entry
        max_value = self.current_capital * self.max_position_pct
        if value > max_value:
            shares = int(safe_divide(max_value, entry, 1))
            value = shares * entry
        
        # Vérifier exposition totale
        total_exposure = sum(p.get('value', 0) for p in self.positions.values())
        max_exposure = self.current_capital * self.max_exposure
        remaining = max_exposure - total_exposure
        
        if value > remaining:
            shares = int(safe_divide(remaining, entry, 0))
            if shares < 1:
                return {'ok': False, 'reason': 'Exposition max', 'shares': 0}
            value = shares * entry
        
        actual_risk = shares * risk_per_share
        
        return {
            'ok': True,
            'symbol': symbol,
            'shares': shares,
            'entry': entry,
            'stop': stop,
            'value': value,
            'value_pct': safe_divide(value, self.current_capital, 0) * 100,
            'risk': actual_risk,
            'risk_pct': safe_divide(actual_risk, self.current_capital, 0) * 100
        }
    
    def open_position(self, symbol: str, shares: int, entry: float,
                     stop: float, tp: float, data: Dict = None):
        """Enregistre une position"""
        if shares <= 0 or entry <= 0:
            logger.error(f"Position invalide: {symbol}")
            return
        
        self.positions[symbol] = {
            'symbol': symbol,
            'shares': shares,
            'entry': entry,
            'time': datetime.now(NY_TZ),
            'stop': stop,
            'tp': tp,
            'highest': entry,
            'value': shares * entry,
            'data': data or {}
        }
        
        self.daily['trades'] += 1
        self.all_time_stats['total_trades'] += 1
        
        logger.info(f"📈 OUVERT: {symbol} | {shares} @ ${entry:.2f}")
        logger.info(f"   Stop: ${stop:.2f} | TP: ${tp:.2f}")
    
    def close_position(self, symbol: str, exit_price: float, reason: str = '') -> Dict:
        """Ferme une position"""
        if symbol not in self.positions:
            return {'error': 'Position non trouvée'}
        
        pos = self.positions[symbol]
        shares = pos['shares']
        entry = pos['entry']
        
        if exit_price <= 0:
            return {'error': 'Prix invalide'}
        
        # PnL
        pnl = (exit_price - entry) * shares
        pnl_pct = safe_divide(exit_price - entry, entry, 0) * 100
        
        # Update stats
        self.daily['pnl'] += pnl
        self.daily['pnl_pct'] = safe_divide(self.daily['pnl'], self.daily['start_capital'], 0) * 100
        self.all_time_stats['total_pnl'] += pnl
        
        if pnl > 0:
            self.daily['wins'] += 1
            self.daily['consec_losses'] = 0
            self.all_time_stats['total_wins'] += 1
            if pnl > self.daily['best']:
                self.daily['best'] = pnl
        else:
            self.daily['losses'] += 1
            self.daily['consec_losses'] += 1
            if pnl < self.daily['worst']:
                self.daily['worst'] = pnl
        
        self.current_capital += pnl
        
        # Historique
        record = {
            'symbol': symbol,
            'entry': entry,
            'exit': exit_price,
            'shares': shares,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': pos['time'],
            'exit_time': datetime.now(NY_TZ),
            'reason': reason,
            'duration': datetime.now(NY_TZ) - pos['time']
        }
        self.history.append(record)
        
        del self.positions[symbol]
        
        emoji = "💰" if pnl > 0 else "📉"
        logger.info(f"{emoji} FERMÉ: {symbol} | ${pnl:+.2f} ({pnl_pct:+.2f}%)")
        
        return record
    
    def update_highest(self, symbol: str, price: float):
        """Update highest price pour trailing"""
        if symbol in self.positions and price > 0:
            if price > self.positions[symbol].get('highest', 0):
                self.positions[symbol]['highest'] = price
    
    def get_summary(self) -> Dict:
        """Résumé des stats"""
        total = self.daily['wins'] + self.daily['losses']
        win_rate = safe_divide(self.daily['wins'], total, 0) * 100
        
        return {
            'date': self.daily['date'],
            'pnl': self.daily['pnl'],
            'pnl_pct': self.daily['pnl_pct'],
            'trades': total,
            'wins': self.daily['wins'],
            'losses': self.daily['losses'],
            'win_rate': win_rate,
            'consec_losses': self.daily['consec_losses'],
            'best': self.daily['best'],
            'worst': self.daily['worst'],
            'capital': self.current_capital,
            'positions': len(self.positions),
            'trading_ok': self.trading_ok,
            'all_time_pnl': self.all_time_stats['total_pnl'],
            'all_time_trades': self.all_time_stats['total_trades'],
            'all_time_win_rate': safe_divide(self.all_time_stats['total_wins'], 
                                              self.all_time_stats['total_trades'], 0) * 100
        }
    
    def print_summary(self):
        """Affiche le résumé"""
        s = self.get_summary()
        logger.info("═" * 60)
        logger.info("📊 RÉSUMÉ SCALPING")
        logger.info("═" * 60)
        logger.info(f"   PnL Jour: ${s['pnl']:+.2f} ({s['pnl_pct']:+.2f}%)")
        logger.info(f"   Trades: {s['trades']} | Win: {s['wins']} | Loss: {s['losses']}")
        logger.info(f"   Win Rate: {s['win_rate']:.1f}%")
        logger.info(f"   Capital: ${s['capital']:,.2f}")
        logger.info(f"   All-Time PnL: ${s['all_time_pnl']:+.2f}")
        logger.info("═" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rm = ScalpingRiskManager(100000)
    
    # Tests
    r = rm.calculate_size(150, 149, 'AAPL', 1.5)
    print(f"✅ Normal: {r['shares']} actions, risque ${r.get('risk', 0):.2f}")
    
    r = rm.calculate_size(150, 150, 'TSLA', 1)
    print(f"✅ Stop=Prix: {r['reason']}")
    
    r = rm.calculate_size(0, 149, 'AMD', 1)
    print(f"✅ Prix=0: {r['reason']}")
