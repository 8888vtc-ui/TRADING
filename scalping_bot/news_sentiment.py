"""
📰 MODULE NEWS & SENTIMENT API
==============================
Intègre les news pour améliorer les décisions de trading

SOURCES:
- Alpaca News API (gratuit avec compte Alpaca)
- Analyse de sentiment basique

UTILISATION:
- Bonus de +1 point si sentiment positif
- Pénalité de -0.5 point si sentiment négatif
- Filtre les trades pendant les annonces importantes
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pytz

logger = logging.getLogger(__name__)

NY_TZ = pytz.timezone('America/New_York')

# Mots-clés pour analyse de sentiment simple
POSITIVE_KEYWORDS = [
    'surge', 'soar', 'jump', 'rally', 'gain', 'rise', 'up', 'high', 'record',
    'beat', 'exceed', 'outperform', 'strong', 'growth', 'profit', 'bullish',
    'upgrade', 'buy', 'positive', 'success', 'breakthrough', 'win', 'deal',
    'partnership', 'expansion', 'launch', 'innovative', 'record-breaking'
]

NEGATIVE_KEYWORDS = [
    'fall', 'drop', 'decline', 'plunge', 'crash', 'down', 'low', 'miss',
    'weak', 'loss', 'bearish', 'downgrade', 'sell', 'negative', 'fail',
    'concern', 'risk', 'warning', 'lawsuit', 'investigation', 'cut',
    'layoff', 'restructuring', 'delay', 'recall', 'scandal', 'fraud'
]

# Mots-clés d'événements majeurs (éviter de trader)
HIGH_IMPACT_KEYWORDS = [
    'fed', 'fomc', 'interest rate', 'inflation', 'cpi', 'jobs report',
    'earnings', 'guidance', 'sec', 'investigation', 'bankruptcy',
    'merger', 'acquisition', 'takeover', 'split', 'dividend'
]


class NewsSentimentAnalyzer:
    """
    Analyseur de sentiment basé sur les news
    =========================================
    Utilise l'API Alpaca News (gratuite)
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = None):
        """
        Initialise l'analyseur avec les credentials Alpaca
        """
        self.api_key = api_key or os.getenv('ALPACA_API_KEY') or os.getenv('APCA_API_KEY_ID')
        self.secret_key = secret_key or os.getenv('ALPACA_SECRET_KEY') or os.getenv('APCA_API_SECRET_KEY')
        self.base_url = base_url or 'https://data.alpaca.markets'
        
        self.api = None
        self._init_api()
        
        # Cache pour éviter trop d'appels API
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(minutes=5)
        
    def _init_api(self):
        """Initialise l'API Alpaca"""
        try:
            from alpaca_trade_api import REST
            if self.api_key and self.secret_key:
                self.api = REST(
                    self.api_key,
                    self.secret_key,
                    base_url='https://paper-api.alpaca.markets'
                )
                logger.info("✅ API News initialisée")
            else:
                logger.warning("⚠️ Credentials Alpaca non trouvées - News désactivées")
        except ImportError:
            logger.warning("⚠️ alpaca_trade_api non installé")
        except Exception as e:
            logger.warning(f"⚠️ Erreur init API News: {e}")
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """
        Analyse simple du sentiment d'un texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            Score entre -1 (négatif) et +1 (positif)
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
        negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        # Score normalisé entre -1 et +1
        score = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, score))
    
    def _has_high_impact_event(self, text: str) -> bool:
        """
        Vérifie si le texte contient des événements à fort impact
        """
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in HIGH_IMPACT_KEYWORDS)
    
    def get_news_sentiment(self, symbol: str, lookback_minutes: int = 60) -> dict:
        """
        Récupère et analyse le sentiment des news pour un symbole
        
        Args:
            symbol: Symbole de l'action (ex: 'AAPL')
            lookback_minutes: Période à analyser
        
        Returns:
            dict avec: sentiment_score, news_count, high_impact, headlines
        """
        # Vérifier le cache
        cache_key = f"{symbol}_{datetime.now(NY_TZ).strftime('%Y%m%d%H%M')}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now(NY_TZ) - cached['timestamp'] < self.cache_duration:
                return cached['data']
        
        result = {
            'sentiment_score': 0.0,
            'news_count': 0,
            'high_impact': False,
            'headlines': [],
            'recommendation': 'NEUTRAL'
        }
        
        # Si pas d'API, retourner neutre
        if not self.api:
            return result
        
        try:
            # Récupérer les news via Alpaca
            end = datetime.now(NY_TZ)
            start = end - timedelta(minutes=lookback_minutes)
            
            news = self.api.get_news(
                symbol=symbol,
                start=start.isoformat(),
                end=end.isoformat(),
                limit=10
            )
            
            if not news:
                return result
            
            sentiments = []
            headlines = []
            
            for article in news:
                headline = getattr(article, 'headline', '')
                summary = getattr(article, 'summary', '')
                
                full_text = f"{headline} {summary}"
                
                # Vérifier événement à fort impact
                if self._has_high_impact_event(full_text):
                    result['high_impact'] = True
                
                # Analyser le sentiment
                sentiment = self._analyze_text_sentiment(full_text)
                sentiments.append(sentiment)
                headlines.append({
                    'headline': headline,
                    'sentiment': sentiment,
                    'time': getattr(article, 'created_at', '')
                })
            
            # Calculer le sentiment moyen
            if sentiments:
                result['sentiment_score'] = sum(sentiments) / len(sentiments)
                result['news_count'] = len(sentiments)
                result['headlines'] = headlines[:5]  # Top 5
                
                # Recommandation
                if result['high_impact']:
                    result['recommendation'] = 'AVOID'  # Éviter pendant événements majeurs
                elif result['sentiment_score'] > 0.3:
                    result['recommendation'] = 'BULLISH'
                elif result['sentiment_score'] < -0.3:
                    result['recommendation'] = 'BEARISH'
                else:
                    result['recommendation'] = 'NEUTRAL'
            
            # Mettre en cache
            self.cache[cache_key] = {
                'timestamp': datetime.now(NY_TZ),
                'data': result
            }
            
            logger.info(f"📰 {symbol}: Sentiment={result['sentiment_score']:.2f} "
                       f"({result['news_count']} news) - {result['recommendation']}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération news {symbol}: {e}")
        
        return result
    
    def get_market_sentiment(self, symbols: List[str]) -> dict:
        """
        Analyse le sentiment global du marché
        
        Args:
            symbols: Liste de symboles à analyser
        
        Returns:
            dict avec sentiment global et par symbole
        """
        results = {}
        sentiments = []
        
        for symbol in symbols:
            result = self.get_news_sentiment(symbol)
            results[symbol] = result
            if result['news_count'] > 0:
                sentiments.append(result['sentiment_score'])
        
        # Sentiment global
        global_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Compter les événements à fort impact
        high_impact_count = sum(1 for r in results.values() if r['high_impact'])
        
        return {
            'global_sentiment': global_sentiment,
            'symbols': results,
            'high_impact_events': high_impact_count,
            'recommendation': 'AVOID' if high_impact_count > 0 else (
                'BULLISH' if global_sentiment > 0.2 else (
                    'BEARISH' if global_sentiment < -0.2 else 'NEUTRAL'
                )
            )
        }
    
    def should_trade(self, symbol: str) -> tuple:
        """
        Détermine si on devrait trader ce symbole basé sur les news
        
        Args:
            symbol: Symbole à vérifier
        
        Returns:
            tuple: (should_trade: bool, reason: str, sentiment: float)
        """
        sentiment_data = self.get_news_sentiment(symbol)
        
        # Éviter pendant les événements majeurs
        if sentiment_data['high_impact']:
            return False, "Événement à fort impact détecté", sentiment_data['sentiment_score']
        
        # Éviter si sentiment très négatif
        if sentiment_data['sentiment_score'] < -0.5:
            return False, f"Sentiment très négatif ({sentiment_data['sentiment_score']:.2f})", sentiment_data['sentiment_score']
        
        return True, sentiment_data['recommendation'], sentiment_data['sentiment_score']


class MockNewsSentimentAnalyzer:
    """
    Version mock pour tests sans API
    """
    
    def get_news_sentiment(self, symbol: str, lookback_minutes: int = 60) -> dict:
        return {
            'sentiment_score': 0.0,
            'news_count': 0,
            'high_impact': False,
            'headlines': [],
            'recommendation': 'NEUTRAL'
        }
    
    def get_market_sentiment(self, symbols: List[str]) -> dict:
        return {
            'global_sentiment': 0.0,
            'symbols': {},
            'high_impact_events': 0,
            'recommendation': 'NEUTRAL'
        }
    
    def should_trade(self, symbol: str) -> tuple:
        return True, "NEUTRAL", 0.0


def get_sentiment_analyzer() -> NewsSentimentAnalyzer:
    """
    Factory pour obtenir l'analyseur approprié
    """
    try:
        analyzer = NewsSentimentAnalyzer()
        if analyzer.api:
            return analyzer
    except:
        pass
    
    logger.info("📰 Utilisation de l'analyseur mock (pas d'API)")
    return MockNewsSentimentAnalyzer()


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = get_sentiment_analyzer()
    
    # Test avec quelques symboles
    symbols = ['AAPL', 'TSLA', 'NVDA']
    
    for symbol in symbols:
        result = analyzer.get_news_sentiment(symbol)
        print(f"\n{symbol}:")
        print(f"  Sentiment: {result['sentiment_score']:.2f}")
        print(f"  News: {result['news_count']}")
        print(f"  Recommandation: {result['recommendation']}")
        
    # Test global
    market = analyzer.get_market_sentiment(symbols)
    print(f"\n📊 Marché global: {market['global_sentiment']:.2f}")
    print(f"   Recommandation: {market['recommendation']}")

