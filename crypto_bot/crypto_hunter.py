"""
🪙 CRYPTO HUNTER BOT V1.0 - CONSERVATEUR
========================================
Bot de trading crypto automatisé avec priorité sur la protection du capital

STRATÉGIE: Momentum Confirmé
CRYPTOS: BTC, ETH, SOL
RISQUE: Ultra conservateur (0.5% par trade)

Auteur: Trading Bot System
Date: 2024
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import pytz
import schedule

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crypto_hunter.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Alpaca
try:
    import alpaca_trade_api as tradeapi
except ImportError:
    logger.error("❌ alpaca-trade-api non installé. pip install alpaca-trade-api")
    sys.exit(1)

import pandas as pd
import numpy as np

from crypto_strategy import CryptoStrategy
from crypto_risk import CryptoRiskManager, CryptoVolatilityFilter


class CryptoHunterBot:
    """
    🪙 Bot Crypto Hunter - Trading Automatisé Conservateur
    =====================================================
    
    - Focus sur BTC, ETH, SOL
    - Stratégie momentum avec confirmation
    - Gestion du risque ultra stricte
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("🪙 CRYPTO HUNTER BOT V1.0 - DÉMARRAGE")
        logger.info("=" * 60)
        
        # API Alpaca
        self.api = self._init_api()
        
        # Composants
        self.strategy = CryptoStrategy()
        self.risk_manager = CryptoRiskManager(self.api)
        self.volatility_filter = CryptoVolatilityFilter()
        
        # Cryptos à trader
        self.symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        
        # Timeframe (5 minutes pour crypto)
        self.timeframe = '5Min'
        self.bars_needed = 100
        
        # Tracking
        self.last_scan = None
        self.trades_today = 0
        self.signals_today = []
        
        # Timezone
        self.tz = pytz.timezone('America/New_York')
        
        logger.info(f"📊 Cryptos: {self.symbols}")
        logger.info(f"⏰ Timeframe: {self.timeframe}")
        logger.info(f"🛡️ Risque par trade: {self.risk_manager.risk_per_trade*100}%")
        
    def _init_api(self):
        """Initialise l'API Alpaca"""
        api_key = os.environ.get('APCA_API_KEY_ID') or os.environ.get('ALPACA_API_KEY')
        secret_key = os.environ.get('APCA_API_SECRET_KEY') or os.environ.get('ALPACA_SECRET_KEY')
        base_url = os.environ.get('APCA_API_BASE_URL') or os.environ.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not api_key or not secret_key:
            logger.error("❌ Variables d'environnement manquantes!")
            logger.error("   Définir: APCA_API_KEY_ID et APCA_API_SECRET_KEY")
            sys.exit(1)
        
        try:
            api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
            account = api.get_account()
            logger.info(f"✅ Connecté à Alpaca")
            logger.info(f"   Portfolio: ${float(account.portfolio_value):,.2f}")
            logger.info(f"   Cash: ${float(account.cash):,.2f}")
            return api
        except Exception as e:
            logger.error(f"❌ Erreur connexion Alpaca: {e}")
            sys.exit(1)
    
    def get_crypto_data(self, symbol: str) -> pd.DataFrame:
        """Récupère les données crypto"""
        try:
            # Format symbole pour Alpaca
            alpaca_symbol = symbol.replace('/', '')  # BTC/USD -> BTCUSD
            
            bars = self.api.get_crypto_bars(
                alpaca_symbol,
                self.timeframe,
                limit=self.bars_needed
            ).df
            
            if bars.empty:
                logger.warning(f"⚠️ Pas de données pour {symbol}")
                return pd.DataFrame()
            
            # Reformater
            bars = bars.reset_index()
            bars.columns = [c.lower() for c in bars.columns]
            
            if 'timestamp' in bars.columns:
                bars = bars.rename(columns={'timestamp': 'time'})
            
            # Garder colonnes essentielles
            cols = ['time', 'open', 'high', 'low', 'close', 'volume']
            for c in cols:
                if c not in bars.columns and c != 'time':
                    bars[c] = 0
            
            return bars[cols] if 'time' in bars.columns else bars[cols[1:]]
            
        except Exception as e:
            logger.error(f"❌ Erreur données {symbol}: {e}")
            return pd.DataFrame()
    
    def scan_opportunities(self):
        """Scanne toutes les cryptos pour opportunités"""
        logger.info("\n" + "=" * 50)
        logger.info("🔍 SCAN CRYPTO EN COURS...")
        logger.info("=" * 50)
        
        opportunities = []
        
        for symbol in self.symbols:
            try:
                df = self.get_crypto_data(symbol)
                
                if df.empty or len(df) < 60:
                    logger.warning(f"⚠️ {symbol}: Données insuffisantes")
                    continue
                
                # Filtre volatilité
                vol_check = self.volatility_filter.is_safe_to_trade(df)
                if not vol_check['safe']:
                    logger.warning(f"⚠️ {symbol}: {vol_check['reason']}")
                    continue
                
                # Générer signal
                signal = self.strategy.generate_signal(df, symbol)
                
                logger.info(f"📊 {symbol}: {signal['signal']} | Score: {signal.get('score', 0):.1f}/{signal.get('max_score', 12)} | Confiance: {signal.get('confidence', 0):.0f}%")
                
                if signal['signal'] == 'BUY':
                    opportunities.append(signal)
                    
            except Exception as e:
                logger.error(f"❌ Erreur scan {symbol}: {e}")
        
        self.last_scan = datetime.now(self.tz)
        return opportunities
    
    def execute_trade(self, signal: dict) -> bool:
        """Exécute un trade"""
        symbol = signal['symbol']
        
        logger.info(f"\n🎯 TENTATIVE ACHAT {symbol}")
        
        # Vérifier avec risk manager
        position = self.risk_manager.calculate_position_size(
            symbol,
            signal['entry_price'],
            signal['stop_loss'],
            signal['confidence']
        )
        
        if not position['can_trade']:
            logger.warning(f"⛔ Trade refusé: {position['reason']}")
            return False
        
        qty = position['qty']
        
        try:
            # Format symbole Alpaca
            alpaca_symbol = symbol.replace('/', '')
            
            # Passer l'ordre
            order = self.api.submit_order(
                symbol=alpaca_symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            logger.info(f"✅ ORDRE PASSÉ!")
            logger.info(f"   Symbole: {symbol}")
            logger.info(f"   Quantité: {qty}")
            logger.info(f"   Prix estimé: ${signal['entry_price']:.2f}")
            logger.info(f"   Stop Loss: ${signal['stop_loss']:.2f} ({signal['stop_loss_pct']:.1f}%)")
            logger.info(f"   Take Profit: ${signal['take_profit']:.2f} ({signal['take_profit_pct']:.1f}%)")
            logger.info(f"   Order ID: {order.id}")
            
            # Stocker infos position
            self.risk_manager.positions[symbol] = {
                'entry': signal['entry_price'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'highest': signal['entry_price'],
                'order_id': order.id,
                'time': datetime.now(self.tz)
            }
            
            self.trades_today += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ordre: {e}")
            return False
    
    def check_exits(self):
        """Vérifie les sorties de positions"""
        exits = self.risk_manager.check_all_exits(self.strategy)
        
        for exit_signal in exits:
            try:
                symbol = exit_signal['symbol']
                alpaca_symbol = symbol.replace('/', '')
                
                logger.info(f"\n🚪 SORTIE {symbol}: {exit_signal['reason']}")
                
                # Fermer la position
                self.api.close_position(alpaca_symbol)
                
                # Enregistrer le trade
                self.risk_manager.record_trade(exit_signal['pnl'])
                
                # Nettoyer
                if symbol in self.risk_manager.positions:
                    del self.risk_manager.positions[symbol]
                
                logger.info(f"✅ Position fermée: {exit_signal['pnl_pct']:.2f}% (${exit_signal['pnl']:.2f})")
                
            except Exception as e:
                logger.error(f"❌ Erreur fermeture {symbol}: {e}")
    
    def print_status(self):
        """Affiche le statut actuel"""
        status = self.risk_manager.get_risk_status()
        
        logger.info("\n" + "=" * 50)
        logger.info("📊 STATUT CRYPTO HUNTER")
        logger.info("=" * 50)
        logger.info(f"💰 Portfolio: ${status['portfolio_value']:,.2f}")
        logger.info(f"💵 Cash: ${status['cash']:,.2f} ({status['cash_ratio']:.1f}%)")
        logger.info(f"📈 Positions: {status['num_positions']}/{status['max_positions']}")
        logger.info(f"🎯 Exposition: ${status['exposure']:,.2f} ({status['exposure_pct']:.1f}%)")
        logger.info(f"📊 P&L non réalisé: ${status['unrealized_pnl']:,.2f}")
        logger.info(f"📅 P&L journalier: ${status['daily_pnl']:,.2f}")
        logger.info(f"🔢 Trades aujourd'hui: {status['daily_trades']}")
        
        if status['positions']:
            logger.info("\n📋 POSITIONS OUVERTES:")
            for pos in status['positions']:
                logger.info(f"   {pos['symbol']}: {pos['qty']} @ ${pos['entry_price']:.2f} → ${pos['current_price']:.2f} ({pos['unrealized_plpc']:.2f}%)")
    
    def trading_cycle(self):
        """Cycle principal de trading"""
        try:
            # 1. Afficher statut
            self.print_status()
            
            # 2. Vérifier sorties
            self.check_exits()
            
            # 3. Scanner opportunités
            opportunities = self.scan_opportunities()
            
            # 4. Exécuter meilleure opportunité
            if opportunities:
                # Trier par score/confiance
                opportunities.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                best = opportunities[0]
                
                logger.info(f"\n🏆 MEILLEURE OPPORTUNITÉ: {best['symbol']}")
                logger.info(f"   Score: {best['score']:.1f}/{best['max_score']}")
                logger.info(f"   Confiance: {best['confidence']:.0f}%")
                
                self.execute_trade(best)
            else:
                logger.info("\n😴 Pas d'opportunité - En attente...")
            
            logger.info(f"\n⏰ Prochain scan dans 5 minutes...")
            
        except Exception as e:
            logger.error(f"❌ Erreur cycle: {e}")
    
    def run(self):
        """Lance le bot"""
        logger.info("\n🚀 DÉMARRAGE CRYPTO HUNTER BOT")
        logger.info("   Trading 24/7 sur BTC, ETH, SOL")
        logger.info("   Stratégie: Momentum Conservateur")
        logger.info("   Intervalle: 5 minutes\n")
        
        # Premier cycle immédiat
        self.trading_cycle()
        
        # Planifier cycles
        schedule.every(5).minutes.do(self.trading_cycle)
        schedule.every().day.at("00:00").do(self.risk_manager.reset_daily)
        
        # Boucle principale
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)
            except KeyboardInterrupt:
                logger.info("\n⏹️ Arrêt demandé...")
                break
            except Exception as e:
                logger.error(f"❌ Erreur: {e}")
                time.sleep(60)


def main():
    """Point d'entrée"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🪙 CRYPTO HUNTER BOT V1.0                               ║
    ║   Trading Crypto Automatisé - Conservateur                ║
    ║                                                           ║
    ║   Cryptos: BTC, ETH, SOL                                  ║
    ║   Stratégie: Momentum Confirmé                            ║
    ║   Risque: 0.5% par trade                                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    bot = CryptoHunterBot()
    bot.run()


if __name__ == "__main__":
    main()

