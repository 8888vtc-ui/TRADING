"""
Script pour tester avec des clés saisies manuellement
"""
from alpaca_trade_api import REST

# Saisissez vos clés ici pour tester
API_KEY = "PKQYJSXQ6NLKKHVUJHA4W3RJI4"
SECRET_KEY = "AQUJqSXwrvtnpfXHVy7tn7qFSwWSWI"  # Vérifiez que c'est complet !
BASE_URL = "https://paper-api.alpaca.markets"

print("🔍 Test avec clés manuelles...")
print(f"API Key: {API_KEY}")
print(f"Secret Key: {SECRET_KEY[:10]}...{SECRET_KEY[-5:] if len(SECRET_KEY) > 15 else ''}")
print(f"Longueur Secret Key: {len(SECRET_KEY)} caractères")
print()

try:
    api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
    account = api.get_account()
    
    print("✅ SUCCÈS !")
    print(f"💰 Cash: ${float(account.cash):,.2f}")
    print(f"📊 Portfolio Value: ${float(account.portfolio_value):,.2f}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    print("💡 Vérifiez:")
    print("   1. La Secret Key est complète (environ 30-40 caractères)")
    print("   2. Pas d'espaces avant/après les clés")
    print("   3. Les clés sont bien pour Paper Trading")

