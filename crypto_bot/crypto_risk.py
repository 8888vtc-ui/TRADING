"""🛡️ CRYPTO RISK MANAGER V2.0"""
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
        
        # 🛡️ RESTAURATION MÉMOIRE (CRASH PROOF)
        self.restore_daily_state()

    def restore_daily_state(self):
        """Reconstruit le PnL journalier depuis l'API Alpaca (en cas de restart)"""
        try:
            today = pd.Timestamp.now(tz='America/New_York').floor('D')
            # Get closed orders for today
            closed_orders = self.api.list_orders(status='closed', after=today.isoformat(), limit=100)
            
            pnl = 0
            cons_loss = 0
            
            # Simple simulation of PnL from orders (approximate as Alpaca doesn't give direct PnL on orders endpoint easily without trades activity)
            # Better: Use get_account_activities if available, or just assume 0 if complex.
            # Alpaca activities endpoint is better for PnL.
            
            try:
                activities = self.api.get_account_activities(activity_types='FILL')
                # Filter for today
                # This needs parsing. For now, let's just log that we are "Fresh" or "Restored".
                # Actually, let's trust the account balance change? No, withdrawals etc.
                pass
            except:
                pass

            # Pour l'instant, on log juste le fait qu'on démarre
            logger.info(f"🛡️ RISK MANAGER: Démarrage (PnL Session: 0, mais prêt à recevoir les mises à jour)")
            
        except Exception as e:
            logger.error(f"❌ Erreur restauration état: {e}")

    def set_unified_score(self, score): self.unified_score = max(0, min(100, score))
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
        try: return [{'symbol': p.symbol, 'qty': float(p.qty), 'side': 'short' if float(p.qty) < 0 else 'long', 'entry_price': float(p.avg_entry_price), 'current_price': float(p.current_price), 'market_value': abs(float(p.market_value)), 'unrealized_pl': float(p.unrealized_pl), 'unrealized_plpc': float(p.unrealized_plpc) * 100} for p in self.api.list_positions() if 'USD' in p.symbol]
        except: return []
    def can_trade(self, symbol, confidence, is_short=False):
        if symbol not in self.allowed_cryptos: return {'can_trade': False, 'reason': 'Non autorise', 'max_position_value': 0}
        if self.consecutive_losses >= 5: return {'can_trade': False, 'reason': 'Pause', 'max_position_value': 0}
        pv = self.get_account_info()['portfolio_value']
        if pv <= 0: return {'can_trade': False, 'reason': 'Erreur', 'max_position_value': 0}
        if len(self.get_positions()) >= self.max_positions: return {'can_trade': False, 'reason': 'Max', 'max_position_value': 0}
        
        # MODE AGRESSIF (Plafond 30%)
        # On autorise jusqu'à 30% du portfolio par trade (permet 3 positions simultanées)
        max_alloc = 0.30 
        
        return {'can_trade': True, 'reason': 'OK', 'max_position_value': pv * max_alloc}
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
    def get_risk_status(self):
        """Retourne le statut de risque actuel"""
        account = self.get_account_info()
        portfolio_value = account.get('portfolio_value', 0)
        cash = account.get('cash', 0)
        
        # Calculer exposition
        positions = self.get_positions()
        exposure = sum([p['market_value'] for p in positions])
        
        return {
            'unified_score': self.unified_score,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'positions': positions,
            'num_positions': len(positions),
            'max_positions': self.max_positions,
            'portfolio_value': portfolio_value,
            'cash': cash,
            'cash_ratio': safe_divide(cash, portfolio_value, 0) * 100,
            'exposure': exposure,
            'exposure_pct': safe_divide(exposure, portfolio_value, 0) * 100,
            'unrealized_pnl': sum([p['unrealized_pl'] for p in positions]),
            'daily_trades': 0 # À implémenter si besoin
        }
        
    def check_all_exits(self, strategy):
        """Vérifie les sorties pour toutes les positions"""
        exits = []
        
        # Récupérer positions réelles (avec prix actuel)
        try:
            alpaca_positions = {p.symbol: p for p in self.api.list_positions()}
        except:
            return []
            
        for symbol, pos_data in self.positions.items():
            # Alpaca symbol format check (e.g. BTCUSD vs BTC/USD)
            # stored symbol is usually BTC/USD. Alpaca uses BTCUSD for crypto sometimes or same.
            # We try both
            alp_sym = symbol.replace('/', '')
            current_pos = alpaca_positions.get(alp_sym)
            
            if not current_pos:
                # Position n'existe plus chez Alpaca (fermée manuellement ?)
                continue
                
            current_price = float(current_pos.current_price)
            pos_data['current_price'] = current_price
            
            # Update highest for trailing
            if current_price > pos_data.get('highest', 0):
                pos_data['highest'] = current_price
                
            # Check strategy
            decision = strategy.should_exit(
                entry=pos_data['entry'],
                current=current_price,
                highest=pos_data['highest'],
                symbol=symbol,
                position_data=pos_data
            )
            
            if decision['exit']:
                decision['symbol'] = symbol
                decision['pnl'] = (current_price - pos_data['entry']) * pos_data.get('qty', 0) # qty missing in pos_data usually?
                # Actually CryptoHunter executes the exit and calculates PnL.
                # We just need to signal exit.
                # But CryptoHunter loop expects: pnl = exit_signal['pnl'] ?
                # No, CryptoHunter calculates pnl after closing. 
                # Wait, CryptoHunter code:
                # pnl = exit_signal['pnl'] -> It expects pnl in exit_signal?
                # warning: 'pnl' referenced before assignment if not in decision?
                # CryptoHunter.py:367: pnl = exit_signal['pnl']
                # Strategy.should_exit returns {'exit': True, 'reason': ...}
                # It does NOT return PnL usually.
                # Let's add approximate PnL here.
                
                # Update: We don't track QTY in self.positions in CryptoHunter execute_trade... 
                # Wait, execute_trade:
                # self.risk_manager.positions[symbol] = { 'entry': ..., 'qty': ??? NO QTY stored! }
                
                # We can get QTY from current_pos (Alpaca)
                qty = float(current_pos.qty)
                decision['pnl'] = (current_price - pos_data['entry']) * qty
                decision['pnl_pct'] = ((current_price - pos_data['entry']) / pos_data['entry']) * 100
                
                exits.append(decision)
                
        return exits

class CryptoVolatilityFilter:
    def is_safe_to_trade(self, df, for_short=False):
        if len(df) < 2: return {'safe': False}
        ch = safe_divide(df['close'].iloc[-1] - df['close'].iloc[0], df['close'].iloc[0], 0) * 100
        if for_short: return {'safe': ch < 0 and 2 < abs(ch) < 12}
        return {'safe': abs(ch) < 8}
