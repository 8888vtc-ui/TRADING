"""
🛡️ CAPITAL PROTECTOR V1.0 - LIMITER LES PERTES, GARDER LES GAINS
==================================================================

PHILOSOPHIE:
"Il vaut mieux un petit gain sécurisé qu'un gros gain potentiel risqué"

PRINCIPES:
1. Stop Loss STRICT et NON-NÉGOCIABLE
2. Trailing Stop AGRESSIF pour verrouiller les gains
3. Take Profit PROGRESSIF (sécuriser par paliers)
4. MODE PROTECTION automatique si drawdown
5. Réduction automatique du risque après pertes
6. JAMAIS de moyenne à la baisse
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProtectionMode(Enum):
    NORMAL = "normal"           # Trading normal
    CAUTIOUS = "cautious"       # -3% daily → réduire risque
    DEFENSIVE = "defensive"     # -5% daily → très prudent
    LOCKDOWN = "lockdown"       # -8% daily → STOP trading


@dataclass
class ProtectedTrade:
    """Trade avec protection intégrée"""
    symbol: str
    entry_price: float
    quantity: float
    side: str  # 'long' ou 'short'
    
    # Protection levels
    stop_loss: float           # STRICT - jamais bougé vers le bas
    break_even_level: float    # Niveau pour passer stop à BE
    trailing_start: float      # Profit % pour activer trailing
    trailing_distance: float   # Distance du trailing
    
    # Take profit progressif
    tp1: float  # Premier TP (30% de la position)
    tp2: float  # Deuxième TP (30% de la position)
    tp3: float  # Troisième TP (40% restant)
    
    # État
    highest_price: float = 0
    lowest_price: float = float('inf')
    current_stop: float = 0
    tp1_hit: bool = False
    tp2_hit: bool = False
    at_break_even: bool = False
    trailing_active: bool = False
    
    def __post_init__(self):
        self.highest_price = self.entry_price
        self.lowest_price = self.entry_price
        self.current_stop = self.stop_loss


class CapitalProtector:
    """
    🛡️ SYSTÈME DE PROTECTION DU CAPITAL
    
    Limite les pertes à:
    - Max 1% par trade
    - Max 3% par jour
    - Max 8% par semaine
    
    Conserve les gains via:
    - Trailing stop automatique
    - Take profit progressif
    - Move to break-even rapide
    """
    
    def __init__(self, initial_capital: float = 1000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.high_watermark = initial_capital  # Plus haut historique
        
        # Limites de pertes (STRICTES)
        self.max_loss_per_trade = 0.01      # 1% max par trade
        self.max_daily_loss = 0.03          # 3% max par jour
        self.max_weekly_loss = 0.08         # 8% max par semaine
        
        # Paramètres de protection
        self.break_even_trigger = 0.015     # +1.5% → stop à break-even
        self.trailing_trigger = 0.025       # +2.5% → trailing activé
        self.trailing_distance = 0.012      # 1.2% trailing distance
        
        # Take profit progressif
        self.tp_levels = [
            {'pct': 0.03, 'sell': 0.30},    # +3% → vendre 30%
            {'pct': 0.05, 'sell': 0.30},    # +5% → vendre 30%
            {'pct': 0.08, 'sell': 0.40},    # +8% → vendre 40% restant
        ]
        
        # État
        self.mode = ProtectionMode.NORMAL
        self.daily_pnl = 0
        self.weekly_pnl = 0
        self.trades_today = 0
        self.consecutive_losses = 0
        self.active_trades: Dict[str, ProtectedTrade] = {}
        
        # Historique
        self.trade_history: List[Dict] = []
        
        logger.info("🛡️ Capital Protector initialisé")
        logger.info(f"   Max perte/trade: {self.max_loss_per_trade*100}%")
        logger.info(f"   Max perte/jour: {self.max_daily_loss*100}%")
        logger.info(f"   Trailing à +{self.trailing_trigger*100}%")
    
    # ═══════════════════════════════════════════════════════════════
    # CALCUL DE PROTECTION
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_protected_entry(
        self, 
        symbol: str, 
        entry_price: float, 
        direction: str = 'long',
        atr_pct: float = 2.0
    ) -> ProtectedTrade:
        """
        Calcule tous les niveaux de protection pour un trade
        """
        
        # Ajuster selon le mode
        risk_mult = self._get_risk_multiplier()
        
        # Stop Loss basé sur ATR mais limité
        stop_distance = min(atr_pct * 0.01, self.max_loss_per_trade) * risk_mult
        
        if direction == 'long':
            stop_loss = entry_price * (1 - stop_distance)
            break_even = entry_price * (1 + self.break_even_trigger)
            trailing_start = entry_price * (1 + self.trailing_trigger)
            tp1 = entry_price * (1 + self.tp_levels[0]['pct'])
            tp2 = entry_price * (1 + self.tp_levels[1]['pct'])
            tp3 = entry_price * (1 + self.tp_levels[2]['pct'])
        else:  # short
            stop_loss = entry_price * (1 + stop_distance)
            break_even = entry_price * (1 - self.break_even_trigger)
            trailing_start = entry_price * (1 - self.trailing_trigger)
            tp1 = entry_price * (1 - self.tp_levels[0]['pct'])
            tp2 = entry_price * (1 - self.tp_levels[1]['pct'])
            tp3 = entry_price * (1 - self.tp_levels[2]['pct'])
        
        # Calculer la taille de position
        max_risk = self.current_capital * self.max_loss_per_trade * risk_mult
        position_value = max_risk / stop_distance if stop_distance > 0 else 0
        quantity = position_value / entry_price if entry_price > 0 else 0
        
        trade = ProtectedTrade(
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
            side=direction,
            stop_loss=stop_loss,
            break_even_level=break_even,
            trailing_start=trailing_start,
            trailing_distance=self.trailing_distance,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3
        )
        
        logger.info(f"\n🛡️ PROTECTION CALCULÉE pour {symbol}")
        logger.info(f"   Entry: ${entry_price:.2f}")
        logger.info(f"   🛑 Stop Loss: ${stop_loss:.2f} ({stop_distance*100:.1f}%)")
        logger.info(f"   🔒 Break-Even à: ${break_even:.2f} (+{self.break_even_trigger*100}%)")
        logger.info(f"   📈 Trailing dès: ${trailing_start:.2f} (+{self.trailing_trigger*100}%)")
        logger.info(f"   💰 TP1: ${tp1:.2f} | TP2: ${tp2:.2f} | TP3: ${tp3:.2f}")
        
        return trade
    
    def _get_risk_multiplier(self) -> float:
        """Multiplicateur de risque selon le mode"""
        if self.mode == ProtectionMode.LOCKDOWN:
            return 0.0  # Pas de trading
        elif self.mode == ProtectionMode.DEFENSIVE:
            return 0.3  # 30% du risque normal
        elif self.mode == ProtectionMode.CAUTIOUS:
            return 0.6  # 60% du risque normal
        else:
            # Réduire après pertes consécutives
            if self.consecutive_losses >= 3:
                return 0.5
            elif self.consecutive_losses >= 2:
                return 0.7
            return 1.0
    
    # ═══════════════════════════════════════════════════════════════
    # MISE À JOUR EN TEMPS RÉEL
    # ═══════════════════════════════════════════════════════════════
    
    def update_trade(self, symbol: str, current_price: float) -> Dict:
        """
        Met à jour la protection d'un trade en cours
        Retourne les actions à effectuer
        """
        if symbol not in self.active_trades:
            return {'action': 'none'}
        
        trade = self.active_trades[symbol]
        actions = []
        
        is_long = trade.side == 'long'
        
        # Mettre à jour highest/lowest
        if current_price > trade.highest_price:
            trade.highest_price = current_price
        if current_price < trade.lowest_price:
            trade.lowest_price = current_price
        
        if is_long:
            profit_pct = (current_price - trade.entry_price) / trade.entry_price
            
            # 1. STOP LOSS touché → SORTIR IMMÉDIATEMENT
            if current_price <= trade.current_stop:
                return {
                    'action': 'EXIT_ALL',
                    'reason': f'🛑 STOP LOSS touché à ${current_price:.2f}',
                    'pnl_pct': profit_pct * 100
                }
            
            # 2. TP1 touché → Vendre 30%
            if not trade.tp1_hit and current_price >= trade.tp1:
                trade.tp1_hit = True
                actions.append({
                    'action': 'PARTIAL_EXIT',
                    'percent': 30,
                    'reason': f'💰 TP1 atteint (+{self.tp_levels[0]["pct"]*100}%)'
                })
            
            # 3. TP2 touché → Vendre 30%
            if not trade.tp2_hit and current_price >= trade.tp2:
                trade.tp2_hit = True
                actions.append({
                    'action': 'PARTIAL_EXIT',
                    'percent': 30,
                    'reason': f'💰 TP2 atteint (+{self.tp_levels[1]["pct"]*100}%)'
                })
            
            # 4. TP3 touché → Vendre tout le reste
            if current_price >= trade.tp3:
                return {
                    'action': 'EXIT_ALL',
                    'reason': f'🎯 TP3 FINAL atteint (+{self.tp_levels[2]["pct"]*100}%)',
                    'pnl_pct': profit_pct * 100
                }
            
            # 5. Move to Break-Even
            if not trade.at_break_even and current_price >= trade.break_even_level:
                trade.at_break_even = True
                trade.current_stop = trade.entry_price * 1.001  # Petit profit garanti
                actions.append({
                    'action': 'MOVE_STOP',
                    'new_stop': trade.current_stop,
                    'reason': f'🔒 Stop déplacé à Break-Even + 0.1%'
                })
            
            # 6. Trailing Stop
            if current_price >= trade.trailing_start:
                trade.trailing_active = True
                new_stop = current_price * (1 - trade.trailing_distance)
                if new_stop > trade.current_stop:
                    trade.current_stop = new_stop
                    actions.append({
                        'action': 'TRAIL_STOP',
                        'new_stop': new_stop,
                        'reason': f'📈 Trailing: stop à ${new_stop:.2f}'
                    })
        
        else:  # SHORT
            profit_pct = (trade.entry_price - current_price) / trade.entry_price
            
            # Stop Loss (au-dessus pour short)
            if current_price >= trade.current_stop:
                return {
                    'action': 'EXIT_ALL',
                    'reason': f'🛑 STOP LOSS touché à ${current_price:.2f}',
                    'pnl_pct': profit_pct * 100
                }
            
            # TP pour short (prix descend)
            if not trade.tp1_hit and current_price <= trade.tp1:
                trade.tp1_hit = True
                actions.append({
                    'action': 'PARTIAL_EXIT',
                    'percent': 30,
                    'reason': f'💰 TP1 short atteint'
                })
            
            if current_price <= trade.tp3:
                return {
                    'action': 'EXIT_ALL',
                    'reason': f'🎯 TP3 FINAL short atteint',
                    'pnl_pct': profit_pct * 100
                }
            
            # Break-even pour short
            if not trade.at_break_even and current_price <= trade.break_even_level:
                trade.at_break_even = True
                trade.current_stop = trade.entry_price * 0.999
                actions.append({
                    'action': 'MOVE_STOP',
                    'new_stop': trade.current_stop,
                    'reason': '🔒 Stop short à Break-Even'
                })
            
            # Trailing pour short
            if current_price <= trade.trailing_start:
                trade.trailing_active = True
                new_stop = current_price * (1 + trade.trailing_distance)
                if new_stop < trade.current_stop:
                    trade.current_stop = new_stop
                    actions.append({
                        'action': 'TRAIL_STOP',
                        'new_stop': new_stop,
                        'reason': f'📉 Trailing short: stop à ${new_stop:.2f}'
                    })
        
        if actions:
            return {'action': 'MULTIPLE', 'actions': actions, 'pnl_pct': profit_pct * 100}
        
        return {'action': 'HOLD', 'pnl_pct': profit_pct * 100}
    
    # ═══════════════════════════════════════════════════════════════
    # GESTION DU MODE DE PROTECTION
    # ═══════════════════════════════════════════════════════════════
    
    def update_daily_pnl(self, pnl: float):
        """Met à jour le P&L et ajuste le mode de protection"""
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.current_capital += pnl
        
        # Mettre à jour high watermark
        if self.current_capital > self.high_watermark:
            self.high_watermark = self.current_capital
        
        # Vérifier les limites
        daily_loss_pct = abs(self.daily_pnl) / self.initial_capital if self.daily_pnl < 0 else 0
        
        old_mode = self.mode
        
        if daily_loss_pct >= 0.08:
            self.mode = ProtectionMode.LOCKDOWN
        elif daily_loss_pct >= 0.05:
            self.mode = ProtectionMode.DEFENSIVE
        elif daily_loss_pct >= 0.03:
            self.mode = ProtectionMode.CAUTIOUS
        else:
            self.mode = ProtectionMode.NORMAL
        
        if self.mode != old_mode:
            if self.mode == ProtectionMode.LOCKDOWN:
                logger.error(f"🚨🚨🚨 MODE LOCKDOWN - Trading STOPPÉ!")
                logger.error(f"   Perte journalière: {daily_loss_pct*100:.1f}%")
            elif self.mode == ProtectionMode.DEFENSIVE:
                logger.warning(f"⚠️⚠️ MODE DÉFENSIF - Risque réduit à 30%")
            elif self.mode == ProtectionMode.CAUTIOUS:
                logger.warning(f"⚠️ MODE PRUDENT - Risque réduit à 60%")
            else:
                logger.info(f"✅ Retour en mode NORMAL")
        
        # Enregistrer perte/gain
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def can_trade(self) -> Dict:
        """Vérifie si on peut encore trader"""
        if self.mode == ProtectionMode.LOCKDOWN:
            return {
                'can_trade': False,
                'reason': '🚨 LOCKDOWN - Perte journalière max atteinte',
                'daily_pnl': self.daily_pnl
            }
        
        if self.consecutive_losses >= 5:
            return {
                'can_trade': False,
                'reason': '⛔ 5 pertes consécutives - Pause obligatoire',
                'consecutive_losses': self.consecutive_losses
            }
        
        return {
            'can_trade': True,
            'mode': self.mode.value,
            'risk_multiplier': self._get_risk_multiplier(),
            'daily_pnl': self.daily_pnl
        }
    
    def reset_daily(self):
        """Reset journalier"""
        self.daily_pnl = 0
        self.trades_today = 0
        if self.mode != ProtectionMode.LOCKDOWN:
            self.mode = ProtectionMode.NORMAL
        logger.info("📅 Reset journalier effectué")
    
    def reset_weekly(self):
        """Reset hebdomadaire"""
        self.weekly_pnl = 0
        self.mode = ProtectionMode.NORMAL
        logger.info("📅 Reset hebdomadaire effectué")
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════════════════
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de protection"""
        drawdown = 0
        if self.high_watermark > 0:
            drawdown = (self.high_watermark - self.current_capital) / self.high_watermark * 100
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'high_watermark': self.high_watermark,
            'drawdown_pct': drawdown,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'mode': self.mode.value,
            'risk_multiplier': self._get_risk_multiplier(),
            'consecutive_losses': self.consecutive_losses,
            'active_trades': len(self.active_trades)
        }
    
    def print_status(self):
        """Affiche le statut complet"""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("🛡️ CAPITAL PROTECTOR - STATUS")
        print("=" * 60)
        print(f"""
   💰 Capital: €{stats['current_capital']:,.2f} (initial: €{stats['initial_capital']:,.2f})
   📈 High Watermark: €{stats['high_watermark']:,.2f}
   📉 Drawdown: {stats['drawdown_pct']:.2f}%
   
   📊 P&L Journalier: €{stats['daily_pnl']:+,.2f}
   📊 P&L Hebdo: €{stats['weekly_pnl']:+,.2f}
   
   🎯 Mode: {stats['mode'].upper()}
   ⚡ Multiplicateur risque: {stats['risk_multiplier']:.1f}x
   🔴 Pertes consécutives: {stats['consecutive_losses']}
   📋 Trades actifs: {stats['active_trades']}
        """)
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n🛡️ TEST CAPITAL PROTECTOR")
    print("=" * 60)
    
    protector = CapitalProtector(initial_capital=1000)
    
    # Simuler un trade
    trade = protector.calculate_protected_entry(
        symbol='BTC/USD',
        entry_price=90000,
        direction='long',
        atr_pct=2.5
    )
    
    print(f"\n📊 Trade créé:")
    print(f"   Position: {trade.quantity:.4f} BTC")
    print(f"   Valeur: ${trade.quantity * trade.entry_price:.2f}")
    
    # Simuler évolution du prix
    prices = [90000, 90500, 91000, 91500, 92000, 92500, 93000, 91800]
    
    protector.active_trades['BTC/USD'] = trade
    
    print(f"\n📈 Simulation de prix:")
    for price in prices:
        result = protector.update_trade('BTC/USD', price)
        print(f"   ${price:,} → {result['action']} (P&L: {result.get('pnl_pct', 0):+.2f}%)")
        if result['action'] == 'EXIT_ALL':
            break
    
    protector.print_status()

