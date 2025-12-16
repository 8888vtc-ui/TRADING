"""
🪙 CRYPTO HUNTER BOT V2.0 - AVEC LEVERAGE INTELLIGENT
====================================================
Bot de trading crypto automatisé avec:
- Stratégie Momentum Conservatrice
- Leverage intelligent (quand conditions optimales)
- API Data Marché (Fear & Greed, Dominance)
- Protection du capital prioritaire

CRYPTOS: BTC, ETH, SOL
RISQUE: Conservateur avec boost leverage occasionnel

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
from market_data_api import CryptoMarketData, MarketConditionChecker
from leverage_manager import LeverageManager, LeverageLevel


from market_scanner import MarketScannerAgent

class CryptoHunterBot:
    """
    🪙 Bot Crypto Hunter V2.0 - Avec Leverage Intelligent
    =====================================================
    
    NOUVEAUTÉS V2.0:
    - Leverage intelligent (max 2x) quand confiance > 85%
    - API Fear & Greed Index
    - API Dominance BTC
    - Vérification conditions marché avant chaque trade
    """
    
    def __init__(self):
        logger.info("=" * 60)
        logger.info("🪙 CRYPTO HUNTER BOT V2.0 - LEVERAGE INTELLIGENT")
        logger.info("=" * 60)
        
        # API Alpaca
        self.api = self._init_api()
        
        # Composants principaux
        self.strategy = CryptoStrategy()
        self.risk_manager = CryptoRiskManager(self.api)
        self.volatility_filter = CryptoVolatilityFilter()
        
        # NOUVEAU: Market Data & Leverage & AI Agent
        self.market_data = CryptoMarketData()
        self.market_checker = MarketConditionChecker()
        self.leverage_manager = LeverageManager(self.market_checker)
        self.ai_scanner = MarketScannerAgent(self.api)
        
        # NOUVEAU: Sentiment Analyzer (Double Garantie Gemini/Claude)
        # Hack path pour import news_sentiment du dossier voisin
        sys.path.append(os.path.join(os.getcwd(), 'scalping_bot'))
        from news_sentiment import get_sentiment_analyzer
        self.sentiment_analyzer = get_sentiment_analyzer()
        logger.info("📰 AI Sentiment Analyzer intégré au Crypto Hunter")
        
        # Cryptos à trader
        # Cryptos à trader (Max Trading Mode + Volatility Team)
        self.symbols = [
            'BTC/USD', 'ETH/USD', 'SOL/USD', 
            'AVAX/USD', 'MATIC/USD', 'LINK/USD', 'ADA/USD', 'XRP/USD',
            'DOT/USD', 'UNI/USD', 'LTC/USD', 'BCH/USD', 'NEAR/USD', 'ATOM/USD'
        ]
        
        # Timeframe
        self.timeframe = '5Min'
        self.bars_needed = 100
        
        # Tracking
        self.last_scan = None
        self.trades_today = 0
        self.leveraged_trades_today = 0
        
        # Timezone
        self.tz = pytz.timezone('America/New_York')
        
        # Afficher config
        self._print_config()
    
    def _print_config(self):
        """Affiche la configuration"""
        logger.info(f"\n📊 CONFIGURATION:")
        logger.info(f"   Cryptos: {self.symbols}")
        logger.info(f"   Timeframe: {self.timeframe}")
        logger.info(f"   Risque par trade: {self.risk_manager.base_risk_per_trade*100}%")
        logger.info(f"   Max positions: {self.risk_manager.max_positions}")
        logger.info(f"   Leverage max: {self.leverage_manager.max_leverage}x")
        logger.info(f"   Leverage activé si confiance > 80%")
        logger.info(f"   APIs: Fear & Greed, BTC Dominance\n")
        
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
    
    def check_market_conditions(self) -> dict:
        """
        NOUVEAU: Vérifie les conditions de marché via APIs
        """
        logger.info("\n🌍 VÉRIFICATION CONDITIONS MARCHÉ...")
        
        try:
            # Fear & Greed
            fg = self.market_data.get_fear_greed_index()
            logger.info(f"   🎭 Fear & Greed: {fg['value']} ({fg['classification']})")
            
            # BTC Dominance
            dom = self.market_data.get_btc_dominance()
            if dom.get('valid'):
                logger.info(f"   👑 BTC Dominance: {dom['btc_dominance']}%")
                logger.info(f"   📈 Market Cap 24h: {dom.get('market_cap_change_24h', 0):.2f}%")
            
            # Décision globale
            decision = self.market_data.should_trade_now()
            
            logger.info(f"\n   📊 VERDICT MARCHÉ:")
            logger.info(f"      Peut trader: {'✅' if decision['can_trade'] else '❌'}")
            logger.info(f"      Peut leverage: {'✅' if decision['can_leverage'] else '❌'}")
            if decision['leverage_multiplier'] > 1:
                logger.info(f"      Leverage autorisé: {decision['leverage_multiplier']}x")
            
            for reason in decision['reasons']:
                logger.info(f"      {reason}")
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification marché: {e}")
            return {
                'can_trade': True,
                'can_leverage': False,
                'leverage_multiplier': 1.0,
                'confidence_adjustment': 0,
                'reasons': ['⚠️ Données marché non disponibles']
            }
    
    def get_crypto_data(self, symbol: str) -> pd.DataFrame:
        """Récupère les données crypto"""
        try:
            # ALPACA V2 requires 'BTC/USD' format, NOT 'BTCUSD'
            alpaca_symbol = symbol 
            
            bars = self.api.get_crypto_bars(
                alpaca_symbol,
                self.timeframe,
                limit=self.bars_needed
            ).df
            
            if bars.empty:
                logger.warning(f"⚠️ Pas de données pour {symbol}")
                return pd.DataFrame()
            
            bars = bars.reset_index()
            bars.columns = [c.lower() for c in bars.columns]
            
            if 'timestamp' in bars.columns:
                bars = bars.rename(columns={'timestamp': 'time'})
            
            cols = ['time', 'open', 'high', 'low', 'close', 'volume']
            for c in cols:
                if c not in bars.columns and c != 'time':
                    bars[c] = 0
            
            return bars[cols] if 'time' in bars.columns else bars[cols[1:]]
            
        except Exception as e:
            logger.error(f"❌ Erreur données {symbol}: {e}")
            return pd.DataFrame()
    
        self.last_scan = datetime.now(self.tz)
        return opportunities
    
    def _scan_single_symbol(self, symbol, market_conditions, confidence_adj):
        """Helper pour scanner un seul symbole (Multi-thread secure)"""
        try:
            df = self.get_crypto_data(symbol)
            if df.empty or len(df) < 60:
                logger.warning(f"⚠️ {symbol}: Données insuffisantes")
                return None
            
            # Filtre volatilité
            vol_check = self.volatility_filter.is_safe_to_trade(df)
            if not vol_check['safe']:
                return None
            
            # 📰 AI SENTIMENT CHECK (Double Garantie)
            should_trade, sent_reason, sent_score = self.sentiment_analyzer.should_trade(symbol)
            if not should_trade:
                # logger.info(f"🛑 {symbol}: Rejet AI ({sent_reason})")
                return None
            
            # Générer signal
            signal = self.strategy.generate_signal(df, symbol)
            
            # Ajuster confiance selon marché
            if signal.get('confidence'):
                signal['confidence'] += confidence_adj
                signal['confidence'] = max(0, min(100, signal['confidence']))
            
            # 🚀 CHECK MOONSHOT (Prioritaire)
            moonshot = self.scan_moonshots(df, symbol)
            if moonshot:
                signal = moonshot
                logger.info(f"🚀 MOONSHOT ACTIVÉ pour {symbol}!")
            
            logger.info(f"📊 {symbol}: {signal['signal']} | Score: {signal.get('score', 0):.1f}/{signal.get('max_score', 12)} | Confiance: {signal.get('confidence', 0):.0f}%")
            
            # 🛠️ MODE CALIBRATION (Log réduit pour performance)
            if signal['signal'] == 'BUY':
                 # NOUVEAU: Vérifier si leverage possible
                leverage_decision = self.leverage_manager.can_use_leverage(signal, market_conditions)
                signal['leverage_decision'] = leverage_decision
                
                if leverage_decision.can_leverage:
                    logger.info(f"   🚀 LEVERAGE {leverage_decision.multiplier}x disponible!")
                return signal
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur scan {symbol}: {e}")
            return None

    def scan_opportunities(self, market_conditions: dict) -> list:
        """Scanne les cryptos pour opportunités (PARALLÈLE V12)"""
        logger.info("\n" + "=" * 50)
        logger.info("⚡ SCAN CRYPTO TURBO (PARALLEL) EN COURS...")
        logger.info("=" * 50)
        
        opportunities = []
        confidence_adj = market_conditions.get('confidence_adjustment', 0)
        
        # Exécution Parallèle (V12 Engine)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Lancer tous les scans en même temps
            futures = {executor.submit(self._scan_single_symbol, sym, market_conditions, confidence_adj): sym for sym in self.symbols}
            
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res and res.get('signal') == 'BUY':
                    opportunities.append(res)
        
        self.last_scan = datetime.now(self.tz)
        return opportunities
    
    def scan_moonshots(self, df: pd.DataFrame, symbol: str) -> dict:
        """
        🚀 DÉTECTION MOONSHOT (PUMP)
        Cherche des mouvements explosifs (>3% en 5min + Volume x2)
        """
        try:
            if len(df) < 5: return {}
            
            # Dernières bougies
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Variation prix
            price_change = ((last['close'] - last['open']) / last['open']) * 100
            
            # Volume anormal
            avg_vol = df['volume'].rolling(20).mean().iloc[-1]
            vol_mult = last['volume'] / avg_vol if avg_vol > 0 else 0
            
            # Critères MOONSHOT
            if price_change > 3.0 and vol_mult > 2.0:
                logger.info(f"🚀 MOONSHOT DÉTECTÉ sur {symbol} (+{price_change:.1f}% | Vol {vol_mult:.1f}x)")
                return {
                    'signal': 'BUY',
                    'symbol': symbol,
                    'confidence': 95, # Confiance max
                    'score': 12,
                    'max_score': 12,
                    'reasons': [f"🚀 PUMP DÉTECTÉ (+{price_change:.1f}%)", f"📊 VOLUME EXPLOSIF ({vol_mult:.1f}x)"],
                    'entry_price': last['close'],
                    'stop_loss': last['close'] * 0.98, # Stop serré -2%
                    'take_profit': last['close'] * 1.05, # TP rapide +5%
                    'is_moonshot': True
                }
                
        except Exception as e:
            logger.error(f"Erreur Moonshot {symbol}: {e}")
            
        return {}
    
    def execute_trade(self, signal: dict, market_conditions: dict) -> bool:
        """Exécute un trade avec gestion du leverage"""
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
        leverage = 1.0
        stop_loss = signal['stop_loss']
        
        # NOUVEAU: Appliquer leverage si autorisé
        leverage_decision = signal.get('leverage_decision')
        if leverage_decision and leverage_decision.can_leverage:
            leverage = leverage_decision.multiplier
            
            # Ajuster stop loss (plus serré avec leverage)
            stop_pct = leverage_decision.adjusted_stop_loss / 100
            stop_loss = signal['entry_price'] * (1 - stop_pct)
            
            # APPLIQUER LE LEVERAGE SUR LA QUANTITÉ
            qty = qty * leverage
            
            logger.info(f"🚀 LEVERAGE ACTIVÉ: {leverage}x -> Qty boostée: {qty}")
            logger.info(f"   Stop ajusté: ${stop_loss:.2f} ({leverage_decision.adjusted_stop_loss:.2f}%)")
            
            self.leverage_manager.open_leveraged_position()
        
        try:
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
            logger.info(f"   Leverage: {leverage}x")
            logger.info(f"   Stop Loss: ${stop_loss:.2f}")
            logger.info(f"   Take Profit: ${signal['take_profit']:.2f}")
            logger.info(f"   Order ID: {order.id}")
            
            # Stocker infos position
            self.risk_manager.positions[symbol] = {
                'entry': signal['entry_price'],
                'stop_loss': stop_loss,
                'take_profit': signal['take_profit'],
                'highest': signal['entry_price'],
                'leverage': leverage,
                'order_id': order.id,
                'time': datetime.now(self.tz)
            }
            
            self.trades_today += 1
            if leverage > 1:
                self.leveraged_trades_today += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ordre: {e}")
            if leverage > 1:
                self.leverage_manager.close_leveraged_position(0)
            return False
    
    def check_exits(self):
        """Vérifie les sorties de positions"""
        exits = self.risk_manager.check_all_exits(self.strategy)
        
        for exit_signal in exits:
            try:
                symbol = exit_signal['symbol']
                alpaca_symbol = symbol.replace('/', '')
                
                logger.info(f"\n🚪 SORTIE {symbol}: {exit_signal['reason']}")
                
                # Récupérer info leverage
                position_info = self.risk_manager.positions.get(symbol, {})
                leverage = position_info.get('leverage', 1.0)
                
                # Fermer la position
                self.api.close_position(alpaca_symbol)
                
                # Enregistrer le trade
                pnl = exit_signal['pnl']
                self.risk_manager.record_trade(pnl)
                
                # Si c'était une position leverage
                if leverage > 1:
                    self.leverage_manager.close_leveraged_position(pnl)
                    logger.info(f"   🚀 Position leverage {leverage}x fermée")
                
                # Nettoyer
                if symbol in self.risk_manager.positions:
                    del self.risk_manager.positions[symbol]
                
                logger.info(f"✅ Position fermée: {exit_signal['pnl_pct']:.2f}% (${pnl:.2f})")
                
            except Exception as e:
                logger.error(f"❌ Erreur fermeture {symbol}: {e}")
    
    def print_status(self):
        """Affiche le statut complet"""
        status = self.risk_manager.get_risk_status()
        leverage_status = self.leverage_manager.get_status()
        
        logger.info("\n" + "=" * 50)
        logger.info("📊 STATUT CRYPTO HUNTER V2.0")
        logger.info("=" * 50)
        logger.info(f"💰 Portfolio: ${status['portfolio_value']:,.2f}")
        logger.info(f"💵 Cash: ${status['cash']:,.2f} ({status['cash_ratio']:.1f}%)")
        logger.info(f"📈 Positions: {status['num_positions']}/{status['max_positions']}")
        logger.info(f"🎯 Exposition: ${status['exposure']:,.2f} ({status['exposure_pct']:.1f}%)")
        logger.info(f"📊 P&L non réalisé: ${status['unrealized_pnl']:,.2f}")
        logger.info(f"📅 P&L journalier: ${status['daily_pnl']:,.2f}")
        logger.info(f"🔢 Trades: {status['daily_trades']} (dont {self.leveraged_trades_today} avec leverage)")
        logger.info(f"🚀 Positions leverage: {leverage_status['leveraged_positions']}/{leverage_status['max_leveraged_positions']}")
        
        if status['positions']:
            logger.info("\n📋 POSITIONS OUVERTES:")
            for pos in status['positions']:
                pos_info = self.risk_manager.positions.get(pos['symbol'], {})
                leverage = pos_info.get('leverage', 1.0)
                lev_str = f" (🚀{leverage}x)" if leverage > 1 else ""
                logger.info(f"   {pos['symbol']}{lev_str}: {pos['qty']} @ ${pos['entry_price']:.2f} → ${pos['current_price']:.2f} ({pos['unrealized_plpc']:.2f}%)")
    
    def trading_cycle(self):
        """Cycle principal de trading"""
        try:
            # 1. Afficher statut
            self.print_status()
            
            # 2. NOUVEAU: Vérifier conditions marché
            market_conditions = self.check_market_conditions()
            
            if not market_conditions['can_trade']:
                logger.warning("⛔ Trading suspendu - Conditions marché défavorables")
                logger.info(f"⏰ Prochain scan dans 5 minutes...")
                return
            
            # 3. Vérifier sorties
            self.check_exits()
            
            # 4. Scanner opportunités
            opportunities = self.scan_opportunities(market_conditions)
            
            # 5. Exécuter meilleure opportunité
            if opportunities:
                # Trier par score puis confiance
                opportunities.sort(key=lambda x: (x.get('score', 0), x.get('confidence', 0)), reverse=True)
                best = opportunities[0]
                
                logger.info(f"\n🏆 MEILLEURE OPPORTUNITÉ: {best['symbol']}")
                logger.info(f"   Score: {best['score']:.1f}/{best['max_score']}")
                logger.info(f"   Confiance: {best['confidence']:.0f}%")
                
                leverage_dec = best.get('leverage_decision')
                if leverage_dec and leverage_dec.can_leverage:
                    logger.info(f"   🚀 Leverage: {leverage_dec.multiplier}x disponible")
                
                self.execute_trade(best, market_conditions)
            else:
                logger.info("\n😴 Pas d'opportunité - En attente...")
            
            logger.info(f"\n⏰ Prochain scan dans 5 minutes...")
            
        except Exception as e:
            logger.error(f"❌ Erreur cycle: {e}")
    
    def run(self):
        """Lance le bot"""
        logger.info("\n🚀 DÉMARRAGE CRYPTO HUNTER BOT V2.0")
        logger.info("   🪙 Trading sur BTC, ETH, SOL")
        logger.info("   🚀 Leverage intelligent activé")
        logger.info("   🌍 APIs Marché connectées")
        logger.info("   ⏰ Intervalle: 5 minutes\n")
        
        # Premier cycle immédiat
        self.trading_cycle()
        
        # Planifier cycles
        schedule.every(5).minutes.do(self.trading_cycle)
        schedule.every(60).minutes.do(self.run_ai_agent)
        schedule.every().day.at("00:00").do(self._daily_reset)
        
        # Premier scan AI au démarrage
        self.run_ai_agent()
        
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
    
    def run_ai_agent(self):
        """Lance l'agent AI pour trouver de nouvelles cryptos"""
        try:
            new_gems = self.ai_scanner.scan_market(self.symbols)
            if new_gems:
                for gem in new_gems:
                    if gem not in self.symbols:
                        self.symbols.append(gem)
                        logger.info(f"🆕 AJOUTÉ À LA LISTE: {gem}")
        except Exception as e:
            logger.error(f"❌ AI Agent Error: {e}")
    
    def _daily_reset(self):
        """Reset quotidien"""
        self.risk_manager.reset_daily()
        # self.leverage_manager.reset_daily() # Pas nécessaire
        self.trades_today = 0
        self.leveraged_trades_today = 0


def main():
    """Point d'entrée"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🪙 CRYPTO HUNTER BOT V2.0                               ║
    ║   Trading Crypto avec Leverage Intelligent                ║
    ║                                                           ║
    ║   Cryptos: BTC, ETH, SOL                                  ║
    ║   Stratégie: Momentum Confirmé                            ║
    ║   Leverage: Max 2x (si confiance > 85%)                   ║
    ║   APIs: Fear & Greed, BTC Dominance                       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    bot = CryptoHunterBot()
    bot.run()


if __name__ == "__main__":
    main()
