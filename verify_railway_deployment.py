"""
Script de vérification pour le déploiement Railway
"""
import os
from dotenv import load_dotenv
from alpaca_trade_api import REST
from datetime import datetime

# Charger les variables (depuis Railway ou local)
load_dotenv('alpaca_api_keys.env')

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

print("=" * 60)
print("🔍 VÉRIFICATION DU DÉPLOIEMENT")
print("=" * 60)
print()

# Vérifier les variables
print("📋 Variables d'environnement:")
print(f"   ALPACA_API_KEY: {'✅ Trouvée' if API_KEY else '❌ Manquante'}")
print(f"   ALPACA_SECRET_KEY: {'✅ Trouvée' if SECRET_KEY else '❌ Manquante'}")
print(f"   ALPACA_BASE_URL: {BASE_URL}")
print()

if not API_KEY or not SECRET_KEY:
    print("❌ Variables manquantes !")
    exit(1)

# Tester la connexion
print("🔌 Test de connexion à l'API Alpaca...")
try:
    api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
    account = api.get_account()
    
    print("✅ Connexion réussie !")
    print()
    print("📊 Informations du compte:")
    print(f"   Account ID: {account.account_number}")
    print(f"   Status: {account.status}")
    print(f"   Cash: ${float(account.cash):,.2f}")
    print(f"   Buying Power: ${float(account.buying_power):,.2f}")
    print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print()
    
    # Vérifier le marché
    clock = api.get_clock()
    print("🏪 État du marché:")
    print(f"   Ouvert: {'✅ Oui' if clock.is_open else '❌ Non'}")
    print(f"   Heure NY: {clock.timestamp}")
    print()
    
    # Vérifier les positions
    positions = api.list_positions()
    print(f"📊 Positions ouvertes: {len(positions)}")
    if positions:
        for pos in positions:
            print(f"   • {pos.symbol}: {pos.qty} @ ${float(pos.avg_entry_price):.2f}")
    print()
    
    print("=" * 60)
    print("✅ TOUT FONCTIONNE CORRECTEMENT !")
    print("=" * 60)
    print()
    print("🚀 Le bot est prêt à trader sur Railway !")
    print()
    print("💡 Prochaines étapes:")
    print("   1. Vérifiez les logs Railway pour voir le bot en action")
    print("   2. Le bot scanne toutes les 5 minutes")
    print("   3. Il trade uniquement aux heures optimales:")
    print("      • 16:30-18:00 Paris (matin US)")
    print("      • 20:00-21:30 Paris (après-midi US)")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    print("💡 Vérifiez:")
    print("   1. Que les variables sont bien configurées dans Railway")
    print("   2. Que le service est déployé et en cours d'exécution")
    print("   3. Consultez les logs Railway pour plus de détails")

