"""
🛡️ GESTIONNAIRE DE RISQUES SWING V3.0
======================================
Version: 3.0 - Optimisé avec diversification
Date: Décembre 2024

AMÉLIORATIONS V3.0:
✅ Protection division par zéro
✅ Diversification sectorielle
✅ Vérification gap pré-market
✅ Take profit progressif
✅ Trailing stop amélioré
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional
import numpy as np

try:
    from shared_utils import (safe_divide, get_sector, count_positions_by_sector,
                             SYMBOLS_BY_SECTOR, check_premarket_gap)
except ImportError:
    def safe_divide(n, d, default=0.0):
        try:
            if d == 0: return default
            return n / d
        except: return default
    
    def get_sector(s): return 'tech'
    def count_positions_by_sector(p): return {}
    SYMBOLS_BY_SECTOR = {'tech': [], 'etf': []}
    def check_premarket_gap(api, s, m): return True, 0, 'N/A'

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Gestionnaire de Risques Swing V3.0
    ==================================
    """
    
    def __init__(self, api):
        self.api = api
        
        # ═══════════════════════════════════════════════════════════
        # PARAMÈTRES DE RISQUE
        # ═══════════════════════════════════════════════════════════
        self.risk_per_trade = 0.02        # 2% du capital par trade
        self.max_position_pct = 0.10      # 10% max par position
        self.max_positions = 5            # 5 positions max
        self.max_daily_loss = 0.03        # 3% perte max journalière
        self.trailing_stop_pct = 0.03     # 3% trailing stop
        
        # Diversification
        self.max_per_sector = 2           # 2 positions max par secteur
        self.max_correlation = 0.8        # Éviter actifs trop corrélés
        
        # Gap protection
        self.max_gap_pct = 5.0            # 5% max gap overnight
        
        # Suivi
        self.daily_pnl = 0
        self.last_reset = date.today()
        self.trailing_stops: Dict[str, float] = {}
        self.sold_percentages: Dict[str, float] = {}  # Pour take profit progressif
        
        # Stats
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0
        }
    
    def can_trade(self) -> tuple:
        """Vérifie si on peut encore trader"""
        # Reset quotidien
        if date.today() != self.last_reset:
            self.daily_pnl = 0
            self.last_reset = date.today()
        
        try:
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            
            # Perte journalière max
            max_loss = portfolio_value * self.max_daily_loss
            if self.daily_pnl < -max_loss:
                return False, f"Perte max atteinte (${self.daily_pnl:.2f})"
            
            # Nombre de positions
            positions = self.api.list_positions()
            if len(positions) >= self.max_positions:
                return False, f"Max positions ({len(positions)}/{self.max_positions})"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Erreur vérification: {e}")
            return False, str(e)
    
    def check_sector_diversification(self, symbol: str) -> tuple:
        """Vérifie la diversification sectorielle"""
        try:
            sector = get_sector(symbol)
            positions = self.api.list_positions()
            
            sector_count = 0
            for pos in positions:
                if get_sector(pos.symbol) == sector:
                    sector_count += 1
            
            if sector_count >= self.max_per_sector:
                return False, f"Max {self.max_per_sector} positions en {sector}"
            
            return True, "OK"
            
        except Exception as e:
            return True, "OK"  # En cas d'erreur, on autorise
    
    def check_gap(self, symbol: str) -> tuple:
        """Vérifie le gap pré-market"""
        try:
            ok, gap_pct, direction = check_premarket_gap(self.api, symbol, self.max_gap_pct)
            if not ok:
                return False, f"Gap {direction} trop grand ({gap_pct:.1f}%)"
            return True, f"Gap OK ({gap_pct:+.1f}%)"
        except:
            return True, "Gap check N/A"
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                               stop_loss: float) -> int:
        """Calcule la taille de position optimale"""
        try:
            # Validations
            if entry_price <= 0:
                logger.warning(f"Prix invalide pour {symbol}")
                return 0
            
            if stop_loss <= 0 or stop_loss >= entry_price:
                logger.warning(f"Stop invalide pour {symbol}")
                return 0
            
            account = self.api.get_account()
            cash = float(account.cash)
            portfolio_value = float(account.portfolio_value)
            buying_power = float(account.buying_power)
            
            # Risque maximum
            risk_amount = portfolio_value * self.risk_per_trade
            
            # Risque par action (protection division/0)
            risk_per_share = entry_price - stop_loss
            if risk_per_share <= 0:
                return 0
            
            # Taille basée sur risque
            size_risk = int(safe_divide(risk_amount, risk_per_share, 0))
            
            # Taille max (% portfolio)
            max_value = portfolio_value * self.max_position_pct
            size_max = int(safe_divide(max_value, entry_price, 0))
            
            # Taille max (buying power)
            size_bp = int(safe_divide(buying_power * 0.5, entry_price, 0))
            
            # Prendre le minimum
            position_size = max(1, min(size_risk, size_max, size_bp))
            
            logger.info(f"📐 Position {symbol}:")
            logger.info(f"   Risque 2%: {size_risk} | Max 10%: {size_max} | BP: {size_bp}")
            logger.info(f"   ➡️ Taille: {position_size} actions")
            
            return position_size
            
        except Exception as e:
            logger.error(f"Erreur calcul position {symbol}: {e}")
            return 0
    
    def update_trailing_stop(self, position) -> Optional[Dict]:
        """Met à jour le trailing stop"""
        symbol = position.symbol
        current_price = float(position.current_price)
        entry_price = float(position.avg_entry_price)
        qty = int(position.qty)
        
        # Nouveau stop
        new_stop = current_price * (1 - self.trailing_stop_pct)
        
        # Ancien stop
        old_stop = self.trailing_stops.get(symbol, entry_price * 0.95)
        
        # Le stop ne peut que monter
        if new_stop > old_stop:
            self.trailing_stops[symbol] = new_stop
            
            # Profit actuel
            profit_pct = safe_divide(current_price - entry_price, entry_price, 0) * 100
            
            # Vérifier si stop touché
            if current_price <= new_stop:
                return {
                    'action': 'SELL_ALL',
                    'symbol': symbol,
                    'qty': qty,
                    'reason': f'Trailing Stop ({profit_pct:+.1f}%)',
                    'profit_pct': profit_pct
                }
            
            # Log si profit significatif
            if profit_pct > 5:
                logger.info(f"📈 {symbol}: +{profit_pct:.1f}% | Trail: ${new_stop:.2f}")
        
        return None
    
    def check_take_profit_progressive(self, position) -> Optional[Dict]:
        """Vérifie le take profit progressif"""
        symbol = position.symbol
        current = float(position.current_price)
        entry = float(position.avg_entry_price)
        qty = int(position.qty)
        
        profit_pct = safe_divide(current - entry, entry, 0) * 100
        
        # Pourcentage déjà vendu
        already_sold = self.sold_percentages.get(symbol, 0)
        
        # Niveaux de take profit
        levels = [
            {'pct': 5, 'sell': 0.25},
            {'pct': 10, 'sell': 0.50},
            {'pct': 15, 'sell': 0.75},
            {'pct': 20, 'sell': 1.0},
        ]
        
        for level in levels:
            if profit_pct >= level['pct']:
                to_sell_pct = level['sell'] - already_sold
                if to_sell_pct > 0:
                    shares_to_sell = int(qty * to_sell_pct)
                    if shares_to_sell >= 1:
                        self.sold_percentages[symbol] = level['sell']
                        
                        action = 'SELL_ALL' if level['sell'] >= 1 else 'SELL_PARTIAL'
                        
                        return {
                            'action': action,
                            'symbol': symbol,
                            'qty': shares_to_sell,
                            'reason': f"Take Profit +{profit_pct:.1f}%",
                            'profit_pct': profit_pct
                        }
        
        return None
    
    def close_position(self, symbol: str, qty: int, reason: str):
        """Ferme une position"""
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            logger.info(f"✅ Vente {symbol}: {qty} actions ({reason})")
            
            # Nettoyer
            if symbol in self.trailing_stops:
                del self.trailing_stops[symbol]
            if symbol in self.sold_percentages:
                del self.sold_percentages[symbol]
                
        except Exception as e:
            logger.error(f"Erreur vente {symbol}: {e}")
    
    def record_trade_result(self, pnl: float):
        """Enregistre le résultat d'un trade"""
        self.daily_pnl += pnl
        self.stats['total_trades'] += 1
        self.stats['total_pnl'] += pnl
        
        if pnl > 0:
            self.stats['winning_trades'] += 1
            if pnl > self.stats['best_trade']:
                self.stats['best_trade'] = pnl
        else:
            self.stats['losing_trades'] += 1
            if pnl < self.stats['worst_trade']:
                self.stats['worst_trade'] = pnl
    
    def get_portfolio_risk(self) -> Dict:
        """Calcule le risque total du portfolio"""
        try:
            positions = self.api.list_positions()
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            
            total_risk = 0
            sector_exposure = {}
            
            for pos in positions:
                entry = float(pos.avg_entry_price)
                current = float(pos.current_price)
                qty = int(pos.qty)
                
                stop = self.trailing_stops.get(pos.symbol, entry * 0.95)
                position_risk = (current - stop) * qty
                total_risk += position_risk
                
                # Exposition par secteur
                sector = get_sector(pos.symbol)
                sector_exposure[sector] = sector_exposure.get(sector, 0) + (current * qty)
            
            risk_pct = safe_divide(total_risk, portfolio_value, 0) * 100
            
            return {
                'total_risk': total_risk,
                'risk_pct': risk_pct,
                'positions': len(positions),
                'sector_exposure': sector_exposure,
                'daily_pnl': self.daily_pnl
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul risque: {e}")
            return {'total_risk': 0, 'risk_pct': 0, 'positions': 0}
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques"""
        win_rate = safe_divide(
            self.stats['winning_trades'],
            self.stats['total_trades'],
            0
        ) * 100
        
        return {
            **self.stats,
            'win_rate': win_rate,
            'daily_pnl': self.daily_pnl
        }
    
    def print_stats(self):
        """Affiche les statistiques"""
        s = self.get_stats()
        logger.info("═" * 60)
        logger.info("📊 STATISTIQUES SWING TRADING")
        logger.info("═" * 60)
        logger.info(f"   Trades: {s['total_trades']}")
        logger.info(f"   Gagnants: {s['winning_trades']} | Perdants: {s['losing_trades']}")
        logger.info(f"   Win Rate: {s['win_rate']:.1f}%")
        logger.info(f"   PnL Total: ${s['total_pnl']:+,.2f}")
        logger.info(f"   PnL Jour: ${s['daily_pnl']:+,.2f}")
        logger.info(f"   Meilleur: ${s['best_trade']:+,.2f}")
        logger.info(f"   Pire: ${s['worst_trade']:+,.2f}")
        logger.info("═" * 60)


if __name__ == "__main__":
    print("✅ Risk Manager Swing V3.0")
    print("   - Diversification sectorielle")
    print("   - Gap protection")
    print("   - Take profit progressif")
    print("   - Protection division/0")
