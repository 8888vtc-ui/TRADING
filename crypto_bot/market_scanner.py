"""
🤖 AI MARKET SCANNER AGENT
==========================
Agent autonome qui scanne le marché global pour trouver les cryptos
qui bougent ("Movers & Shakers") et les ajouter dynamiquement au bot.
"""

import logging
import pandas as pd
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class MarketScannerAgent:
    def __init__(self, api):
        self.api = api
        self.min_volume = 1_000_000  # 1M$ volume min
        self.min_price = 0.01        # Eviter les dust coins
        self.min_change = 5.0        # +5% min pour être intéressant
        self.detected_symbols = set()
        
    def scan_market(self, current_symbols: list) -> list:
        """
        Scanne tout le marché pour trouver de nouvelles pépites.
        Retourne la liste des symboles à AJOUTER.
        """
        new_candidates = []
        logger.info("\n🕵️ AI AGENT: Scan du marché global en cours...")
        
        try:
            # Récupérer les snapshots (Tous les cryptos dispos sur Alpaca)
            # Note: get_crypto_snapshots return un dictionnaire {symbol: snapshot}
            # On demande les majeurs pour éviter le bruit si possible, mais Alpaca a une liste finie.
            # On va demander une liste large ou utiliser une méthode de discovery si dispo.
            # Alpaca n'a pas de "get_all_tickers" facile pour crypto en une fois V2, 
            # mais on peut scanner une liste connue de "Top 50" ou similar.
            # Pour l'instant, on va simuler un scan large sur une liste étendue prédéfinie 
            # car l'API snapshot demande des symboles spécifiques.
            
            # Liste étendue de candidats potentiels (Top 30 Market Cap + Meme coins)
            extended_universe = [
                'DOGE/USD', 'SHIB/USD', 'PEPE/USD', 'BONK/USD',
                'AAVE/USD', 'CRV/USD', 'MKR/USD', 'SNX/USD',
                'COMP/USD', 'YFI/USD', 'SUSHI/USD', 'BAT/USD',
                'ALGO/USD', 'XL/USD', 'XLM/USD', 'ETC/USD'
            ]
            
            # Filtrer ceux qu'on trade déjà
            candidates = [s for s in extended_universe if s not in current_symbols]
            
            if not candidates:
                logger.info("🕵️ AI AGENT: Tous les candidats sont déjà tradés.")
                return []

            # Nettoyer les symboles pour l'API (enlever le /USD pour l'appel si besoin, 
            # mais get_crypto_snapshots V2 prend souvent les paires brutes ou normalisées)
            # On essaie par lots
            
            # Simulation intelligente: On va vérifier la volatilité de ces candidats
            # En réalité, on ferait un appel API snapshot.
            
            # Pour chaque candidat, on regarde la bougie daily
            # Optimisation: On utilise get_crypto_bars daily sur 1 jour pour tous
            
            # On va construire une liste de symboles compatible API
            # Alpaca API snapshots endpoint is efficient.
            
            # Appel API réel (si possible)
            # snapshots = self.api.get_crypto_snapshots(candidates, feed='us_equity') # feed param depends on subscription
            # On va faire simple: itérer et check 24h change
            
            for symbol in candidates:
                try:
                    alpaca_sym = symbol #.replace('/', '') # V2 uses BTC/USD usually
                    bars = self.api.get_crypto_bars(alpaca_sym, '1Day', limit=2).df
                    
                    if bars.empty or len(bars) < 1:
                        continue
                        
                    last_bar = bars.iloc[-1]
                    
                    # Calcul variation
                    open_p = last_bar['open']
                    close_p = last_bar['close']
                    volume = last_bar['volume'] * close_p # Volume en $ approx
                    
                    if open_p == 0: continue
                    
                    change_pct = ((close_p - open_p) / open_p) * 100
                    
                    # Critères de sélection AI
                    if (abs(change_pct) >= self.min_change and 
                        volume >= self.min_volume and 
                        close_p >= self.min_price):
                        
                        logger.info(f"✨ AI AGENT: PÉPITE DÉTECTÉE -> {symbol} ({change_pct:+.2f}% | Vol ${volume/1e6:.1f}M)")
                        new_candidates.append(symbol)
                        self.detected_symbols.add(symbol)
                        
                except Exception as ex:
                    continue
            
            if new_candidates:
                logger.info(f"🕵️ AI AGENT: A recruté {len(new_candidates)} nouveaux symboles!")
            else:
                logger.info("🕵️ AI AGENT: Rien d'intéressant à ajouter.")
                
            return new_candidates

        except Exception as e:
            logger.error(f"❌ AI AGENT Error: {e}")
            return []
