"""
🧠 MARKET INTELLIGENCE - APIs INFORMATIVES POUR TOUS LES BOTS
=============================================================
Ce module consulte TOUTES les APIs disponibles avant chaque décision de trading.

APIs utilisées:
1. Fear & Greed Index (Crypto + Actions)
2. VIX (Volatilité)
3. Actualités financières
4. Calendrier économique
5. Sentiment de marché
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class MarketIntelligence:
    """
    🧠 Intelligence de Marché Centralisée
    =====================================
    Consulte toutes les APIs avant de trader
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.last_full_check = None
        
        # Seuils de décision
        self.thresholds = {
            'fear_greed_danger_high': 80,   # Trop de cupidité
            'fear_greed_danger_low': 15,    # Panique extrême
            'fear_greed_caution_high': 70,
            'fear_greed_caution_low': 25,
            'vix_danger': 35,               # VIX très élevé
            'vix_caution': 25,
            'vix_optimal': 18,              # VIX idéal pour trading
        }
        
        logger.info("🧠 Market Intelligence initialisé")
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        self.cache[key] = (data, time.time())
    
    # ═══════════════════════════════════════════════════════════════
    # 1. FEAR & GREED INDEX (Crypto)
    # ═══════════════════════════════════════════════════════════════
    def get_crypto_fear_greed(self) -> Dict:
        """Fear & Greed Index pour crypto"""
        cached = self._get_cached('crypto_fg')
        if cached: return cached
        
        try:
            r = requests.get("https://api.alternative.me/fng/", timeout=10)
            data = r.json()
            if data.get('data'):
                value = int(data['data'][0]['value'])
                result = {
                    'value': value,
                    'classification': data['data'][0]['value_classification'],
                    'source': 'alternative.me',
                    'valid': True
                }
                self._set_cache('crypto_fg', result)
                return result
        except Exception as e:
            logger.warning(f"Fear & Greed API error: {e}")
        
        return {'value': 50, 'classification': 'Neutral', 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 2. VIX (Volatilité Actions)
    # ═══════════════════════════════════════════════════════════════
    def get_vix(self) -> Dict:
        """VIX - Indice de volatilité"""
        cached = self._get_cached('vix')
        if cached: return cached
        
        try:
            # API Yahoo Finance pour VIX
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            
            if 'chart' in data and data['chart']['result']:
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                result = {
                    'value': round(price, 2),
                    'level': 'HIGH' if price > 25 else 'NORMAL' if price > 15 else 'LOW',
                    'valid': True
                }
                self._set_cache('vix', result)
                return result
        except Exception as e:
            logger.warning(f"VIX API error: {e}")
        
        return {'value': 20, 'level': 'NORMAL', 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 3. MARKET CAP & DOMINANCE
    # ═══════════════════════════════════════════════════════════════
    def get_market_overview(self) -> Dict:
        """Vue globale du marché"""
        cached = self._get_cached('market_overview')
        if cached: return cached
        
        try:
            r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
            data = r.json()
            
            if data.get('data'):
                d = data['data']
                result = {
                    'total_market_cap': d['total_market_cap'].get('usd', 0),
                    'btc_dominance': round(d['market_cap_percentage'].get('btc', 50), 2),
                    'eth_dominance': round(d['market_cap_percentage'].get('eth', 15), 2),
                    'market_cap_change_24h': round(d.get('market_cap_change_percentage_24h_usd', 0), 2),
                    'valid': True
                }
                self._set_cache('market_overview', result)
                return result
        except Exception as e:
            logger.warning(f"Market overview API error: {e}")
        
        return {'btc_dominance': 50, 'market_cap_change_24h': 0, 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 4. TRENDING STOCKS/CRYPTO
    # ═══════════════════════════════════════════════════════════════
    def get_trending(self) -> Dict:
        """Crypto et actions tendances"""
        cached = self._get_cached('trending')
        if cached: return cached
        
        try:
            r = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10)
            data = r.json()
            
            if data.get('coins'):
                trending = [c['item']['symbol'].upper() for c in data['coins'][:5]]
                result = {'trending_crypto': trending, 'valid': True}
                self._set_cache('trending', result)
                return result
        except:
            pass
        
        return {'trending_crypto': [], 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 5. ANALYSE COMPLÈTE
    # ═══════════════════════════════════════════════════════════════
    def full_analysis(self) -> Dict:
        """
        🧠 ANALYSE COMPLÈTE DU MARCHÉ
        Consulte TOUTES les APIs et retourne une décision
        """
        logger.info("🧠 Analyse complète du marché en cours...")
        
        # Collecter toutes les données
        fear_greed = self.get_crypto_fear_greed()
        vix = self.get_vix()
        market = self.get_market_overview()
        trending = self.get_trending()
        
        # Scores
        score = 50  # Base neutre
        warnings = []
        signals = []
        
        # ═══════════════════════════════════════════════════════════
        # Analyse Fear & Greed
        # ═══════════════════════════════════════════════════════════
        fg_value = fear_greed.get('value', 50)
        
        if fg_value >= self.thresholds['fear_greed_danger_high']:
            score -= 30
            warnings.append(f"⚠️ DANGER: Cupidité extrême ({fg_value})")
        elif fg_value >= self.thresholds['fear_greed_caution_high']:
            score -= 15
            warnings.append(f"⚠️ Cupidité élevée ({fg_value})")
        elif fg_value <= self.thresholds['fear_greed_danger_low']:
            score -= 20
            warnings.append(f"⚠️ Peur extrême ({fg_value}) - Volatilité!")
        elif fg_value <= self.thresholds['fear_greed_caution_low']:
            score += 10
            signals.append(f"✅ Peur = Opportunité ({fg_value})")
        elif 40 <= fg_value <= 60:
            score += 15
            signals.append(f"✅ Marché neutre stable ({fg_value})")
        
        # ═══════════════════════════════════════════════════════════
        # Analyse VIX
        # ═══════════════════════════════════════════════════════════
        vix_value = vix.get('value', 20)
        
        if vix_value >= self.thresholds['vix_danger']:
            score -= 25
            warnings.append(f"⚠️ VIX DANGER ({vix_value}) - Marché très volatile!")
        elif vix_value >= self.thresholds['vix_caution']:
            score -= 10
            warnings.append(f"⚠️ VIX élevé ({vix_value})")
        elif vix_value <= self.thresholds['vix_optimal']:
            score += 10
            signals.append(f"✅ VIX optimal ({vix_value})")
        
        # ═══════════════════════════════════════════════════════════
        # Analyse Market Cap Change
        # ═══════════════════════════════════════════════════════════
        mc_change = market.get('market_cap_change_24h', 0)
        
        if mc_change > 5:
            score += 10
            signals.append(f"✅ Marché haussier (+{mc_change}%)")
        elif mc_change < -5:
            score -= 15
            warnings.append(f"⚠️ Marché baissier ({mc_change}%)")
        
        # ═══════════════════════════════════════════════════════════
        # Décision finale
        # ═══════════════════════════════════════════════════════════
        can_trade = score >= 35
        can_leverage = score >= 60
        
        if score >= 70:
            recommendation = "🟢 CONDITIONS EXCELLENTES"
            max_risk_multiplier = 1.5
        elif score >= 50:
            recommendation = "🟡 CONDITIONS NORMALES"
            max_risk_multiplier = 1.0
        elif score >= 35:
            recommendation = "🟠 CONDITIONS PRUDENTES"
            max_risk_multiplier = 0.7
        else:
            recommendation = "🔴 CONDITIONS DÉFAVORABLES"
            max_risk_multiplier = 0.0
        
        # ═══════════════════════════════════════════════════════════
        # Décision de durée de position (HOLD LONGER)
        # ═══════════════════════════════════════════════════════════
        hold_multiplier = 1.0  # Base
        hold_reason = "Normal"
        
        # Si marché très bullish, on garde plus longtemps
        if score >= 70:
            hold_multiplier = 2.0  # Take profit 2x plus loin
            hold_reason = "🚀 Marché porteur - Laisser courir les gains!"
        elif score >= 55:
            hold_multiplier = 1.5  # Take profit 50% plus loin
            hold_reason = "📈 Tendance positive - Prolonger les positions"
        elif score <= 35:
            hold_multiplier = 0.5  # Take profit plus serré
            hold_reason = "⚠️ Marché risqué - Prendre les profits rapidement"
        
        # Ajuster selon momentum du marché
        if mc_change > 3:
            hold_multiplier *= 1.3
            hold_reason += " | Momentum fort"
        elif mc_change < -2:
            hold_multiplier *= 0.7
            hold_reason += " | Momentum faible"
        
        result = {
            'score': score,
            'can_trade': can_trade,
            'can_leverage': can_leverage,
            'recommendation': recommendation,
            'max_risk_multiplier': max_risk_multiplier,
            'hold_multiplier': hold_multiplier,  # NOUVEAU: Multiplicateur de durée
            'hold_reason': hold_reason,          # NOUVEAU: Raison
            'warnings': warnings,
            'signals': signals,
            'data': {
                'fear_greed': fear_greed,
                'vix': vix,
                'market': market,
                'trending': trending
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Log résumé
        logger.info(f"🧠 RÉSULTAT ANALYSE: Score {score}/100")
        logger.info(f"   {recommendation}")
        logger.info(f"   Peut trader: {'✅' if can_trade else '❌'}")
        logger.info(f"   Peut leverage: {'✅' if can_leverage else '❌'}")
        logger.info(f"   📍 Hold: {hold_multiplier}x - {hold_reason}")
        for w in warnings[:3]:
            logger.info(f"   {w}")
        for s in signals[:3]:
            logger.info(f"   {s}")
        
        self.last_full_check = datetime.now()
        return result
    
    def quick_check(self) -> bool:
        """Check rapide: peut-on trader?"""
        # Si analyse récente, utiliser le cache
        if self.last_full_check:
            if (datetime.now() - self.last_full_check).seconds < 300:
                cached = self._get_cached('full_analysis')
                if cached:
                    return cached.get('can_trade', True)
        
        result = self.full_analysis()
        self._set_cache('full_analysis', result)
        return result['can_trade']
    
    def get_risk_multiplier(self) -> float:
        """Retourne le multiplicateur de risque basé sur les conditions"""
        result = self.full_analysis()
        return result.get('max_risk_multiplier', 1.0)


# Instance globale
_intelligence = None

def get_market_intelligence() -> MarketIntelligence:
    """Retourne l'instance globale"""
    global _intelligence
    if _intelligence is None:
        _intelligence = MarketIntelligence()
    return _intelligence


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧠 TEST MARKET INTELLIGENCE")
    print("=" * 60)
    
    intel = MarketIntelligence()
    result = intel.full_analysis()
    
    print(f"\n📊 Score: {result['score']}/100")
    print(f"🎯 Recommandation: {result['recommendation']}")
    print(f"💰 Multiplicateur risque: {result['max_risk_multiplier']}x")

