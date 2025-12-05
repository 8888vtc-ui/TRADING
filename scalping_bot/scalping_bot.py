"""
🔥 BOT DE SCALPING ULTRA-OPTIMISÉ NASDAQ V2.1
=============================================
Version: 2.1 - Avec News Sentiment & Protection Division/0
Stratégie: Confluence multi-indicateurs + News
Timeframe: 1-5 minutes
Déploiement: Railway (gratuit)

CARACTÉRISTIQUES:
- 7 indicateurs en confluence
- 📰 Intégration News Sentiment API
- ✅ Protection contre division par zéro
- Gestion de risque stricte (0.5% par trade)
- Trailing stop adaptatif
- Horaires de trading optimaux
- Scan toutes les 60 secondes

OBJECTIFS:
- Win Rate: 65-75%
- Ratio R/R: 1:2
- Max 20 trades/jour
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

from scalping_strategy import ScalpingStrategy
from scalping_risk import ScalpingRiskManager
from news_sentiment import get_sentiment_analyzer

# ═══════════════════════════════════════════════════════════
# CONFIGURATION DU LOGGING
# ═══════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# CHARGEMENT DES VARIABLES D'ENVIRONNEMENT
# ═══════════════════════════════════════════════════════════
load_dotenv('../alpaca_api_keys.env')
load_dotenv('alpaca_api_keys.env')

# Debug: Afficher les variables disponibles
print("🔍 DEBUG - Variables d'environnement Alpaca (Scalping Bot):")
print(f"   ALPACA_API_KEY: {os.getenv('ALPACA_API_KEY', 'NON DÉFINIE')[:10] if os.getenv('ALPACA_API_KEY') else 'NON DÉFINIE'}...")
print(f"   ALPACA_SECRET_KEY: {'DÉFINIE' if os.getenv('ALPACA_SECRET_KEY') else 'NON DÉFINIE'}")

# Configuration API
API_KEY = os.getenv('ALPACA_API_KEY') or os.getenv('APCA_API_KEY_ID')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY') or os.getenv('APCA_API_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL') or os.getenv('APCA_API_BASE_URL') or 'https://paper-api.alpaca.markets'

print(f"   API_KEY final: {'DÉFINIE' if API_KEY else 'NON DÉFINIE'}")
print(f"   SECRET_KEY final: {'DÉFINIE' if SECRET_KEY else 'NON DÉFINIE'}")
print(f"   BASE_URL final: {BASE_URL}")

# Vérifier que les clés sont présentes
if not API_KEY:
    print("❌ ERREUR: Aucune clé API trouvée!")
    raise ValueError("ALPACA_API_KEY ou APCA_API_KEY_ID requis")

if not SECRET_KEY:
    print("❌ ERREUR: Aucune clé secrète trouvée!")
    raise ValueError("ALPACA_SECRET_KEY ou APCA_API_SECRET_KEY requis")

# Définir les variables pour la bibliothèque Alpaca
os.environ['APCA_API_KEY_ID'] = API_KEY
os.environ['APCA_API_SECRET_KEY'] = SECRET_KEY
os.environ['APCA_API_BASE_URL'] = BASE_URL

print("✅ Variables configurées pour Alpaca API")

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════
NY_TZ = pytz.timezone('America/New_York')
PARIS_TZ = pytz.timezone('Europe/Paris')

# Symboles à trader (Haute volatilité pour scalping)
SCALPING_SYMBOLS = [
    'TSLA',   # Tesla - Très volatile
    'NVDA',   # NVIDIA - Tech volatile
    'AMD',    # AMD - Semi-conducteurs
    'QQQ',    # ETF NASDAQ (liquide)
    'SPY',    # ETF S&P 500 (très liquide)
    'META',   # Meta - Volatile
    'AAPL',   # Apple - Liquide
    'MSFT',   # Microsoft - Stable mais liquide
]

# Horaires de scalping optimaux (heure New York)
# Plus agressif que le swing trading
SCALPING_HOURS = {
    # Session d'ouverture - MEILLEURE pour scalping
    'session1_start': (9, 35),    # 09:35 NY (5 min après ouverture)
    'session1_end': (11, 30),     # 11:30 NY
    
    # Session Power Hour - Très bonne
    'session2_start': (15, 0),    # 15:00 NY
    'session2_end': (15, 55),     # 15:55 NY (5 min avant fermeture)
}

# Intervalle de scan (plus fréquent pour scalping)
SCAN_INTERVAL_SECONDS = 60  # Toutes les 60 secondes


class ScalpingBot:
    """
    Bot de Scalping Ultra-Optimisé V2.1
    ====================================
    - Trades rapides avec gestion de risque stricte
    - Intégration News Sentiment
    - Protection division par zéro
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("🔥 INITIALISATION DU BOT DE SCALPING V2.1")
        logger.info("=" * 60)
        
        # Connexion API Alpaca
        try:
            self.api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
            account = self.api.get_account()
            
            logger.info("✅ Connexion API réussie")
            logger.info(f"📈 Pouvoir d'achat: ${float(account.buying_power):,.2f}")
            logger.info(f"💰 Valeur du portfolio: ${float(account.portfolio_value):,.2f}")
            
            trading_mode = "Paper Trading" if 'paper' in BASE_URL else "⚠️ LIVE TRADING"
            logger.info(f"🎯 Mode: {trading_mode}")
            
            initial_capital = float(account.portfolio_value)
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion API: {e}")
            raise
        
        # Initialiser l'analyseur de sentiment
        self.sentiment_analyzer = get_sentiment_analyzer()
        logger.info("📰 Analyseur de sentiment initialisé")
        
        # Initialiser la stratégie et le risk manager
        self.strategy = ScalpingStrategy()
        self.risk_manager = ScalpingRiskManager(initial_capital=initial_capital)
        
        # Configuration
        self.symbols = SCALPING_SYMBOLS
        self.last_scan_time = None
        
        # Stats de session
        self.session_stats = {
            'signals_generated': 0,
            'trades_executed': 0,
            'scans_completed': 0
        }
        
        logger.info(f"📊 Symboles: {', '.join(self.symbols)}")
        logger.info(f"⏱️ Scan: toutes les {SCAN_INTERVAL_SECONDS} secondes")
        logger.info("✅ Bot Scalping initialisé avec succès")
    
    def is_scalping_time(self) -> tuple:
        """
        Vérifie si c'est une bonne heure pour le scalping
        
        Returns:
            tuple: (is_scalping_time, session_name, time_info)
        """
        now_ny = datetime.now(NY_TZ)
        now_paris = datetime.now(PARIS_TZ)
        current_time = (now_ny.hour, now_ny.minute)
        
        time_info = f"{now_paris.strftime('%H:%M:%S')} Paris | {now_ny.strftime('%H:%M:%S')} New York"
        
        # Weekend = pas de trading
        if now_ny.weekday() >= 5:
            return False, "Weekend", time_info
        
        # Vérifier Session 1 (Ouverture)
        if (SCALPING_HOURS['session1_start'] <= current_time <= SCALPING_HOURS['session1_end']):
            return True, "🌅 Session Ouverture", time_info
        
        # Vérifier Session 2 (Power Hour)
        if (SCALPING_HOURS['session2_start'] <= current_time <= SCALPING_HOURS['session2_end']):
            return True, "⚡ Power Hour", time_info
        
        # Hors session
        return False, "Hors session scalping", time_info
    
    def get_market_data(self, symbol: str, timeframe: str = '1Min', limit: int = 100) -> pd.DataFrame:
        """
        Récupère les données de marché pour un symbole
        
        Args:
            symbol: Symbole à récupérer
            timeframe: '1Min' ou '5Min'
            limit: Nombre de barres
        
        Returns:
            DataFrame avec OHLCV
        """
        try:
            bars = self.api.get_bars(
                symbol,
                timeframe,
                limit=limit,
                feed='iex'  # Données gratuites IEX
            ).df
            
            if bars.empty:
                return pd.DataFrame()
            
            # Reset index et renommer les colonnes
            bars = bars.reset_index()
            bars.columns = [col.lower() for col in bars.columns]
            
            if 'timestamp' in bars.columns:
                bars['timestamp'] = pd.to_datetime(bars['timestamp'])
                bars = bars.set_index('timestamp')
            
            return bars
            
        except Exception as e:
            logger.error(f"❌ Erreur données {symbol}: {e}")
            return pd.DataFrame()
    
    def execute_buy(self, symbol: str, signal_data: dict) -> bool:
        """
        Exécute un ordre d'achat avec gestion de risque
        """
        try:
            # Récupérer le prix actuel
            quote = self.api.get_latest_quote(symbol)
            current_price = float(quote.ask_price) if quote.ask_price else signal_data['entry_price']
            
            # Calculer la taille de position
            position_info = self.risk_manager.calculate_position_size(
                entry_price=current_price,
                stop_loss=signal_data['stop_loss'],
                symbol=symbol,
                volatility_pct=signal_data.get('indicators', {}).get('atr_pct', 1.0)
            )
            
            if not position_info['allowed']:
                logger.warning(f"⚠️ Position refusée: {position_info['reason']}")
                return False
            
            shares = position_info['shares']
            
            if shares < 1:
                logger.warning(f"⚠️ Position trop petite pour {symbol}")
                return False
            
            # Passer l'ordre
            order = self.api.submit_order(
                symbol=symbol,
                qty=shares,
                side='buy',
                type='market',
                time_in_force='day'
            )
            
            logger.info(f"🚀 ORDRE D'ACHAT ENVOYÉ: {symbol}")
            logger.info(f"   Actions: {shares}")
            logger.info(f"   Prix estimé: ${current_price:.2f}")
            logger.info(f"   Valeur: ${shares * current_price:.2f}")
            logger.info(f"   Stop Loss: ${signal_data['stop_loss']:.2f}")
            logger.info(f"   Take Profit: ${signal_data['take_profit']:.2f}")
            
            # Enregistrer la position
            self.risk_manager.register_trade_entry(
                symbol=symbol,
                shares=shares,
                entry_price=current_price,
                stop_loss=signal_data['stop_loss'],
                take_profit=signal_data['take_profit'],
                signal_data=signal_data
            )
            
            self.session_stats['trades_executed'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution achat {symbol}: {e}")
            return False
    
    def execute_sell(self, symbol: str, reason: str = 'Signal') -> bool:
        """
        Ferme une position existante
        """
        try:
            # Vérifier si on a une position
            positions = self.api.list_positions()
            position = next((p for p in positions if p.symbol == symbol), None)
            
            if not position:
                logger.warning(f"⚠️ Pas de position à vendre pour {symbol}")
                return False
            
            shares = int(position.qty)
            current_price = float(position.current_price)
            
            # Passer l'ordre de vente
            order = self.api.submit_order(
                symbol=symbol,
                qty=shares,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            # Enregistrer la sortie
            self.risk_manager.register_trade_exit(
                symbol=symbol,
                exit_price=current_price,
                exit_reason=reason
            )
            
            logger.info(f"📤 POSITION FERMÉE: {symbol}")
            logger.info(f"   Actions: {shares}")
            logger.info(f"   Prix: ${current_price:.2f}")
            logger.info(f"   Raison: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vente {symbol}: {e}")
            return False
    
    def check_open_positions(self):
        """
        Vérifie les positions ouvertes pour trailing stop et exits
        """
        try:
            positions = self.api.list_positions()
            
            for position in positions:
                symbol = position.symbol
                current_price = float(position.current_price)
                entry_price = float(position.avg_entry_price)
                
                # Mettre à jour le highest price pour trailing stop
                self.risk_manager.update_position_price(symbol, current_price)
                
                # Vérifier si on doit sortir
                if symbol in self.risk_manager.open_positions:
                    pos_data = self.risk_manager.open_positions[symbol]
                    highest_price = pos_data.get('highest_price', entry_price)
                    
                    exit_check = self.strategy.should_exit_position(
                        entry_price=entry_price,
                        current_price=current_price,
                        highest_price=highest_price,
                        position_data=pos_data
                    )
                    
                    if exit_check['should_exit']:
                        self.execute_sell(symbol, exit_check['reason'])
                    else:
                        # Log du profit en cours
                        profit_pct = exit_check.get('current_profit_pct', 0)
                        if abs(profit_pct) > 0.1:  # Ne log que si > 0.1%
                            emoji = "📈" if profit_pct > 0 else "📉"
                            logger.debug(f"{emoji} {symbol}: {profit_pct:+.2f}%")
                            
        except Exception as e:
            logger.error(f"❌ Erreur vérification positions: {e}")
    
    def scan_for_signals(self):
        """
        Scanne tous les symboles pour des opportunités de scalping
        Avec intégration News Sentiment
        """
        is_time, session, time_info = self.is_scalping_time()
        
        logger.info(f"🔍 SCAN SCALPING V2.1 - {time_info}")
        
        if not is_time:
            logger.info(f"🔒 {session} - Vérification des positions uniquement")
            self.check_open_positions()
            return
        
        logger.info(f"⚡ {session} - Recherche d'opportunités")
        
        # Vérifier si trading autorisé
        allowed, reason = self.risk_manager.check_trading_allowed()
        if not allowed:
            logger.warning(f"⚠️ Trading bloqué: {reason}")
            self.check_open_positions()
            return
        
        self.session_stats['scans_completed'] += 1
        
        # Scanner chaque symbole
        for symbol in self.symbols:
            # Skip si déjà en position
            if symbol in self.risk_manager.open_positions:
                continue
            
            # 📰 Vérifier le sentiment des news
            should_trade, sentiment_reason, sentiment_score = self.sentiment_analyzer.should_trade(symbol)
            
            if not should_trade:
                logger.info(f"📰 {symbol}: Skip - {sentiment_reason}")
                continue
            
            # Récupérer les données
            df = self.get_market_data(symbol, timeframe='1Min', limit=100)
            
            if df.empty:
                continue
            
            # Générer le signal AVEC le sentiment
            signal = self.strategy.generate_signal(df, news_sentiment=sentiment_score)
            
            if signal['signal'] == 'BUY' and signal['confidence'] >= 60:
                self.session_stats['signals_generated'] += 1
                
                logger.info(f"🎯 SIGNAL ACHAT: {symbol}")
                logger.info(f"   Confiance: {signal['confidence']:.1f}%")
                logger.info(f"   Score: {signal['score']}/{signal['max_score']}")
                logger.info(f"   📰 Sentiment: {sentiment_score:.2f} ({sentiment_reason})")
                for reason in signal.get('reasons', [])[:5]:
                    logger.info(f"   {reason}")
                
                # Exécuter l'achat
                self.execute_buy(symbol, signal)
        
        # Vérifier les positions existantes
        self.check_open_positions()
        
        # Résumé périodique
        if self.session_stats['scans_completed'] % 10 == 0:
            self.risk_manager.print_daily_summary()
    
    def run(self):
        """
        Boucle principale du bot
        """
        logger.info("=" * 60)
        logger.info("🔥 DÉMARRAGE DU BOT DE SCALPING")
        logger.info("=" * 60)
        
        # Premier scan immédiat
        self.scan_for_signals()
        
        # Scheduler pour scans réguliers
        schedule.every(SCAN_INTERVAL_SECONDS).seconds.do(self.scan_for_signals)
        
        logger.info(f"⏰ Scan programmé toutes les {SCAN_INTERVAL_SECONDS} secondes")
        logger.info("🚀 Bot en cours d'exécution...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Arrêt demandé par l'utilisateur")
                self.risk_manager.print_daily_summary()
                break
                
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")
                time.sleep(10)


# ═══════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("🔥 BOT DE SCALPING NASDAQ - DÉMARRAGE")
        logger.info("=" * 60)
        
        bot = ScalpingBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()

