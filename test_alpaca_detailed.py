"""
Script de test détaillé pour diagnostiquer la connexion Alpaca
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

print("=" * 60)
print("🔍 DIAGNOSTIC DÉTAILLÉ - CONNEXION ALPACA API")
print("=" * 60)
print()

# Vérification des variables
print("📋 Vérification des variables d'environnement:")
print(f"   BASE_URL: {BASE_URL}")
print(f"   API_KEY: {API_KEY[:15]}..." if API_KEY else "   API_KEY: ❌ NON TROUVÉE")
print(f"   SECRET_KEY: {'✅ Trouvée (' + str(len(SECRET_KEY)) + ' caractères)' if SECRET_KEY else '❌ NON TROUVÉE'}")
print()

if not API_KEY:
    print("❌ ERREUR: ALPACA_API_KEY manquante")
    exit(1)

if not SECRET_KEY:
    print("❌ ERREUR: ALPACA_SECRET_KEY manquante")
    exit(1)

# Test de connexion
print("🔌 Tentative de connexion...")
print()

try:
    # Connexion à l'API
    api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
    
    print("✅ Client API créé avec succès")
    print("📡 Requête vers l'API...")
    print()
    
    # Obtenir les informations du compte
    account = api.get_account()
    
    print("=" * 60)
    print("✅ CONNEXION RÉUSSIE !")
    print("=" * 60)
    print()
    print("📊 INFORMATIONS DU COMPTE:")
    print(f"   Account ID: {account.account_number}")
    print(f"   Status: {account.status}")
    print(f"   Trading Blocked: {account.trading_blocked}")
    print(f"   Account Blocked: {account.account_blocked}")
    print(f"   Pattern Day Trader: {account.pattern_day_trader}")
    print()
    print("💰 CAPITAL:")
    print(f"   Cash: ${float(account.cash):,.2f}")
    print(f"   Buying Power: ${float(account.buying_power):,.2f}")
    print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"   Equity: ${float(account.equity):,.2f}")
    print(f"   Long Market Value: ${float(account.long_market_value):,.2f}")
    print(f"   Short Market Value: ${float(account.short_market_value):,.2f}")
    print()
    print("🎯 MODE: Paper Trading (Argent fictif)")
    print("=" * 60)
    
except Exception as e:
    print("=" * 60)
    print("❌ ERREUR DE CONNEXION")
    print("=" * 60)
    print(f"Type d'erreur: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print()
    print("💡 VÉRIFICATIONS À EFFECTUER:")
    print("   1. Vérifiez que les clés API sont correctes dans alpaca_api_keys.env")
    print("   2. Vérifiez que vous utilisez les clés Paper Trading (pas Live)")
    print("   3. Vérifiez que le compte est activé sur le dashboard Alpaca")
    print("   4. Vérifiez votre connexion Internet")
    print("   5. Essayez de régénérer les clés API depuis le dashboard")
    print()
    print("🔗 Dashboard: https://app.alpaca.markets/paper/dashboard/configuration")
    print("=" * 60)
    exit(1)

