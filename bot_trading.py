"""
🤖 BOT DE TRADING AUTOMATIQUE NASDAQ 100
=========================================
Stratégie : Long uniquement avec stops de protection
Horaires : Optimisés pour les meilleures heures de trading
Déploiement : Railway (gratuit)
"""

import os
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import schedule
from alpaca_trade_api import REST
import pandas as pd

from strategy import TradingStrategy
from risk_manager import RiskManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv('alpaca_api_keys.env')

# Configuration
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

# Timezone
NY_TZ = pytz.timezone('America/New_York')
PARIS_TZ = pytz.timezone('Europe/Paris')

# Symboles à trader (Top NASDAQ 100)
SYMBOLS = ['QQQ', 'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA']

# Horaires de trading optimaux (heure New York)
TRADING_HOURS = {
    'morning_start': 10,    # 10:30 NY = 16:30 Paris
    'morning_start_min': 30,
    'morning_end': 12,      # 12:00 NY = 18:00 Paris
    'morning_end_min': 0,
    'afternoon_start': 14,  # 14:00 NY = 20:00 Paris
    'afternoon_start_min': 0,
    'afternoon_end': 15,    # 15:30 NY = 21:30 Paris
    'afternoon_end_min': 30,
}


class TradingBot:
    """Bot de trading automatique pour le NASDAQ 100"""
    
    def __init__(self):
        """Initialise le bot"""
        logger.info("=" * 60)
        logger.info("🤖 DÉMARRAGE DU BOT DE TRADING NASDAQ 100")
        logger.info("=" * 60)
        
        # Connexion à l'API Alpaca
        self.api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
        
        # Vérifier la connexion
        self._check_connection()
        
        # Initialiser la stratégie et le gestionnaire de risques
        self.strategy = TradingStrategy(self.api)
        self.risk_manager = RiskManager(self.api)
        
        # État du bot
        self.is_running = True
        self.trades_today = 0
        self.last_scan_time = None
        
        logger.info(f"📊 Symboles surveillés: {', '.join(SYMBOLS)}")
        logger.info("✅ Bot initialisé avec succès")
    
    def _check_connection(self):
        """Vérifie la connexion à l'API"""
        try:
            account = self.api.get_account()
            logger.info(f"✅ Connexion API réussie")
            logger.info(f"💰 Capital: ${float(account.cash):,.2f}")
            logger.info(f"📈 Pouvoir d'achat: ${float(account.buying_power):,.2f}")
            logger.info(f"🎯 Mode: Paper Trading")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            raise
    
    def is_market_open(self):
        """Vérifie si le marché est ouvert"""
        try:
            clock = self.api.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Erreur vérification marché: {e}")
            return False
    
    def is_optimal_trading_time(self):
        """Vérifie si c'est un moment optimal pour trader"""
        now = datetime.now(NY_TZ)
        current_hour = now.hour
        current_minute = now.minute
        current_time = current_hour * 60 + current_minute
        
        # Session du matin: 10:30 - 12:00 NY
        morning_start = TRADING_HOURS['morning_start'] * 60 + TRADING_HOURS['morning_start_min']
        morning_end = TRADING_HOURS['morning_end'] * 60 + TRADING_HOURS['morning_end_min']
        
        # Session de l'après-midi: 14:00 - 15:30 NY
        afternoon_start = TRADING_HOURS['afternoon_start'] * 60 + TRADING_HOURS['afternoon_start_min']
        afternoon_end = TRADING_HOURS['afternoon_end'] * 60 + TRADING_HOURS['afternoon_end_min']
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return is_morning or is_afternoon
    
    def get_trading_session(self):
        """Retourne la session de trading actuelle"""
        now = datetime.now(NY_TZ)
        current_hour = now.hour
        current_minute = now.minute
        current_time = current_hour * 60 + current_minute
        
        morning_start = TRADING_HOURS['morning_start'] * 60 + TRADING_HOURS['morning_start_min']
        morning_end = TRADING_HOURS['morning_end'] * 60 + TRADING_HOURS['morning_end_min']
        afternoon_start = TRADING_HOURS['afternoon_start'] * 60 + TRADING_HOURS['afternoon_start_min']
        afternoon_end = TRADING_HOURS['afternoon_end'] * 60 + TRADING_HOURS['afternoon_end_min']
        
        if morning_start <= current_time <= morning_end:
            return "🌅 Session Matin (10:30-12:00 NY)"
        elif afternoon_start <= current_time <= afternoon_end:
            return "🌆 Session Après-midi (14:00-15:30 NY)"
        elif current_time < morning_start:
            return "⏳ Attente ouverture session matin"
        elif morning_end < current_time < afternoon_start:
            return "😴 Pause déjeuner (pas de trading)"
        else:
            return "🌙 Marché fermé ou hors horaires optimaux"
    
    def scan_and_trade(self):
        """Scan les symboles et exécute les trades"""
        now_ny = datetime.now(NY_TZ)
        now_paris = datetime.now(PARIS_TZ)
        
        logger.info("-" * 60)
        logger.info(f"🔍 SCAN - {now_paris.strftime('%H:%M:%S')} Paris | {now_ny.strftime('%H:%M:%S')} New York")
        logger.info(f"📍 {self.get_trading_session()}")
        
        # Vérifier si le marché est ouvert
        if not self.is_market_open():
            logger.info("🔒 Marché fermé - Pas de trading")
            return
        
        # Vérifier si c'est un moment optimal
        if not self.is_optimal_trading_time():
            logger.info("⏰ Hors horaires optimaux - Scan uniquement, pas d'exécution")
            # On peut quand même scanner pour info
            self._scan_only()
            return
        
        logger.info("✅ Horaires optimaux - Trading actif")
        
        # Vérifier les limites de risque
        if not self.risk_manager.can_trade():
            logger.warning("⚠️ Limites de risque atteintes - Pas de nouveaux trades")
            return
        
        # Scanner chaque symbole
        for symbol in SYMBOLS:
            try:
                self._analyze_and_trade(symbol)
            except Exception as e:
                logger.error(f"❌ Erreur {symbol}: {e}")
        
        # Gérer les positions existantes (trailing stops, etc.)
        self._manage_positions()
        
        self.last_scan_time = datetime.now()
    
    def _scan_only(self):
        """Scan sans exécution (hors horaires optimaux)"""
        signals = []
        for symbol in SYMBOLS:
            try:
                signal = self.strategy.analyze(symbol)
                if signal['action'] == 'BUY':
                    signals.append(f"{symbol}: Score {signal['score']}/10")
            except Exception as e:
                logger.error(f"Erreur scan {symbol}: {e}")
        
        if signals:
            logger.info(f"📊 Signaux détectés (non exécutés): {', '.join(signals)}")
    
    def _analyze_and_trade(self, symbol):
        """Analyse un symbole et exécute un trade si nécessaire"""
        # Analyser le symbole
        signal = self.strategy.analyze(symbol)
        
        if signal['action'] == 'BUY' and signal['score'] >= 5:
            logger.info(f"📈 SIGNAL ACHAT: {symbol}")
            logger.info(f"   Score: {signal['score']}/10")
            logger.info(f"   Raisons: {', '.join(signal['reasons'])}")
            
            # Calculer la taille de position
            position_size = self.risk_manager.calculate_position_size(
                symbol=symbol,
                entry_price=signal['entry_price'],
                stop_loss=signal['stop_loss']
            )
            
            if position_size > 0:
                # Exécuter le trade
                self._execute_trade(
                    symbol=symbol,
                    qty=position_size,
                    entry_price=signal['entry_price'],
                    stop_loss=signal['stop_loss'],
                    take_profit=signal['take_profit']
                )
        elif signal['action'] == 'HOLD':
            logger.debug(f"⏸️ {symbol}: Pas de signal (Score: {signal['score']}/10)")
    
    def _execute_trade(self, symbol, qty, entry_price, stop_loss, take_profit):
        """Exécute un trade avec protection"""
        try:
            # Ordre bracket (entrée + stop loss + take profit)
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc',
                order_class='bracket',
                take_profit={'limit_price': round(take_profit, 2)},
                stop_loss={
                    'stop_price': round(stop_loss, 2),
                    'limit_price': round(stop_loss * 0.99, 2)  # Stop limit légèrement sous
                }
            )
            
            logger.info(f"✅ ORDRE EXÉCUTÉ: {symbol}")
            logger.info(f"   Quantité: {qty} actions")
            logger.info(f"   Stop Loss: ${stop_loss:.2f}")
            logger.info(f"   Take Profit: ${take_profit:.2f}")
            logger.info(f"   Order ID: {order.id}")
            
            self.trades_today += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution {symbol}: {e}")
    
    def _manage_positions(self):
        """Gère les positions existantes"""
        try:
            positions = self.api.list_positions()
            
            if positions:
                logger.info(f"📊 Positions ouvertes: {len(positions)}")
                
                for pos in positions:
                    symbol = pos.symbol
                    qty = int(pos.qty)
                    entry = float(pos.avg_entry_price)
                    current = float(pos.current_price)
                    pnl = float(pos.unrealized_pl)
                    pnl_pct = float(pos.unrealized_plpc) * 100
                    
                    logger.info(f"   {symbol}: {qty} @ ${entry:.2f} | "
                              f"Actuel: ${current:.2f} | "
                              f"P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
                    
                    # Vérifier si on doit ajuster le trailing stop
                    self.risk_manager.update_trailing_stop(pos)
            else:
                logger.info("📭 Aucune position ouverte")
                
        except Exception as e:
            logger.error(f"Erreur gestion positions: {e}")
    
    def get_status(self):
        """Retourne le statut du bot"""
        try:
            account = self.api.get_account()
            positions = self.api.list_positions()
            
            return {
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'positions': len(positions),
                'trades_today': self.trades_today,
                'market_open': self.is_market_open(),
                'optimal_time': self.is_optimal_trading_time(),
                'session': self.get_trading_session()
            }
        except Exception as e:
            logger.error(f"Erreur statut: {e}")
            return None
    
    def run(self):
        """Lance le bot"""
        logger.info("🚀 Bot en cours d'exécution...")
        logger.info(f"⏰ Scan toutes les 5 minutes")
        logger.info("")
        
        # Premier scan immédiat
        self.scan_and_trade()
        
        # Programmer les scans toutes les 5 minutes
        schedule.every(5).minutes.do(self.scan_and_trade)
        
        # Afficher le statut toutes les 30 minutes
        schedule.every(30).minutes.do(self._print_status)
        
        # Boucle principale
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("⏹️ Arrêt du bot demandé...")
                self.is_running = False
            except Exception as e:
                logger.error(f"Erreur boucle principale: {e}")
                time.sleep(60)  # Attendre 1 minute avant de réessayer
        
        logger.info("👋 Bot arrêté")
    
    def _print_status(self):
        """Affiche le statut du bot"""
        status = self.get_status()
        if status:
            logger.info("=" * 60)
            logger.info("📊 STATUT DU BOT")
            logger.info(f"   💰 Cash: ${status['cash']:,.2f}")
            logger.info(f"   📈 Portfolio: ${status['portfolio_value']:,.2f}")
            logger.info(f"   📊 Positions: {status['positions']}")
            logger.info(f"   🔄 Trades aujourd'hui: {status['trades_today']}")
            logger.info(f"   🏪 Marché: {'Ouvert' if status['market_open'] else 'Fermé'}")
            logger.info(f"   ⏰ {status['session']}")
            logger.info("=" * 60)


# Point d'entrée
if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        raise

