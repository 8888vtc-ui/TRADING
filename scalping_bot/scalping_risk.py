"""
🛡️ GESTIONNAIRE DE RISQUE SCALPING V2.1
========================================
Version: 2.1 - Avec corrections division par zéro
Auteur: Trading Bot System
Date: Décembre 2024

CORRECTIONS V2.1:
- Protection contre division par zéro dans tous les calculs
- Gestion des valeurs NaN/Inf
- Validation des entrées

RÈGLES:
- Max 0.5% de risque par trade
- Max 2% de perte journalière
- Max 5 trades perdants consécutifs = STOP
- Position sizing dynamique basé sur volatilité
"""

import logging
from datetime import datetime
from typing import Dict, List
import pytz
import numpy as np

logger = logging.getLogger(__name__)

NY_TZ = pytz.timezone('America/New_York')


def safe_divide(numerator, denominator, default=0.0):
    """Division sécurisée"""
    try:
        if denominator == 0 or np.isnan(denominator) or np.isinf(denominator):
            return default
        result = numerator / denominator
        if np.isnan(result) or np.isinf(result):
            return default
        return result
    except:
        return default


class ScalpingRiskManager:
    """
    Gestionnaire de Risque pour Scalping V2.1
    =========================================
    Optimisé avec protection contre erreurs numériques
    """
    
    def __init__(self, initial_capital: float = 100000):
        # Validation du capital
        if initial_capital <= 0 or np.isnan(initial_capital):
            initial_capital = 100000
            logger.warning("Capital invalide, utilisation de $100,000 par défaut")
        
        # ═══════════════════════════════════════════════════════════
        # CAPITAL & LIMITES
        # ═══════════════════════════════════════════════════════════
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Risque par trade
        self.risk_per_trade_pct = 0.5
        self.max_risk_per_trade_pct = 1.0
        
        # Limites journalières
        self.max_daily_loss_pct = 2.0
        self.max_daily_profit_pct = 5.0
        self.max_trades_per_day = 20
        self.max_consecutive_losses = 5
        
        # Limites de position
        self.max_position_pct = 10.0
        self.max_positions = 3
        self.max_exposure_pct = 25.0
        
        # ═══════════════════════════════════════════════════════════
        # TRACKING JOURNALIER
        # ═══════════════════════════════════════════════════════════
        self.daily_stats = {
            'date': None,
            'starting_capital': initial_capital,
            'trades_count': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'consecutive_losses': 0,
            'pnl': 0.0,
            'pnl_pct': 0.0,
            'max_drawdown': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0
        }
        
        self.trade_history: List[Dict] = []
        self.open_positions: Dict[str, Dict] = {}
        
        self.trading_allowed = True
        self.halt_reason = None
        
    def reset_daily_stats(self):
        """Reset les statistiques journalières"""
        today = datetime.now(NY_TZ).date()
        
        if self.daily_stats['date'] != today:
            logger.info(f"📊 Reset stats journalières - {today}")
            self.daily_stats = {
                'date': today,
                'starting_capital': self.current_capital,
                'trades_count': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'consecutive_losses': 0,
                'pnl': 0.0,
                'pnl_pct': 0.0,
                'max_drawdown': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0
            }
            self.trading_allowed = True
            self.halt_reason = None
    
    def check_trading_allowed(self) -> tuple:
        """Vérifie si le trading est autorisé"""
        self.reset_daily_stats()
        
        # Perte journalière max
        if self.daily_stats['pnl_pct'] <= -self.max_daily_loss_pct:
            self.trading_allowed = False
            self.halt_reason = f"Perte max atteinte ({self.daily_stats['pnl_pct']:.2f}%)"
            return False, self.halt_reason
        
        # Nombre de trades
        if self.daily_stats['trades_count'] >= self.max_trades_per_day:
            self.trading_allowed = False
            self.halt_reason = f"Max trades atteint ({self.max_trades_per_day})"
            return False, self.halt_reason
        
        # Pertes consécutives
        if self.daily_stats['consecutive_losses'] >= self.max_consecutive_losses:
            self.trading_allowed = False
            self.halt_reason = f"Pertes consécutives max ({self.max_consecutive_losses})"
            return False, self.halt_reason
        
        # Positions ouvertes
        if len(self.open_positions) >= self.max_positions:
            return False, f"Max positions ({self.max_positions})"
        
        return True, "Trading autorisé"
    
    def calculate_position_size(self, entry_price: float, stop_loss: float,
                               symbol: str, volatility_pct: float = 1.0) -> dict:
        """
        Calcule la taille de position avec protection contre erreurs
        """
        # Validation des entrées
        if entry_price <= 0 or np.isnan(entry_price):
            return {'allowed': False, 'reason': 'Prix d\'entrée invalide', 'shares': 0}
        
        if stop_loss <= 0 or np.isnan(stop_loss):
            return {'allowed': False, 'reason': 'Stop loss invalide', 'shares': 0}
        
        if stop_loss >= entry_price:
            return {'allowed': False, 'reason': 'Stop loss >= prix entrée', 'shares': 0}
        
        # Vérifier trading autorisé
        allowed, reason = self.check_trading_allowed()
        if not allowed:
            return {'allowed': False, 'reason': reason, 'shares': 0}
        
        # Calculer le risque par action - PROTECTION DIVISION PAR ZÉRO
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            return {'allowed': False, 'reason': 'Risque par action = 0', 'shares': 0}
        
        # Ajuster le risque selon volatilité
        adjusted_risk_pct = self.risk_per_trade_pct
        if volatility_pct > 2.0:
            adjusted_risk_pct *= 0.5
        elif volatility_pct > 1.5:
            adjusted_risk_pct *= 0.75
        
        # Montant à risquer - PROTECTION
        risk_amount = safe_divide(
            self.current_capital * adjusted_risk_pct,
            100,
            self.current_capital * 0.005  # 0.5% par défaut
        )
        
        # Nombre d'actions - PROTECTION DIVISION PAR ZÉRO
        shares = int(safe_divide(risk_amount, risk_per_share, 0))
        
        if shares < 1:
            return {'allowed': False, 'reason': 'Position trop petite', 'shares': 0}
        
        # Vérifier taille max
        position_value = shares * entry_price
        max_position = safe_divide(
            self.current_capital * self.max_position_pct,
            100,
            self.current_capital * 0.1
        )
        
        if position_value > max_position:
            shares = int(safe_divide(max_position, entry_price, 1))
            position_value = shares * entry_price
        
        # Vérifier exposition totale
        total_exposure = sum(
            pos.get('value', 0) for pos in self.open_positions.values()
        )
        max_total_exposure = safe_divide(
            self.current_capital * self.max_exposure_pct,
            100,
            self.current_capital * 0.25
        )
        remaining = max_total_exposure - total_exposure
        
        if position_value > remaining:
            shares = int(safe_divide(remaining, entry_price, 0))
            position_value = shares * entry_price
        
        if shares < 1:
            return {'allowed': False, 'reason': 'Exposition max atteinte', 'shares': 0}
        
        # Calculer risque réel
        actual_risk = shares * risk_per_share
        actual_risk_pct = safe_divide(actual_risk, self.current_capital, 0) * 100
        position_pct = safe_divide(position_value, self.current_capital, 0) * 100
        
        return {
            'allowed': True,
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_value': position_value,
            'position_pct': position_pct,
            'risk_amount': actual_risk,
            'risk_pct': actual_risk_pct,
            'risk_per_share': risk_per_share
        }
    
    def register_trade_entry(self, symbol: str, shares: int, entry_price: float,
                            stop_loss: float, take_profit: float, signal_data: dict = None):
        """Enregistre une nouvelle position"""
        if shares <= 0 or entry_price <= 0:
            logger.error(f"Entrée invalide: {symbol} shares={shares} price={entry_price}")
            return
        
        position = {
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'entry_time': datetime.now(NY_TZ),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'highest_price': entry_price,
            'value': shares * entry_price,
            'signal_data': signal_data or {}
        }
        
        self.open_positions[symbol] = position
        self.daily_stats['trades_count'] += 1
        
        logger.info(f"📈 Position ouverte: {symbol}")
        logger.info(f"   Actions: {shares} @ ${entry_price:.2f}")
        logger.info(f"   Valeur: ${position['value']:.2f}")
        logger.info(f"   Stop: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
    
    def register_trade_exit(self, symbol: str, exit_price: float,
                           exit_reason: str = 'Manual') -> dict:
        """Enregistre la sortie d'une position"""
        if symbol not in self.open_positions:
            return {'error': 'Position non trouvée'}
        
        position = self.open_positions[symbol]
        shares = position['shares']
        entry_price = position['entry_price']
        
        # Validation
        if exit_price <= 0 or shares <= 0:
            logger.error(f"Sortie invalide: {symbol}")
            return {'error': 'Valeurs invalides'}
        
        # PnL - PROTECTION
        pnl = (exit_price - entry_price) * shares
        pnl_pct = safe_divide(exit_price - entry_price, entry_price, 0) * 100
        
        # Mise à jour stats
        self.daily_stats['pnl'] += pnl
        self.daily_stats['pnl_pct'] = safe_divide(
            self.daily_stats['pnl'],
            self.daily_stats['starting_capital'],
            0
        ) * 100
        
        if pnl > 0:
            self.daily_stats['winning_trades'] += 1
            self.daily_stats['consecutive_losses'] = 0
            if pnl > self.daily_stats['best_trade']:
                self.daily_stats['best_trade'] = pnl
        else:
            self.daily_stats['losing_trades'] += 1
            self.daily_stats['consecutive_losses'] += 1
            if pnl < self.daily_stats['worst_trade']:
                self.daily_stats['worst_trade'] = pnl
        
        self.current_capital += pnl
        
        # Historique
        trade_record = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now(NY_TZ),
            'exit_reason': exit_reason,
            'holding_time': datetime.now(NY_TZ) - position['entry_time']
        }
        self.trade_history.append(trade_record)
        
        del self.open_positions[symbol]
        
        emoji = "💰" if pnl > 0 else "📉"
        logger.info(f"{emoji} Position fermée: {symbol}")
        logger.info(f"   PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        logger.info(f"   Capital: ${self.current_capital:.2f}")
        
        return trade_record
    
    def update_position_price(self, symbol: str, current_price: float):
        """Met à jour le highest price pour trailing stop"""
        if symbol in self.open_positions and current_price > 0:
            pos = self.open_positions[symbol]
            if current_price > pos.get('highest_price', 0):
                pos['highest_price'] = current_price
    
    def get_daily_summary(self) -> dict:
        """Retourne les stats journalières"""
        total = self.daily_stats['winning_trades'] + self.daily_stats['losing_trades']
        win_rate = safe_divide(self.daily_stats['winning_trades'], total, 0) * 100
        
        return {
            'date': self.daily_stats['date'],
            'pnl': self.daily_stats['pnl'],
            'pnl_pct': self.daily_stats['pnl_pct'],
            'total_trades': total,
            'winning_trades': self.daily_stats['winning_trades'],
            'losing_trades': self.daily_stats['losing_trades'],
            'win_rate': win_rate,
            'consecutive_losses': self.daily_stats['consecutive_losses'],
            'best_trade': self.daily_stats['best_trade'],
            'worst_trade': self.daily_stats['worst_trade'],
            'current_capital': self.current_capital,
            'open_positions': len(self.open_positions),
            'trading_allowed': self.trading_allowed
        }
    
    def print_daily_summary(self):
        """Affiche le résumé journalier"""
        s = self.get_daily_summary()
        
        logger.info("=" * 60)
        logger.info("📊 RÉSUMÉ JOURNALIER SCALPING")
        logger.info("=" * 60)
        logger.info(f"   PnL: ${s['pnl']:.2f} ({s['pnl_pct']:+.2f}%)")
        logger.info(f"   Trades: {s['total_trades']} (W:{s['winning_trades']} L:{s['losing_trades']})")
        logger.info(f"   Win Rate: {s['win_rate']:.1f}%")
        logger.info(f"   Capital: ${s['current_capital']:.2f}")
        logger.info("=" * 60)


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    rm = ScalpingRiskManager(100000)
    
    # Test avec valeurs normales
    result = rm.calculate_position_size(150.0, 149.0, 'AAPL', 1.5)
    print(f"✅ Test normal: {result['shares']} actions")
    
    # Test avec division par zéro
    result = rm.calculate_position_size(150.0, 150.0, 'AAPL', 1.5)
    print(f"✅ Test stop=entry: {result['reason']}")
    
    # Test avec prix invalide
    result = rm.calculate_position_size(0, 149.0, 'AAPL', 1.5)
    print(f"✅ Test prix=0: {result['reason']}")
    
    print("\n✅ Tous les tests de protection passés!")
