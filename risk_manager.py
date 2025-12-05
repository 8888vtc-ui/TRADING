"""
🛡️ GESTIONNAIRE DE RISQUES
===========================
Gestion du capital, position sizing et trailing stops
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


class RiskManager:
    """Gestionnaire de risques pour le trading"""
    
    def __init__(self, api):
        """Initialise le gestionnaire de risques"""
        self.api = api
        
        # Paramètres de risque
        self.risk_per_trade = 0.02       # 2% du capital par trade
        self.max_position_pct = 0.10     # 10% max par position
        self.max_positions = 5           # 5 positions max simultanées
        self.max_daily_loss = 0.03       # 3% perte max journalière
        self.trailing_stop_pct = 0.03    # Trailing stop 3%
        
        # Suivi des trades
        self.daily_pnl = 0
        self.last_reset_date = date.today()
        
        # Cache des trailing stops
        self.trailing_stops = {}
    
    def can_trade(self):
        """Vérifie si on peut encore trader"""
        # Reset quotidien
        if date.today() != self.last_reset_date:
            self.daily_pnl = 0
            self.last_reset_date = date.today()
        
        # Vérifier la perte journalière
        account = self.api.get_account()
        portfolio_value = float(account.portfolio_value)
        
        if self.daily_pnl < -portfolio_value * self.max_daily_loss:
            logger.warning(f"⚠️ Perte journalière max atteinte: ${self.daily_pnl:.2f}")
            return False
        
        # Vérifier le nombre de positions
        positions = self.api.list_positions()
        if len(positions) >= self.max_positions:
            logger.info(f"📊 Nombre max de positions atteint ({len(positions)}/{self.max_positions})")
            return False
        
        return True
    
    def calculate_position_size(self, symbol, entry_price, stop_loss):
        """Calcule la taille de position optimale"""
        try:
            account = self.api.get_account()
            cash = float(account.cash)
            portfolio_value = float(account.portfolio_value)
            buying_power = float(account.buying_power)
            
            # Risque maximum pour ce trade
            risk_amount = portfolio_value * self.risk_per_trade
            
            # Risque par action
            risk_per_share = entry_price - stop_loss
            
            if risk_per_share <= 0:
                logger.warning(f"⚠️ Stop loss invalide pour {symbol}")
                return 0
            
            # Taille de position basée sur le risque
            position_size_risk = int(risk_amount / risk_per_share)
            
            # Taille max basée sur le pourcentage du portfolio
            max_position_value = portfolio_value * self.max_position_pct
            position_size_max = int(max_position_value / entry_price)
            
            # Taille max basée sur le buying power
            position_size_bp = int(buying_power * 0.5 / entry_price)  # Utiliser 50% du BP max
            
            # Prendre le minimum
            position_size = min(position_size_risk, position_size_max, position_size_bp)
            
            # Minimum 1 action
            position_size = max(1, position_size)
            
            logger.info(f"📐 Position sizing {symbol}:")
            logger.info(f"   Risque 2%: {position_size_risk} actions")
            logger.info(f"   Max 10%: {position_size_max} actions")
            logger.info(f"   Buying Power: {position_size_bp} actions")
            logger.info(f"   ➡️ Taille finale: {position_size} actions")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Erreur calcul position {symbol}: {e}")
            return 0
    
    def update_trailing_stop(self, position):
        """Met à jour le trailing stop d'une position"""
        symbol = position.symbol
        current_price = float(position.current_price)
        entry_price = float(position.avg_entry_price)
        qty = int(position.qty)
        
        # Calculer le nouveau stop basé sur le prix actuel
        new_stop = current_price * (1 - self.trailing_stop_pct)
        
        # Récupérer l'ancien stop
        old_stop = self.trailing_stops.get(symbol, entry_price * (1 - 0.05))
        
        # Le stop ne peut que monter
        if new_stop > old_stop:
            self.trailing_stops[symbol] = new_stop
            
            # Vérifier si le prix a touché le stop
            if current_price <= new_stop:
                logger.info(f"🛑 TRAILING STOP TOUCHÉ: {symbol} @ ${current_price:.2f}")
                self._close_position(symbol, qty, "Trailing Stop")
            else:
                # Calculer le profit potentiel
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                if profit_pct > 10:
                    logger.info(f"📈 {symbol}: +{profit_pct:.1f}% | Trailing stop: ${new_stop:.2f}")
    
    def _close_position(self, symbol, qty, reason):
        """Ferme une position"""
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            logger.info(f"✅ Position fermée: {symbol} ({reason})")
            
            # Nettoyer le cache
            if symbol in self.trailing_stops:
                del self.trailing_stops[symbol]
                
        except Exception as e:
            logger.error(f"Erreur fermeture {symbol}: {e}")
    
    def get_portfolio_risk(self):
        """Calcule le risque total du portfolio"""
        try:
            positions = self.api.list_positions()
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            
            total_risk = 0
            
            for pos in positions:
                entry = float(pos.avg_entry_price)
                current = float(pos.current_price)
                qty = int(pos.qty)
                
                # Risque basé sur le trailing stop
                stop = self.trailing_stops.get(pos.symbol, entry * 0.95)
                position_risk = (current - stop) * qty
                total_risk += position_risk
            
            risk_pct = (total_risk / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            return {
                'total_risk': total_risk,
                'risk_pct': risk_pct,
                'positions': len(positions)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul risque: {e}")
            return {'total_risk': 0, 'risk_pct': 0, 'positions': 0}
    
    def check_take_profit(self, position):
        """Vérifie si on doit prendre des profits"""
        current = float(position.current_price)
        entry = float(position.avg_entry_price)
        profit_pct = ((current - entry) / entry) * 100
        
        # Take profit progressif
        if profit_pct >= 20:
            return {'action': 'SELL_ALL', 'reason': 'Take Profit 20%'}
        elif profit_pct >= 15:
            return {'action': 'SELL_33', 'reason': 'Take Profit 15%'}
        elif profit_pct >= 10:
            return {'action': 'SELL_33', 'reason': 'Take Profit 10%'}
        
        return {'action': 'HOLD', 'reason': None}

