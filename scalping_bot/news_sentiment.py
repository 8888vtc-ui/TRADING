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
        Initialise l'analyseur avec NewsAPI, Gemini (Google) et Anthropic (Claude)
        """
        self.alpaca_key = api_key or os.getenv('ALPACA_API_KEY')
        self.alpaca_secret = secret_key or os.getenv('ALPACA_SECRET_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_ORG_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        self.api = None
        self._init_api()
        
        # Clients externes
        self.newsapi_client = None
        if self.newsapi_key:
            try:
                from newsapi import NewsApiClient
                self.newsapi_client = NewsApiClient(api_key=self.newsapi_key)
                logger.info("✅ NewsAPI.org initialisé")
            except ImportError:
                logger.warning("⚠️ newsapi-python non installé")

        # 1. Gemini (Gratuit - Prioritaire)
        self.gemini_model = None
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Google Gemini (Gratuit) initialisé (Prioritaire)")
            except ImportError:
                logger.warning("⚠️ google-generativeai non installé")

        # 2. Claude (Payant - Backup)
        self.anthropic_client = None
        if self.anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
                logger.info("✅ Anthropic Claude (Backup) initialisé")
            except ImportError:
                logger.warning("⚠️ anthropic non installé")
        
        # Cache
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(minutes=15)
        
    def _analyze_with_ai(self, text: str, symbol: str) -> float:
        """
        Analyse Double Garantie:
        1. Essaie Gemini (Gratuit)
        2. Si échec, essaie Claude (Backup)
        3. Si échec, méthode classique
        """
        
        # TENTATIVE 1: GEMINI
        if self.gemini_model:
            try:
                prompt = f"""
                Analyze the sentiment of this news text regarding {symbol} for intraday trading.
                Return ONLY a number between -1.0 (Very Bearish) and 1.0 (Very Bullish).
                Text: "{text[:3000]}"
                """
                response = self.gemini_model.generate_content(prompt)
                if response.text:
                    return float(response.text.strip())
            except Exception as e:
                logger.warning(f"⚠️ Gemini a échoué, passage au backup Claude... ({e})")

        # TENTATIVE 2: CLAUDE
        if self.anthropic_client:
            try:
                prompt = f"""
                Analyze the sentiment of this news text regarding {symbol} for intraday trading.
                Return ONLY a number between -1.0 (Very Bearish) and 1.0 (Very Bullish).
                Text: "{text[:2000]}"
                """
                message = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": prompt}]
                )
                if message.content:
                    return float(message.content[0].text.strip())
            except Exception as e:
                logger.error(f"❌ Claude a aussi échoué: {e}")

        # TENTATIVE 3: SIMPLE (FALLBACK)
        return self._analyze_text_sentiment(text)

    def get_news_sentiment(self, symbol: str, lookback_minutes: int = 60) -> dict:
        """Récupère news via Alpaca + NewsAPI et analyse avec AI (Double Garantie)"""
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d%H')}"
        if cache_key in self.cache: return self.cache[cache_key]['data']
        
        headlines = []
        full_text = ""
        
        # 1. NewsAPI
        if self.newsapi_client:
            try:
                top_headlines = self.newsapi_client.get_everything(
                    q=symbol,
                    language='en',
                    sort_by='publishedAt',
                    page_size=5
                )
                for article in top_headlines.get('articles', []):
                    h = article['title']
                    headlines.append({'headline': h, 'source': 'NewsAPI'})
                    full_text += f"{h}. "
            except Exception as e:
                logger.warning(f"⚠️ NewsAPI Error: {e}")

        # 2. Alpaca News
        if self.api:
            try:
                end = datetime.now(NY_TZ)
                start = end - timedelta(minutes=lookback_minutes)
                news = self.api.get_news(symbol=symbol, start=start.isoformat(), end=end.isoformat(), limit=3)
                for article in news:
                    h = article.headline
                    headlines.append({'headline': h, 'source': 'Alpaca'})
                    full_text += f"{h}. "
            except: pass
            
        # 3. Analyse
        if not full_text:
            return {'sentiment_score': 0.0, 'news_count': 0, 'recommendation': 'NEUTRAL'}
            
        sentiment_score = self._analyze_with_ai(full_text, symbol)
        
        result = {
            'sentiment_score': sentiment_score,
            'news_count': len(headlines),
            'high_impact': abs(sentiment_score) > 0.8,
            'headlines': headlines,
            'recommendation': 'BULLISH' if sentiment_score > 0.3 else 'BEARISH' if sentiment_score < -0.3 else 'NEUTRAL'
        }
        
        self.cache[cache_key] = {'timestamp': datetime.now(), 'data': result}
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

