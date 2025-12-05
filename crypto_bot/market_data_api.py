"""
📊 MARKET DATA API - Vérification du Marché Crypto
==================================================
APIs utilisées:
- Fear & Greed Index (Alternative.me)
- Bitcoin Dominance
- Market Cap Total
- Données on-chain basiques

Ces données aident à confirmer si le marché est favorable
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class CryptoMarketData:
    """
    Récupère et analyse les données de marché crypto
    pour confirmer les conditions de trading
    """
    
    def __init__(self):
        # Cache pour éviter trop de requêtes
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Seuils pour le trading
        self.fear_greed_thresholds = {
            'extreme_fear': 25,      # Achat potentiel (contrarian)
            'fear': 40,              # Prudent
            'neutral': 55,           # Normal
            'greed': 75,             # Attention
            'extreme_greed': 85      # Danger - éviter longs
        }
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Récupère une donnée en cache si valide"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        """Met en cache une donnée"""
        self.cache[key] = (data, time.time())
    
    def get_fear_greed_index(self) -> Dict:
        """
        Récupère le Fear & Greed Index
        Source: alternative.me/crypto/fear-and-greed-index/
        
        Valeurs:
        0-25: Extreme Fear (bon pour acheter)
        25-45: Fear
        45-55: Neutral
        55-75: Greed
        75-100: Extreme Greed (danger)
        """
        cached = self._get_cached('fear_greed')
        if cached:
            return cached
        
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('data'):
                current = data['data'][0]
                result = {
                    'value': int(current['value']),
                    'classification': current['value_classification'],
                    'timestamp': current['timestamp'],
                    'valid': True
                }
                
                # Analyse
                value = result['value']
                if value <= self.fear_greed_thresholds['extreme_fear']:
                    result['signal'] = 'STRONG_BUY'
                    result['leverage_ok'] = False  # Trop risqué malgré opportunité
                    result['description'] = "Peur extrême - Opportunité contrarian"
                elif value <= self.fear_greed_thresholds['fear']:
                    result['signal'] = 'BUY'
                    result['leverage_ok'] = False
                    result['description'] = "Peur - Bon pour accumulation"
                elif value <= self.fear_greed_thresholds['neutral']:
                    result['signal'] = 'NEUTRAL'
                    result['leverage_ok'] = True  # Conditions stables
                    result['description'] = "Neutre - Marché équilibré"
                elif value <= self.fear_greed_thresholds['greed']:
                    result['signal'] = 'CAUTION'
                    result['leverage_ok'] = True  # OK mais prudent
                    result['description'] = "Cupidité - Prudence"
                else:
                    result['signal'] = 'DANGER'
                    result['leverage_ok'] = False  # Trop risqué
                    result['description'] = "Cupidité extrême - ÉVITER LONGS"
                
                self._set_cache('fear_greed', result)
                logger.info(f"📊 Fear & Greed: {value} ({result['classification']}) - {result['signal']}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur Fear & Greed API: {e}")
        
        return {
            'value': 50,
            'classification': 'Neutral',
            'signal': 'NEUTRAL',
            'leverage_ok': False,
            'valid': False,
            'description': "Données non disponibles"
        }
    
    def get_btc_dominance(self) -> Dict:
        """
        Récupère la dominance BTC
        Utile pour savoir si focus sur BTC ou altcoins
        """
        cached = self._get_cached('btc_dominance')
        if cached:
            return cached
        
        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('data'):
                btc_dom = data['data']['market_cap_percentage'].get('btc', 50)
                result = {
                    'btc_dominance': round(btc_dom, 2),
                    'eth_dominance': round(data['data']['market_cap_percentage'].get('eth', 15), 2),
                    'total_market_cap': data['data']['total_market_cap'].get('usd', 0),
                    'market_cap_change_24h': data['data'].get('market_cap_change_percentage_24h_usd', 0),
                    'valid': True
                }
                
                # Analyse dominance
                if btc_dom > 55:
                    result['signal'] = 'BTC_FOCUS'
                    result['description'] = "BTC dominant - Focus sur Bitcoin"
                elif btc_dom < 40:
                    result['signal'] = 'ALT_SEASON'
                    result['description'] = "Alt season - Altcoins performent"
                else:
                    result['signal'] = 'BALANCED'
                    result['description'] = "Marché équilibré"
                
                self._set_cache('btc_dominance', result)
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur BTC Dominance API: {e}")
        
        return {'btc_dominance': 50, 'valid': False}
    
    def get_market_overview(self) -> Dict:
        """
        Vue d'ensemble du marché crypto
        Combine plusieurs indicateurs
        """
        fear_greed = self.get_fear_greed_index()
        dominance = self.get_btc_dominance()
        
        overview = {
            'fear_greed': fear_greed,
            'dominance': dominance,
            'timestamp': datetime.now().isoformat(),
            'overall_signal': 'NEUTRAL',
            'leverage_allowed': False,
            'confidence_boost': 0
        }
        
        # Calculer signal global
        signals = []
        
        # Fear & Greed
        fg_value = fear_greed.get('value', 50)
        if fg_value <= 30:
            signals.append(('BUY', 2))
        elif fg_value <= 45:
            signals.append(('BUY', 1))
        elif fg_value >= 80:
            signals.append(('SELL', 2))
        elif fg_value >= 65:
            signals.append(('SELL', 1))
        else:
            signals.append(('NEUTRAL', 0))
        
        # Market cap change
        mc_change = dominance.get('market_cap_change_24h', 0)
        if mc_change > 3:
            signals.append(('BUY', 1))
        elif mc_change < -3:
            signals.append(('SELL', 1))
        
        # Calculer score global
        buy_score = sum(s[1] for s in signals if s[0] == 'BUY')
        sell_score = sum(s[1] for s in signals if s[0] == 'SELL')
        
        if buy_score > sell_score + 1:
            overview['overall_signal'] = 'BULLISH'
            overview['confidence_boost'] = min(10, buy_score * 3)
        elif sell_score > buy_score + 1:
            overview['overall_signal'] = 'BEARISH'
            overview['confidence_boost'] = -min(10, sell_score * 3)
        else:
            overview['overall_signal'] = 'NEUTRAL'
        
        # Leverage autorisé seulement si conditions optimales
        # Fear & Greed entre 40-60 (stable) et pas de volatilité extrême
        if 35 <= fg_value <= 65 and abs(mc_change) < 5:
            overview['leverage_allowed'] = True
        
        return overview
    
    def get_crypto_prices(self, symbols: list = ['bitcoin', 'ethereum', 'solana']) -> Dict:
        """
        Récupère les prix actuels et variations
        """
        cached = self._get_cached('prices')
        if cached:
            return cached
        
        try:
            ids = ','.join(symbols)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ids,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            result = {'valid': True, 'prices': {}}
            for symbol in symbols:
                if symbol in data:
                    result['prices'][symbol] = {
                        'price': data[symbol].get('usd', 0),
                        'change_24h': data[symbol].get('usd_24h_change', 0),
                        'volume_24h': data[symbol].get('usd_24h_vol', 0)
                    }
            
            self._set_cache('prices', result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur prix API: {e}")
        
        return {'valid': False, 'prices': {}}
    
    def should_trade_now(self) -> Dict:
        """
        Décision finale: doit-on trader maintenant?
        """
        overview = self.get_market_overview()
        
        result = {
            'can_trade': True,
            'can_leverage': False,
            'leverage_multiplier': 1.0,
            'confidence_adjustment': 0,
            'reasons': []
        }
        
        # Fear & Greed check
        fg = overview['fear_greed']
        fg_value = fg.get('value', 50)
        
        if fg_value >= 85:
            result['can_trade'] = False
            result['reasons'].append(f"⛔ Extreme Greed ({fg_value}) - Marché surchauffé")
        elif fg_value <= 15:
            result['reasons'].append(f"⚠️ Extreme Fear ({fg_value}) - Volatilité élevée attendue")
            result['confidence_adjustment'] = -10
        elif 40 <= fg_value <= 60:
            result['can_leverage'] = True
            result['reasons'].append(f"✅ Fear & Greed stable ({fg_value})")
        
        # Signal global
        if overview['overall_signal'] == 'BEARISH':
            result['can_leverage'] = False
            result['confidence_adjustment'] -= 5
            result['reasons'].append("⚠️ Signal global bearish")
        elif overview['overall_signal'] == 'BULLISH':
            result['confidence_adjustment'] += 5
            result['reasons'].append("✅ Signal global bullish")
        
        # Leverage autorisé?
        if result['can_leverage'] and overview['leverage_allowed']:
            result['leverage_multiplier'] = 1.5  # Max 1.5x en mode conservateur
            result['reasons'].append("✅ Leverage 1.5x autorisé")
        
        return result


class MarketConditionChecker:
    """
    Vérificateur rapide des conditions de marché
    À utiliser avant chaque trade
    """
    
    def __init__(self):
        self.market_data = CryptoMarketData()
        self.last_check = None
        self.last_result = None
        self.check_interval = 60  # Vérifier au moins toutes les 60 secondes
    
    def check(self) -> Dict:
        """Vérifie les conditions actuelles"""
        now = time.time()
        
        # Utiliser cache si récent
        if self.last_check and (now - self.last_check) < self.check_interval:
            return self.last_result
        
        result = self.market_data.should_trade_now()
        self.last_check = now
        self.last_result = result
        
        return result
    
    def quick_check(self) -> bool:
        """Check rapide: peut-on trader?"""
        result = self.check()
        return result['can_trade']
    
    def can_use_leverage(self) -> tuple:
        """Peut-on utiliser le leverage?"""
        result = self.check()
        return result['can_leverage'], result['leverage_multiplier']


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("📊 TEST MARKET DATA API")
    print("=" * 50)
    
    market = CryptoMarketData()
    
    # Test Fear & Greed
    fg = market.get_fear_greed_index()
    print(f"\n🎭 Fear & Greed Index: {fg['value']} ({fg['classification']})")
    print(f"   Signal: {fg['signal']}")
    print(f"   Leverage OK: {fg['leverage_ok']}")
    
    # Test Dominance
    dom = market.get_btc_dominance()
    print(f"\n👑 BTC Dominance: {dom.get('btc_dominance', 'N/A')}%")
    
    # Test Overview
    overview = market.get_market_overview()
    print(f"\n📈 Signal Global: {overview['overall_signal']}")
    print(f"   Leverage Autorisé: {overview['leverage_allowed']}")
    
    # Test décision
    decision = market.should_trade_now()
    print(f"\n🎯 DÉCISION TRADING:")
    print(f"   Peut trader: {decision['can_trade']}")
    print(f"   Peut leverage: {decision['can_leverage']}")
    print(f"   Multiplicateur: {decision['leverage_multiplier']}x")
    for reason in decision['reasons']:
        print(f"   {reason}")

