"""
⚡ TRADING ENGINE V2.0 - SYSTÈME OPTIMISÉ
=========================================
Ordre optimal des opérations pour maximiser la réactivité:

1. ⚡ CHECK EXITS IMMÉDIAT (< 100ms)
   └── Priorité absolue à la protection du capital

2. 📡 FETCH APIs EN PARALLÈLE (ThreadPool)
   ├── Fear & Greed
   ├── VIX
   ├── DXY
   ├── Market Overview
   └── Calendrier économique

3. 📊 CALCULATE INDICATORS (pendant fetch APIs si possible)

4. 🧠 COMBINE & SCORE (Score Unifié V2.0)

5. 🎯 EXECUTE si signal OK

RÉSULTAT: Cycle < 3 secondes au lieu de 10-15
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)


class TradingEngineV2:
    """
    ⚡ Trading Engine V2.0 - Optimisé pour la réactivité
    """
    
    def __init__(self, api, strategy, risk_manager, market_intel, optimal_strategy):
        self.api = api
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.market_intel = market_intel
        self.optimal_strategy = optimal_strategy
        
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.cycle_count = 0
        self.last_cycle_time = 0
        
        # Métriques
        self.metrics = {
            'exits_checked': 0,
            'trades_executed': 0,
            'cycles_completed': 0,
            'avg_cycle_time_ms': 0,
            'total_cycle_time_ms': 0,
        }
        
        logger.info("⚡ Trading Engine V2.0 initialisé")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1: CHECK EXITS IMMÉDIAT
    # ═══════════════════════════════════════════════════════════════
    
    def check_exits_immediate(self) -> List[Dict]:
        """
        ⚡ Vérifie les exits en PRIORITÉ ABSOLUE
        Doit être < 100ms
        """
        start = time.time()
        exits = []
        
        try:
            positions = self.risk_manager.get_positions()
            
            for pos in positions:
                symbol = pos['symbol']
                entry = pos['entry_price']
                current = pos['current_price']
                pnl_pct = pos['unrealized_plpc']
                
                # Stop Loss check
                position_data = self.risk_manager.positions.get(symbol, {})
                stop = position_data.get('stop_loss', entry * 0.97)
                take_profit = position_data.get('take_profit', entry * 1.06)
                highest = position_data.get('highest', current)
                
                # Update highest
                if current > highest:
                    self.risk_manager.positions.setdefault(symbol, {})['highest'] = current
                    highest = current
                
                exit_signal = None
                
                # Stop Loss touché
                if current <= stop:
                    exit_signal = {
                        'symbol': symbol,
                        'reason': f'🛑 STOP LOSS ({pnl_pct:.2f}%)',
                        'type': 'STOP',
                        'qty': pos['qty'],
                        'pnl_pct': pnl_pct
                    }
                
                # Take Profit touché
                elif current >= take_profit:
                    exit_signal = {
                        'symbol': symbol,
                        'reason': f'💰 TAKE PROFIT ({pnl_pct:.2f}%)',
                        'type': 'TP',
                        'qty': pos['qty'],
                        'pnl_pct': pnl_pct
                    }
                
                # Trailing stop (si profit > 2%)
                elif pnl_pct > 2:
                    trail_stop = highest * 0.985  # 1.5% trailing
                    if current <= trail_stop:
                        exit_signal = {
                            'symbol': symbol,
                            'reason': f'📉 TRAILING STOP ({pnl_pct:.2f}%)',
                            'type': 'TRAIL',
                            'qty': pos['qty'],
                            'pnl_pct': pnl_pct
                        }
                
                if exit_signal:
                    exits.append(exit_signal)
                    logger.warning(f"⚠️ EXIT SIGNAL: {exit_signal['symbol']} - {exit_signal['reason']}")
        
        except Exception as e:
            logger.error(f"Erreur check exits: {e}")
        
        elapsed = (time.time() - start) * 1000
        self.metrics['exits_checked'] += len(exits)
        
        if elapsed > 100:
            logger.warning(f"⚠️ Exit check lent: {elapsed:.0f}ms (cible <100ms)")
        else:
            logger.info(f"⚡ Exits checked in {elapsed:.0f}ms")
        
        return exits
    
    def execute_exits(self, exits: List[Dict]) -> int:
        """Exécute les sorties de position"""
        executed = 0
        
        for exit_signal in exits:
            try:
                symbol = exit_signal['symbol']
                
                # Fermer la position
                self.api.close_position(symbol.replace('/', ''))
                
                # Enregistrer
                self.risk_manager.record_trade(0, trade_type='CLOSE')
                
                # Nettoyer
                if symbol in self.risk_manager.positions:
                    del self.risk_manager.positions[symbol]
                
                logger.info(f"✅ Position fermée: {symbol} - {exit_signal['reason']}")
                executed += 1
                
            except Exception as e:
                logger.error(f"Erreur fermeture {exit_signal['symbol']}: {e}")
        
        return executed
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2: FETCH PARALLÈLE
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_all_data_parallel(self, symbols: List[str]) -> Dict:
        """
        📡 Fetch toutes les données en parallèle
        - APIs informatives
        - Données de marché pour chaque symbol
        """
        start = time.time()
        results = {'market': None, 'symbols': {}}
        
        # Soumettre tous les jobs
        futures = {}
        
        # Market Intelligence
        futures['market'] = self.executor.submit(self.market_intel.full_analysis)
        
        # Données pour chaque symbol
        for symbol in symbols:
            futures[f'data_{symbol}'] = self.executor.submit(self._get_symbol_data, symbol)
        
        # Collecter les résultats
        for key, future in futures.items():
            try:
                result = future.result(timeout=15)
                if key == 'market':
                    results['market'] = result
                elif key.startswith('data_'):
                    symbol = key.replace('data_', '')
                    results['symbols'][symbol] = result
            except Exception as e:
                logger.warning(f"Fetch {key} timeout/error: {e}")
        
        elapsed = (time.time() - start) * 1000
        logger.info(f"📡 Toutes données récupérées en {elapsed:.0f}ms")
        
        return results
    
    def _get_symbol_data(self, symbol: str):
        """Récupère les données pour un symbol"""
        try:
            return self.strategy.get_historical_data(symbol)
        except Exception as e:
            logger.error(f"Erreur données {symbol}: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 3 & 4: ANALYSE ET SCORING
    # ═══════════════════════════════════════════════════════════════
    
    def analyze_opportunities(self, data: Dict) -> List[Dict]:
        """
        🧠 Analyse les opportunités avec le scoring unifié V2.0
        """
        start = time.time()
        opportunities = []
        
        market_data = data.get('market', {}).get('data', {})
        
        # Vérifier si trading autorisé
        if not data.get('market', {}).get('can_trade', True):
            logger.warning(f"⛔ Trading bloqué: {data.get('market', {}).get('recommendation', 'N/A')}")
            return opportunities
        
        for symbol, df in data.get('symbols', {}).items():
            if df is None or len(df) < 50:
                continue
            
            try:
                # Générer signal de base
                signal = self.strategy.generate_signal(df, symbol) if hasattr(self.strategy, 'generate_signal') else self.strategy.analyze(symbol)
                
                if signal.get('signal') != 'BUY' and signal.get('action') != 'BUY':
                    continue
                
                # Extraire indicateurs
                indicators = signal.get('indicators', {})
                if not indicators and hasattr(signal, 'get'):
                    indicators = {
                        'close': signal.get('price', signal.get('entry_price', 0)),
                        'rsi': signal.get('rsi', 50),
                        'adx': signal.get('adx', 20),
                        'volume_ratio': signal.get('volume_ratio', 1),
                    }
                
                # Score unifié V2.0
                unified_result = self.optimal_strategy.calculate_unified_score(
                    market_data,
                    indicators,
                    df
                )
                
                # Ajouter au signal
                signal['unified_score'] = unified_result['total_score']
                signal['unified_decision'] = unified_result['decision']
                signal['leverage'] = unified_result['leverage']
                signal['hold_multiplier'] = unified_result['hold_multiplier']
                signal['stop_loss_optimal'] = signal.get('entry_price', 0) * (1 - unified_result['stop_loss_pct'] / 100)
                signal['take_profit_optimal'] = signal.get('entry_price', 0) * (1 + unified_result['take_profit_pct'] / 100)
                
                # Filtrer par score minimum
                if unified_result['total_score'] >= 45:
                    opportunities.append(signal)
                    logger.info(f"✅ Opportunité: {symbol} | Score: {unified_result['total_score']}/100")
                
            except Exception as e:
                logger.error(f"Erreur analyse {symbol}: {e}")
        
        # Trier par score
        opportunities.sort(key=lambda x: x.get('unified_score', 0), reverse=True)
        
        elapsed = (time.time() - start) * 1000
        logger.info(f"🧠 Analyse en {elapsed:.0f}ms - {len(opportunities)} opportunités")
        
        return opportunities
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 5: EXÉCUTION
    # ═══════════════════════════════════════════════════════════════
    
    def execute_best_opportunity(self, opportunities: List[Dict], market_data: Dict) -> bool:
        """
        🎯 Exécute la meilleure opportunité
        """
        if not opportunities:
            return False
        
        best = opportunities[0]
        symbol = best.get('symbol')
        
        logger.info(f"\n🎯 MEILLEURE OPPORTUNITÉ: {symbol}")
        logger.info(f"   Score Unifié: {best.get('unified_score')}/100")
        logger.info(f"   {best.get('unified_decision')}")
        logger.info(f"   Leverage: {best.get('leverage')}x")
        
        try:
            # Calculer position
            entry_price = best.get('entry_price', best.get('price', 0))
            stop_loss = best.get('stop_loss_optimal', entry_price * 0.97)
            confidence = best.get('confidence', best.get('unified_score', 50))
            
            position = self.risk_manager.calculate_position_size(
                symbol,
                entry_price,
                stop_loss,
                confidence
            )
            
            if not position.get('can_trade'):
                logger.warning(f"⛔ Trade refusé: {position.get('reason')}")
                return False
            
            qty = position['qty']
            leverage = best.get('leverage', 1.0)
            
            # Passer l'ordre
            alpaca_symbol = symbol.replace('/', '')
            
            order = self.api.submit_order(
                symbol=alpaca_symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            # Stocker infos position
            self.risk_manager.positions[symbol] = {
                'entry': entry_price,
                'stop_loss': stop_loss,
                'take_profit': best.get('take_profit_optimal', entry_price * 1.06),
                'highest': entry_price,
                'leverage': leverage,
                'unified_score': best.get('unified_score'),
                'order_id': order.id,
                'time': datetime.now()
            }
            
            logger.info(f"✅ ORDRE PASSÉ!")
            logger.info(f"   Symbole: {symbol}")
            logger.info(f"   Quantité: {qty}")
            logger.info(f"   Leverage: {leverage}x")
            logger.info(f"   Stop: ${stop_loss:.2f}")
            logger.info(f"   TP: ${best.get('take_profit_optimal', 0):.2f}")
            
            self.metrics['trades_executed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # CYCLE PRINCIPAL OPTIMISÉ
    # ═══════════════════════════════════════════════════════════════
    
    def run_optimized_cycle(self, symbols: List[str]) -> Dict:
        """
        ⚡ CYCLE DE TRADING OPTIMISÉ
        Exécute toutes les étapes dans l'ordre optimal
        """
        cycle_start = time.time()
        self.cycle_count += 1
        
        logger.info("\n" + "=" * 60)
        logger.info(f"⚡ CYCLE #{self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
        logger.info("=" * 60)
        
        result = {
            'cycle': self.cycle_count,
            'exits_executed': 0,
            'trade_executed': False,
            'opportunities': 0,
            'blocked': False,
            'total_time_ms': 0
        }
        
        try:
            # ════════════════════════════════════════════════════
            # ÉTAPE 1: CHECK EXITS IMMÉDIAT (< 100ms)
            # ════════════════════════════════════════════════════
            exits = self.check_exits_immediate()
            if exits:
                result['exits_executed'] = self.execute_exits(exits)
            
            # ════════════════════════════════════════════════════
            # ÉTAPE 2: FETCH PARALLÈLE (1-2s)
            # ════════════════════════════════════════════════════
            data = self.fetch_all_data_parallel(symbols)
            
            # Vérifier si trading bloqué
            market_result = data.get('market', {})
            if not market_result.get('can_trade', True):
                result['blocked'] = True
                result['block_reason'] = market_result.get('recommendation', 'Unknown')
                logger.warning(f"⛔ Trading bloqué: {result['block_reason']}")
            else:
                # ════════════════════════════════════════════════════
                # ÉTAPE 3 & 4: ANALYSE ET SCORING
                # ════════════════════════════════════════════════════
                opportunities = self.analyze_opportunities(data)
                result['opportunities'] = len(opportunities)
                
                # ════════════════════════════════════════════════════
                # ÉTAPE 5: EXÉCUTION
                # ════════════════════════════════════════════════════
                if opportunities:
                    result['trade_executed'] = self.execute_best_opportunity(
                        opportunities,
                        market_result
                    )
        
        except Exception as e:
            logger.error(f"❌ Erreur cycle: {e}")
            result['error'] = str(e)
        
        # Métriques
        cycle_time = (time.time() - cycle_start) * 1000
        result['total_time_ms'] = cycle_time
        
        self.metrics['cycles_completed'] += 1
        self.metrics['total_cycle_time_ms'] += cycle_time
        self.metrics['avg_cycle_time_ms'] = self.metrics['total_cycle_time_ms'] / self.metrics['cycles_completed']
        self.last_cycle_time = cycle_time
        
        logger.info(f"\n⚡ Cycle terminé en {cycle_time:.0f}ms")
        logger.info(f"   Moyenne: {self.metrics['avg_cycle_time_ms']:.0f}ms")
        
        return result
    
    def get_metrics(self) -> Dict:
        """Retourne les métriques du trading engine"""
        return {
            **self.metrics,
            'last_cycle_time_ms': self.last_cycle_time,
            'cycle_count': self.cycle_count
        }


if __name__ == "__main__":
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    print("""
    ⚡ TRADING ENGINE V2.0 - DÉMARRAGE
    ==================================
    Mode: 24/7 LOOP
    Intervalle: ~1 minute
    """)
    
    # Initialisation
    try:
        engine = TradingEngineV2()
        logger.info("✅ Moteur initialisé avec succès")
    except Exception as e:
        logger.critical(f"❌ Echec initialisation: {e}")
        exit(1)
        
    # Boucle principale
    while True:
        try:
            # Exécuter un cycle
            result = engine.run_trading_cycle()
            
            # Attendre 60 secondes avant le prochain cycle
            # (Pour éviter de spammer l'API et respecter les rate limits)
            sleep_time = 60
            logger.info(f"⏳ Attente {sleep_time}s...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt manuel demandé")
            break
        except Exception as e:
            logger.error(f"❌ Crash boucle principale: {e}")
            time.sleep(60)  # Pause de sécurité en cas d'erreur grave

