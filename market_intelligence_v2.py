"""
🧠 MARKET INTELLIGENCE V2.0 - SYSTÈME COMPLET
=============================================
TOUTES les APIs informatives combinées:
- Fear & Greed Index (Crypto)
- VIX (Volatilité Actions)
- DXY (Dollar Index)
- Calendrier Économique
- Market Cap & Dominance
- Funding Rate (Crypto Futures)
- Trending Assets

+ Cache intelligent
+ Fetch parallèle (async)
+ Scoring unifié
"""

import asyncio
import aiohttp
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import time
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


class MarketIntelligenceV2:
    """
    🧠 Market Intelligence V2.0 - Système complet
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = {
            'fear_greed': 300,      # 5 min
            'vix': 60,              # 1 min
            'dxy': 60,              # 1 min
            'market_overview': 300,  # 5 min
            'calendar': 1800,        # 30 min
            'funding': 300,          # 5 min
            'trending': 600,         # 10 min
        }
        
        self.last_full_analysis = None
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Seuils de décision
        self.thresholds = {
            'fg_optimal_low': 25,
            'fg_optimal_high': 55,
            'fg_danger_high': 80,
            'fg_danger_low': 15,
            'vix_optimal': 18,
            'vix_caution': 25,
            'vix_danger': 35,
            'dxy_bullish': 102,
            'dxy_bearish': 105,
        }
        
        # High-impact events (bloquer trading)
        self.high_impact_events = [
            'FOMC', 'Federal Reserve', 'Interest Rate Decision',
            'Non-Farm Payrolls', 'NFP', 'CPI', 'Consumer Price Index',
            'GDP', 'Unemployment Rate', 'ECB', 'BOE', 'BOJ'
        ]
        
        logger.info("🧠 Market Intelligence V2.0 initialisé")
    
    # ═══════════════════════════════════════════════════════════════
    # CACHE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            duration = self.cache_duration.get(key, 300)
            if time.time() - timestamp < duration:
                return data
        return None
    
    def _set_cache(self, key: str, data: Dict):
        self.cache[key] = (data, time.time())
    
    # ═══════════════════════════════════════════════════════════════
    # 1. FEAR & GREED INDEX
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_fear_greed(self) -> Dict:
        """Fear & Greed Index pour crypto"""
        cached = self._get_cached('fear_greed')
        if cached:
            return cached
        
        try:
            r = requests.get("https://api.alternative.me/fng/", timeout=10)
            data = r.json()
            if data.get('data'):
                value = int(data['data'][0]['value'])
                result = {
                    'value': value,
                    'classification': data['data'][0]['value_classification'],
                    'valid': True
                }
                self._set_cache('fear_greed', result)
                return result
        except Exception as e:
            logger.warning(f"Fear & Greed API: {e}")
        
        return {'value': 50, 'classification': 'Neutral', 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 2. VIX (Volatility Index)
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_vix(self) -> Dict:
        """VIX - Indice de volatilité"""
        cached = self._get_cached('vix')
        if cached:
            return cached
        
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            
            if 'chart' in data and data['chart']['result']:
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                prev = data['chart']['result'][0]['meta'].get('previousClose', price)
                change = ((price - prev) / prev) * 100 if prev else 0
                
                result = {
                    'value': round(price, 2),
                    'change': round(change, 2),
                    'level': 'DANGER' if price > 35 else 'HIGH' if price > 25 else 'NORMAL' if price > 15 else 'LOW',
                    'valid': True
                }
                self._set_cache('vix', result)
                return result
        except Exception as e:
            logger.warning(f"VIX API: {e}")
        
        return {'value': 20, 'change': 0, 'level': 'NORMAL', 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 3. DXY (Dollar Index) - NOUVEAU
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_dxy(self) -> Dict:
        """Dollar Index - Corrélation inverse crypto/actions"""
        cached = self._get_cached('dxy')
        if cached:
            return cached
        
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            
            if 'chart' in data and data['chart']['result']:
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                prev = data['chart']['result'][0]['meta'].get('previousClose', price)
                change = ((price - prev) / prev) * 100 if prev else 0
                
                # DXY élevé = bearish pour crypto/actions
                signal = 'BEARISH' if price > 105 else 'NEUTRAL' if price > 102 else 'BULLISH'
                
                result = {
                    'value': round(price, 2),
                    'change': round(change, 2),
                    'signal': signal,
                    'valid': True
                }
                self._set_cache('dxy', result)
                return result
        except Exception as e:
            logger.warning(f"DXY API: {e}")
        
        return {'value': 103, 'change': 0, 'signal': 'NEUTRAL', 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 4. CALENDRIER ÉCONOMIQUE - NOUVEAU (CRITIQUE)
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_economic_calendar(self) -> Dict:
        """Calendrier économique - Détecte events high-impact"""
        cached = self._get_cached('calendar')
        if cached:
            return cached
        
        try:
            # Utiliser API investing.com ou alternative
            # Pour l'instant, simulation basée sur jour/heure
            now = datetime.now()
            
            # Jours typiques FOMC: Mercredi après 1ère semaine du mois
            # NFP: 1er vendredi du mois
            
            is_fomc_week = (now.day <= 14 and now.weekday() == 2)  # Mercredi, 2 premières semaines
            is_nfp_day = (now.day <= 7 and now.weekday() == 4)      # Vendredi, 1ère semaine
            
            block = False
            reason = None
            
            # Heures critiques (EST)
            hour_est = (now.hour - 5) % 24  # Approximation
            
            if is_fomc_week and 13 <= hour_est <= 15:
                block = True
                reason = "FOMC Meeting - Attendre 30min après annonce"
            elif is_nfp_day and 7 <= hour_est <= 10:
                block = True
                reason = "NFP Release - Forte volatilité attendue"
            
            result = {
                'block_trading': block,
                'reason': reason,
                'is_fomc_week': is_fomc_week,
                'is_nfp_day': is_nfp_day,
                'valid': True
            }
            self._set_cache('calendar', result)
            return result
            
        except Exception as e:
            logger.warning(f"Calendar: {e}")
        
        return {'block_trading': False, 'reason': None, 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 5. MARKET OVERVIEW (CoinGecko)
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_market_overview(self) -> Dict:
        """Vue globale du marché crypto"""
        cached = self._get_cached('market_overview')
        if cached:
            return cached
        
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
                    'active_cryptos': d.get('active_cryptocurrencies', 0),
                    'valid': True
                }
                self._set_cache('market_overview', result)
                return result
        except Exception as e:
            logger.warning(f"Market overview: {e}")
        
        return {'btc_dominance': 50, 'market_cap_change_24h': 0, 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 6. FUNDING RATE (Crypto Futures) - NOUVEAU
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_funding_rate(self) -> Dict:
        """Funding Rate - Détecte les squeezes potentiels"""
        cached = self._get_cached('funding')
        if cached:
            return cached
        
        try:
            # Binance Futures API (public)
            url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
            r = requests.get(url, timeout=10)
            data = r.json()
            
            if data and len(data) > 0:
                rate = float(data[0]['fundingRate']) * 100
                
                # Funding positif = beaucoup de longs → short squeeze possible
                # Funding négatif = beaucoup de shorts → long squeeze possible
                if rate > 0.1:
                    squeeze_risk = 'SHORT_SQUEEZE'
                    signal = 'BEARISH'  # Trop de longs
                elif rate < -0.1:
                    squeeze_risk = 'LONG_SQUEEZE'
                    signal = 'BULLISH'  # Trop de shorts
                else:
                    squeeze_risk = 'NONE'
                    signal = 'NEUTRAL'
                
                result = {
                    'btc_funding': round(rate, 4),
                    'squeeze_risk': squeeze_risk,
                    'signal': signal,
                    'valid': True
                }
                self._set_cache('funding', result)
                return result
        except Exception as e:
            logger.warning(f"Funding rate: {e}")
        
        return {'btc_funding': 0, 'squeeze_risk': 'NONE', 'signal': 'NEUTRAL', 'valid': False}
    
    # ═══════════════════════════════════════════════════════════════
    # 7. TRENDING
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_trending(self) -> Dict:
        """Cryptos tendances"""
        cached = self._get_cached('trending')
        if cached:
            return cached
        
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
    # FETCH ALL PARALLEL
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_all_parallel(self) -> Dict:
        """Fetch toutes les APIs en parallèle (thread pool)"""
        start = time.time()
        
        futures = {
            'fear_greed': self.executor.submit(self.fetch_fear_greed),
            'vix': self.executor.submit(self.fetch_vix),
            'dxy': self.executor.submit(self.fetch_dxy),
            'market': self.executor.submit(self.fetch_market_overview),
            'calendar': self.executor.submit(self.fetch_economic_calendar),
            'funding': self.executor.submit(self.fetch_funding_rate),
            'trending': self.executor.submit(self.fetch_trending),
        }
        
        results = {}
        for key, future in futures.items():
            try:
                results[key] = future.result(timeout=15)
            except Exception as e:
                logger.warning(f"Fetch {key} timeout: {e}")
                results[key] = {}
        
        elapsed = time.time() - start
        logger.info(f"📡 Toutes APIs récupérées en {elapsed:.2f}s")
        
        return results
    
    # ═══════════════════════════════════════════════════════════════
    # FULL ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    def full_analysis(self) -> Dict:
        """
        🧠 ANALYSE COMPLÈTE DU MARCHÉ
        Combine TOUTES les APIs et retourne un score unifié
        """
        logger.info("\n" + "=" * 60)
        logger.info("🧠 ANALYSE MARKET INTELLIGENCE V2.0")
        logger.info("=" * 60)
        
        # Fetch all en parallèle
        data = self.fetch_all_parallel()
        
        fear_greed = data.get('fear_greed', {})
        vix = data.get('vix', {})
        dxy = data.get('dxy', {})
        market = data.get('market', {})
        calendar = data.get('calendar', {})
        funding = data.get('funding', {})
        
        # ═══════════════════════════════════════════════════════════
        # VÉRIFICATION CALENDRIER (BLOQUANT)
        # ═══════════════════════════════════════════════════════════
        if calendar.get('block_trading'):
            logger.warning(f"🚫 TRADING BLOQUÉ: {calendar['reason']}")
            return {
                'score': 0,
                'can_trade': False,
                'block_reason': calendar['reason'],
                'recommendation': '🚫 ATTENDRE - EVENT ÉCONOMIQUE MAJEUR',
                'data': data
            }
        
        # ═══════════════════════════════════════════════════════════
        # SCORING
        # ═══════════════════════════════════════════════════════════
        score = 50  # Base
        warnings = []
        signals = []
        
        # 1. Fear & Greed (max ±25)
        fg = fear_greed.get('value', 50)
        logger.info(f"🎭 Fear & Greed: {fg} ({fear_greed.get('classification', 'N/A')})")
        
        if fg >= 80:
            score -= 25
            warnings.append(f"⚠️ DANGER: Cupidité extrême ({fg})")
        elif fg >= 70:
            score -= 15
            warnings.append(f"⚠️ Cupidité élevée ({fg})")
        elif fg <= 15:
            score -= 20
            warnings.append(f"⚠️ Peur extrême ({fg}) - Volatilité!")
        elif fg <= 25:
            score += 15
            signals.append(f"✅ Peur = Opportunité contrarian ({fg})")
        elif 40 <= fg <= 55:
            score += 20
            signals.append(f"✅ Zone optimale ({fg})")
        
        # 2. VIX (max ±20)
        vix_val = vix.get('value', 20)
        logger.info(f"📊 VIX: {vix_val} ({vix.get('level', 'N/A')})")
        
        if vix_val >= 35:
            score -= 20
            warnings.append(f"⚠️ VIX DANGER ({vix_val})")
        elif vix_val >= 25:
            score -= 10
            warnings.append(f"⚠️ VIX élevé ({vix_val})")
        elif vix_val <= 18:
            score += 10
            signals.append(f"✅ VIX optimal ({vix_val})")
        
        # 3. DXY (max ±15) - NOUVEAU
        dxy_val = dxy.get('value', 103)
        dxy_signal = dxy.get('signal', 'NEUTRAL')
        logger.info(f"💵 DXY: {dxy_val} ({dxy_signal})")
        
        if dxy_signal == 'BEARISH':
            score -= 10
            warnings.append(f"⚠️ Dollar fort ({dxy_val}) - Baissier crypto/actions")
        elif dxy_signal == 'BULLISH':
            score += 10
            signals.append(f"✅ Dollar faible ({dxy_val}) - Haussier crypto/actions")
        
        # 4. Market Cap Change (max ±15)
        mc_change = market.get('market_cap_change_24h', 0)
        logger.info(f"📈 Market Cap 24h: {mc_change:+.2f}%")
        
        if mc_change > 5:
            score += 15
            signals.append(f"✅ Marché très haussier (+{mc_change}%)")
        elif mc_change > 2:
            score += 10
            signals.append(f"✅ Marché haussier (+{mc_change}%)")
        elif mc_change < -5:
            score -= 15
            warnings.append(f"⚠️ Marché très baissier ({mc_change}%)")
        elif mc_change < -2:
            score -= 10
            warnings.append(f"⚠️ Marché baissier ({mc_change}%)")
        
        # 5. Funding Rate (max ±10) - NOUVEAU
        funding_rate = funding.get('btc_funding', 0)
        squeeze = funding.get('squeeze_risk', 'NONE')
        logger.info(f"💰 Funding Rate: {funding_rate:.4f}% ({squeeze})")
        
        if squeeze == 'LONG_SQUEEZE':
            score += 10
            signals.append(f"✅ Long squeeze possible - Bullish")
        elif squeeze == 'SHORT_SQUEEZE':
            score -= 5
            warnings.append(f"⚠️ Short squeeze possible - Prudence")
        
        # Clamp score
        score = max(0, min(100, score))
        
        # ═══════════════════════════════════════════════════════════
        # DÉCISION
        # ═══════════════════════════════════════════════════════════
        can_trade = score >= 35
        can_leverage = score >= 60
        force_max = score >= 85
        
        if score >= 85:
            recommendation = "🔥🔥🔥 CONDITIONS EXCEPTIONNELLES - LEVERAGE MAX!"
            risk_mult = 2.5
            hold_mult = 2.5
        elif score >= 75:
            recommendation = "🔥🔥 CONDITIONS EXCELLENTES"
            risk_mult = 2.0
            hold_mult = 2.0
        elif score >= 60:
            recommendation = "🟢 CONDITIONS BONNES"
            risk_mult = 1.5
            hold_mult = 1.5
        elif score >= 50:
            recommendation = "🟡 CONDITIONS NORMALES"
            risk_mult = 1.0
            hold_mult = 1.0
        elif score >= 35:
            recommendation = "🟠 CONDITIONS PRUDENTES"
            risk_mult = 0.7
            hold_mult = 0.7
        else:
            recommendation = "🔴 CONDITIONS DÉFAVORABLES - NE PAS TRADER"
            risk_mult = 0.0
            hold_mult = 0.5
        
        # ═══════════════════════════════════════════════════════════
        # LOG RÉSULTAT
        # ═══════════════════════════════════════════════════════════
        logger.info("\n" + "-" * 50)
        logger.info(f"🏆 SCORE FINAL: {score}/100")
        logger.info(f"   {recommendation}")
        logger.info(f"   Peut trader: {'✅' if can_trade else '❌'}")
        logger.info(f"   Peut leverage: {'✅' if can_leverage else '❌'}")
        logger.info(f"   Risk mult: {risk_mult}x | Hold mult: {hold_mult}x")
        
        for w in warnings[:3]:
            logger.info(f"   {w}")
        for s in signals[:3]:
            logger.info(f"   {s}")
        
        self.last_full_analysis = datetime.now()
        
        return {
            'score': score,
            'can_trade': can_trade,
            'can_leverage': can_leverage,
            'force_max_leverage': force_max,
            'recommendation': recommendation,
            'risk_multiplier': risk_mult,
            'hold_multiplier': hold_mult,
            'warnings': warnings,
            'signals': signals,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    
    def quick_check(self) -> bool:
        """Check rapide: peut-on trader?"""
        if self.last_full_analysis:
            cached = self._get_cached('full_analysis')
            if cached:
                return cached.get('can_trade', True)
        
        result = self.full_analysis()
        self._set_cache('full_analysis', result)
        return result['can_trade']


# ═══════════════════════════════════════════════════════════════════
# INSTANCE GLOBALE
# ═══════════════════════════════════════════════════════════════════
_intelligence_v2 = None

def get_market_intelligence_v2() -> MarketIntelligenceV2:
    global _intelligence_v2
    if _intelligence_v2 is None:
        _intelligence_v2 = MarketIntelligenceV2()
    return _intelligence_v2


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
    
    print("\n🧠 TEST MARKET INTELLIGENCE V2.0")
    print("=" * 60)
    
    intel = MarketIntelligenceV2()
    result = intel.full_analysis()
    
    print(f"\n📊 Score Final: {result['score']}/100")
    print(f"🎯 {result['recommendation']}")

