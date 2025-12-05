"""
Script de test pour vérifier la connexion à l'API Alpaca
"""
import os
from dotenv import load_dotenv
from alpaca_trade_api import REST

# Charger les variables d'environnement
load_dotenv('alpaca_api_keys.env')

# Configuration
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

def test_connection():
    """Teste la connexion à l'API Alpaca"""
    
    print("🔍 Test de connexion à Alpaca API...")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:10]}..." if API_KEY else "❌ API Key non trouvée")
    print()
    
    if not API_KEY:
        print("❌ ERREUR: ALPACA_API_KEY non trouvée dans alpaca_api_keys.env")
        return False
    
    if not SECRET_KEY:
        print("⚠️  ATTENTION: ALPACA_SECRET_KEY non trouvée")
        print("   Vous devez ajouter votre Secret Key dans alpaca_api_keys.env")
        return False
    
    try:
        # Connexion à l'API
        api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
        
        # Obtenir les informations du compte
        account = api.get_account()
        
        print("✅ Connexion réussie !")
        print()
        print("📊 Informations du compte:")
        print(f"   Status: {account.status}")
        print(f"   Trading Blocked: {account.trading_blocked}")
        print(f"   Account Blocked: {account.account_blocked}")
        print()
        print("💰 Capital:")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"   Equity: ${float(account.equity):,.2f}")
        print()
        print("🎯 Mode: Paper Trading (Argent fictif)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("💡 Vérifications:")
        print("   1. Vérifiez que vos clés API sont correctes")
        print("   2. Vérifiez que vous êtes connecté à Internet")
        print("   3. Vérifiez que le compte est activé")
        return False

if __name__ == "__main__":
    test_connection()

