
import os
import sys
from alpaca_trade_api import REST

def verify_leverage():
    print("🔍 VÉRIFICATION DU LEVERAGE ALPACA...")
    
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    if not api_key:
        print("❌ API Key manquante")
        return

    try:
        api = REST(api_key, secret_key, base_url)
        account = api.get_account()
        
        print(f"\n📊 INFO COMPTE:")
        print(f"   Status: {account.status}")
        print(f"   Currency: {account.currency}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"   Buying Power (Total): ${float(account.buying_power):,.2f}")
        print(f"   RegT Buying Power: ${float(account.regt_buying_power):,.2f}")
        print(f"   Daytrading Buying Power: ${float(account.daytrading_buying_power):,.2f}")
        print(f"   Multiplier (Levier théorique): {account.multiplier}x")
        
        # Test Crypto specific
        print(f"\n🪙 CRYPTO CAPABILITY:")
        try:
            # Check for generic crypto asset
            asset = api.get_asset('BTC/USD')
            print(f"   BTC/USD Tradable: {asset.tradable}")
            print(f"   BTC/USD Marginable: {asset.marginable}")
            print(f"   BTC/USD Shortable: {asset.shortable}")
        except Exception as e:
            print(f"   ❌ Erreur Asset Check: {e}")

        # Simulation
        print(f"\n⚡ TEST DE CALCUL:")
        cash = float(account.cash)
        bp = float(account.buying_power)
        
        if bp > cash * 1.5:
            print(f"   ✅ LEVERAGE DISPONIBLE sur le compte globable.")
            print(f"   Vous avez ${bp:,.2f} de puissance pour ${cash:,.2f} de cash.")
            print(f"   C'est un ratio de {bp/cash:.2f}x.")
        else:
            print(f"   ⚠️ ATTENTION: Le Buying Power est proche du Cash.")
            print(f"   Il est possible que le leverage soit désactivé ou restreint (Compte Cash vs Margin).")
            
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

if __name__ == "__main__":
    verify_leverage()
