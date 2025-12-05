"""
🛡️ GESTIONNAIRE DE RISQUE SCALPING ULTRA-OPTIMISÉ
==================================================
Gestion de risque stricte pour scalping haute fréquence

RÈGLES:
- Max 1% de risque par trade
- Max 3% de perte journalière
- Max 10 trades perdants consécutifs = STOP
- Position sizing dynamique basé sur volatilité
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

logger = logging.getLogger(__name__)

NY_TZ = pytz.timezone('America/New_York')


class ScalpingRiskManager:
    """
    Gestionnaire de Risque pour Scalping
    =====================================
    Optimisé pour trades rapides avec gestion stricte
    """
    
    def __init__(self, initial_capital: float = 100000):
        # ═══════════════════════════════════════════════════════════
        # CAPITAL & LIMITES
        # ═══════════════════════════════════════════════════════════
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Risque par trade (très conservateur pour scalping)
        self.risk_per_trade_pct = 0.5          # 0.5% max par trade
        self.max_risk_per_trade_pct = 1.0      # Jamais plus de 1%
        
        # Limites journalières
        self.max_daily_loss_pct = 2.0          # Stop à -2% jour
        self.max_daily_profit_pct = 5.0        # Objectif +5% jour
        self.max_trades_per_day = 20           # Max 20 trades/jour
        self.max_consecutive_losses = 5        # Stop après 5 pertes
        
        # Limites de position
        self.max_position_pct = 10.0           # Max 10% du capital par position
        self.max_positions = 3                 # Max 3 positions simultanées
        self.max_exposure_pct = 25.0           # Max 25% d'exposition totale
        
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
        
        # Historique des trades
        self.trade_history: List[Dict] = []
        self.open_positions: Dict[str, Dict] = {}
        
        # État du trading
        self.trading_allowed = True
        self.halt_reason = None
        
    def reset_daily_stats(self):
        """Reset les statistiques journalières"""
        today = datetime.now(NY_TZ).date()
        
        if self.daily_stats['date'] != today:
            logger.info(f"📊 Reset stats journalières - Nouvelle journée: {today}")
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
        """
        Vérifie si le trading est autorisé
        
        Returns:
            tuple: (is_allowed, reason)
        """
        self.reset_daily_stats()
        
        # 1. Vérifier perte journalière max
        if self.daily_stats['pnl_pct'] <= -self.max_daily_loss_pct:
            self.trading_allowed = False
            self.halt_reason = f"Perte journalière max atteinte ({self.daily_stats['pnl_pct']:.2f}%)"
            return False, self.halt_reason
        
        # 2. Vérifier nombre de trades
        if self.daily_stats['trades_count'] >= self.max_trades_per_day:
            self.trading_allowed = False
            self.halt_reason = f"Nombre max de trades atteint ({self.max_trades_per_day})"
            return False, self.halt_reason
        
        # 3. Vérifier pertes consécutives
        if self.daily_stats['consecutive_losses'] >= self.max_consecutive_losses:
            self.trading_allowed = False
            self.halt_reason = f"Pertes consécutives max ({self.max_consecutive_losses})"
            return False, self.halt_reason
        
        # 4. Vérifier nombre de positions ouvertes
        if len(self.open_positions) >= self.max_positions:
            return False, f"Max positions atteint ({self.max_positions})"
        
        # 5. Vérifier objectif journalier (optionnel - peut continuer)
        if self.daily_stats['pnl_pct'] >= self.max_daily_profit_pct:
            logger.info(f"🎉 Objectif journalier atteint: +{self.daily_stats['pnl_pct']:.2f}%")
            # On peut continuer mais avec prudence
        
        return True, "Trading autorisé"
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, 
                               symbol: str, volatility_pct: float = 1.0) -> dict:
        """
        Calcule la taille de position optimale basée sur le risque
        
        Args:
            entry_price: Prix d'entrée prévu
            stop_loss: Prix du stop loss
            symbol: Symbole de l'actif
            volatility_pct: Volatilité actuelle (ATR %)
        
        Returns:
            dict avec shares, position_value, risk_amount, etc.
        """
        # Vérifier si trading autorisé
        allowed, reason = self.check_trading_allowed()
        if not allowed:
            return {
                'allowed': False,
                'reason': reason,
                'shares': 0
            }
        
        # Calculer le risque par action
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            return {
                'allowed': False,
                'reason': 'Stop loss invalide',
                'shares': 0
            }
        
        # Ajuster le risque en fonction de la volatilité
        # Plus volatile = moins de risque
        adjusted_risk_pct = self.risk_per_trade_pct
        if volatility_pct > 2.0:
            adjusted_risk_pct = self.risk_per_trade_pct * 0.5  # Réduire de moitié
        elif volatility_pct > 1.5:
            adjusted_risk_pct = self.risk_per_trade_pct * 0.75
        
        # Calculer le montant à risquer
        risk_amount = self.current_capital * (adjusted_risk_pct / 100)
        
        # Calculer le nombre d'actions
        shares = int(risk_amount / risk_per_share)
        
        # Vérifier la taille de position max
        position_value = shares * entry_price
        max_position_value = self.current_capital * (self.max_position_pct / 100)
        
        if position_value > max_position_value:
            shares = int(max_position_value / entry_price)
            position_value = shares * entry_price
        
        # Vérifier l'exposition totale
        total_exposure = sum(
            pos.get('value', 0) for pos in self.open_positions.values()
        )
        remaining_exposure = (self.current_capital * self.max_exposure_pct / 100) - total_exposure
        
        if position_value > remaining_exposure:
            shares = int(remaining_exposure / entry_price)
            position_value = shares * entry_price
        
        if shares < 1:
            return {
                'allowed': False,
                'reason': 'Position trop petite (< 1 action)',
                'shares': 0
            }
        
        # Recalculer le risque réel
        actual_risk = shares * risk_per_share
        actual_risk_pct = (actual_risk / self.current_capital) * 100
        
        return {
            'allowed': True,
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_value': position_value,
            'position_pct': (position_value / self.current_capital) * 100,
            'risk_amount': actual_risk,
            'risk_pct': actual_risk_pct,
            'risk_per_share': risk_per_share
        }
    
    def register_trade_entry(self, symbol: str, shares: int, entry_price: float,
                            stop_loss: float, take_profit: float, signal_data: dict = None):
        """Enregistre une nouvelle position"""
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
        
        # Calculer le PnL
        pnl = (exit_price - entry_price) * shares
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Mettre à jour les stats
        self.daily_stats['pnl'] += pnl
        self.daily_stats['pnl_pct'] = (self.daily_stats['pnl'] / self.daily_stats['starting_capital']) * 100
        
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
        
        # Mettre à jour le capital
        self.current_capital += pnl
        
        # Ajouter à l'historique
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
        
        # Supprimer la position
        del self.open_positions[symbol]
        
        emoji = "💰" if pnl > 0 else "📉"
        logger.info(f"{emoji} Position fermée: {symbol}")
        logger.info(f"   PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        logger.info(f"   Raison: {exit_reason}")
        logger.info(f"   Capital: ${self.current_capital:.2f}")
        
        return trade_record
    
    def update_position_price(self, symbol: str, current_price: float):
        """Met à jour le prix actuel d'une position (pour trailing stop)"""
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
    
    def get_daily_summary(self) -> dict:
        """Retourne un résumé des stats journalières"""
        total_trades = self.daily_stats['winning_trades'] + self.daily_stats['losing_trades']
        win_rate = (self.daily_stats['winning_trades'] / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'date': self.daily_stats['date'],
            'pnl': self.daily_stats['pnl'],
            'pnl_pct': self.daily_stats['pnl_pct'],
            'total_trades': total_trades,
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
        summary = self.get_daily_summary()
        
        logger.info("=" * 60)
        logger.info("📊 RÉSUMÉ JOURNALIER SCALPING")
        logger.info("=" * 60)
        logger.info(f"   Date: {summary['date']}")
        logger.info(f"   PnL: ${summary['pnl']:.2f} ({summary['pnl_pct']:+.2f}%)")
        logger.info(f"   Trades: {summary['total_trades']} (W:{summary['winning_trades']} L:{summary['losing_trades']})")
        logger.info(f"   Win Rate: {summary['win_rate']:.1f}%")
        logger.info(f"   Meilleur trade: ${summary['best_trade']:.2f}")
        logger.info(f"   Pire trade: ${summary['worst_trade']:.2f}")
        logger.info(f"   Capital: ${summary['current_capital']:.2f}")
        logger.info(f"   Positions ouvertes: {summary['open_positions']}")
        logger.info("=" * 60)


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    rm = ScalpingRiskManager(initial_capital=100000)
    
    # Test position sizing
    result = rm.calculate_position_size(
        entry_price=150.0,
        stop_loss=149.0,
        symbol='AAPL',
        volatility_pct=1.5
    )
    
    print(f"\n📊 Test Position Sizing:")
    print(f"   Actions: {result['shares']}")
    print(f"   Valeur: ${result.get('position_value', 0):.2f}")
    print(f"   Risque: ${result.get('risk_amount', 0):.2f} ({result.get('risk_pct', 0):.2f}%)")

