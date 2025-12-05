"""
🔮 PRÉDICTIONS EN TEMPS RÉEL - 5 Décembre 2025
Utilise les APIs pour analyser le marché MAINTENANT
"""

import requests
from datetime import datetime
import json

def fetch_fear_greed():
    """Fear & Greed Index"""
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=10)
        data = r.json()
        return {
            'value': int(data['data'][0]['value']),
            'sentiment': data['data'][0]['value_classification']
        }
    except:
        return {'value': 50, 'sentiment': 'Neutral'}

def fetch_crypto_global():
    """CoinGecko Global Data"""
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        data = r.json()['data']
        return {
            'btc_dominance': round(data['market_cap_percentage']['btc'], 1),
            'eth_dominance': round(data['market_cap_percentage']['eth'], 1),
            'market_cap_change_24h': round(data['market_cap_change_percentage_24h_usd'], 2),
            'total_market_cap': data['total_market_cap']['usd'],
            'total_volume': data['total_volume']['usd']
        }
    except:
        return {'btc_dominance': 50, 'eth_dominance': 18, 'market_cap_change_24h': 0}

def fetch_btc_price():
    """Prix BTC actuel"""
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true", timeout=10)
        data = r.json()
        return {
            'btc': {'price': data['bitcoin']['usd'], 'change_24h': round(data['bitcoin']['usd_24h_change'], 2)},
            'eth': {'price': data['ethereum']['usd'], 'change_24h': round(data['ethereum']['usd_24h_change'], 2)},
            'sol': {'price': data['solana']['usd'], 'change_24h': round(data['solana']['usd_24h_change'], 2)}
        }
    except:
        return {}

def analyze_and_predict():
    """Analyse complète et prédictions"""
    
    print("=" * 70)
    print("🔮 PRÉDICTIONS EN TEMPS RÉEL - " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    print("=" * 70)
    
    # Récupérer les données
    print("\n📡 Récupération des données...")
    
    fear_greed = fetch_fear_greed()
    crypto_global = fetch_crypto_global()
    prices = fetch_btc_price()
    
    # ═══════════════════════════════════════════════════════════════
    # AFFICHAGE DES DONNÉES
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 70)
    print("📊 DONNÉES MARCHÉ ACTUELLES")
    print("─" * 70)
    
    # Fear & Greed
    fg = fear_greed['value']
    fg_emoji = "😱" if fg < 25 else "😰" if fg < 45 else "😐" if fg < 55 else "😊" if fg < 75 else "🤑"
    print(f"\n🎭 Fear & Greed Index: {fg} ({fear_greed['sentiment']}) {fg_emoji}")
    
    # Crypto Global
    print(f"\n🌍 Marché Global Crypto:")
    print(f"   ├── BTC Dominance: {crypto_global['btc_dominance']}%")
    print(f"   ├── ETH Dominance: {crypto_global['eth_dominance']}%")
    mc_change = crypto_global['market_cap_change_24h']
    mc_emoji = "🚀" if mc_change > 3 else "📈" if mc_change > 0 else "📉" if mc_change > -3 else "💥"
    print(f"   └── Market Cap 24h: {mc_change:+.2f}% {mc_emoji}")
    
    # Prix
    if prices:
        print(f"\n💰 Prix Actuels:")
        for coin, data in prices.items():
            ch = data['change_24h']
            emoji = "🟢" if ch > 2 else "🔵" if ch > 0 else "🔴" if ch > -2 else "⚫"
            print(f"   ├── {coin.upper()}: ${data['price']:,.2f} ({ch:+.2f}%) {emoji}")
    
    # ═══════════════════════════════════════════════════════════════
    # CALCUL DU SCORE UNIFIÉ
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 70)
    print("🏆 CALCUL SCORE UNIFIÉ")
    print("─" * 70)
    
    score = 50  # Base
    reasons = []
    
    # Fear & Greed (max 25 points)
    if 25 <= fg <= 55:
        score += 25
        reasons.append(f"✅ F&G zone optimale ({fg}): +25")
    elif 55 < fg <= 70:
        score += 15
        reasons.append(f"✅ F&G neutre-positif ({fg}): +15")
    elif fg > 75:
        score -= 10
        reasons.append(f"⚠️ F&G trop élevé ({fg}): -10")
    elif fg < 25:
        score += 10  # Contrarian
        reasons.append(f"✅ F&G peur = opportunité ({fg}): +10")
    
    # Market Cap Change (max 20 points)
    if mc_change > 5:
        score += 20
        reasons.append(f"✅ MC forte hausse ({mc_change:+.1f}%): +20")
    elif mc_change > 2:
        score += 15
        reasons.append(f"✅ MC hausse ({mc_change:+.1f}%): +15")
    elif mc_change > 0:
        score += 10
        reasons.append(f"✅ MC positive ({mc_change:+.1f}%): +10")
    elif mc_change > -3:
        score += 0
        reasons.append(f"⚠️ MC légère baisse ({mc_change:+.1f}%): +0")
    else:
        score -= 15
        reasons.append(f"❌ MC forte baisse ({mc_change:+.1f}%): -15")
    
    # BTC Dominance
    btc_dom = crypto_global['btc_dominance']
    if btc_dom > 55:
        score += 5
        reasons.append(f"✅ BTC fort ({btc_dom}%): +5")
    elif btc_dom < 42:
        score += 5
        reasons.append(f"✅ Altseason ({btc_dom}%): +5")
    
    # Momentum des prix
    if prices:
        btc_change = prices.get('btc', {}).get('change_24h', 0)
        if btc_change > 5:
            score += 10
            reasons.append(f"✅ BTC momentum fort ({btc_change:+.1f}%): +10")
        elif btc_change > 2:
            score += 5
            reasons.append(f"✅ BTC momentum ({btc_change:+.1f}%): +5")
        elif btc_change < -5:
            score -= 10
            reasons.append(f"❌ BTC chute ({btc_change:+.1f}%): -10")
    
    # Clamp score
    score = max(0, min(100, score))
    
    print()
    for r in reasons:
        print(f"   {r}")
    
    print(f"\n   {'='*50}")
    print(f"   🏆 SCORE FINAL: {score}/100")
    print(f"   {'='*50}")
    
    # ═══════════════════════════════════════════════════════════════
    # PRÉDICTIONS & RECOMMANDATIONS
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 70)
    print("🔮 PRÉDICTIONS & RECOMMANDATIONS")
    print("─" * 70)
    
    # Déterminer action
    if score >= 90:
        action = "🔥🔥🔥 TRADE AGRESSIF"
        leverage = "5x"
        risk = "3%"
        emoji = "🚀🚀🚀"
    elif score >= 80:
        action = "🔥🔥 TRADE FORT"
        leverage = "3x"
        risk = "2%"
        emoji = "🚀🚀"
    elif score >= 70:
        action = "🔥 TRADE CONFIANT"
        leverage = "2x"
        risk = "1.5%"
        emoji = "🚀"
    elif score >= 60:
        action = "✅ TRADE MODÉRÉ"
        leverage = "1.5x"
        risk = "1%"
        emoji = "📈"
    elif score >= 55:
        action = "⚠️ TRADE PRUDENT"
        leverage = "1x"
        risk = "0.5%"
        emoji = "📊"
    else:
        action = "❌ ATTENDRE"
        leverage = "0x"
        risk = "0%"
        emoji = "🛑"
    
    print(f"\n   {emoji} {action}")
    print(f"\n   📊 Paramètres recommandés:")
    print(f"      ├── Leverage: {leverage}")
    print(f"      ├── Risque par trade: {risk}")
    
    if score >= 55:
        if score >= 80:
            print(f"      ├── Stop Loss: 0.8% (serré avec leverage)")
            print(f"      └── Take Profit: 4-6% (laisser courir)")
        elif score >= 70:
            print(f"      ├── Stop Loss: 1.2%")
            print(f"      └── Take Profit: 3-4%")
        else:
            print(f"      ├── Stop Loss: 2%")
            print(f"      └── Take Profit: 3%")
    
    # Prédictions par crypto
    print("\n   🎯 Prédictions par crypto:")
    
    if prices:
        btc_price = prices['btc']['price']
        eth_price = prices['eth']['price']
        sol_price = prices['sol']['price']
        
        if score >= 70:
            print(f"      ├── BTC: 📈 Potentiel +5-10% → ${btc_price * 1.05:,.0f} - ${btc_price * 1.10:,.0f}")
            print(f"      ├── ETH: 📈 Potentiel +6-12% → ${eth_price * 1.06:,.0f} - ${eth_price * 1.12:,.0f}")
            print(f"      └── SOL: 📈 Potentiel +8-15% → ${sol_price * 1.08:,.0f} - ${sol_price * 1.15:,.0f}")
        elif score >= 55:
            print(f"      ├── BTC: 📊 Range ${btc_price * 0.97:,.0f} - ${btc_price * 1.05:,.0f}")
            print(f"      ├── ETH: 📊 Range ${eth_price * 0.96:,.0f} - ${eth_price * 1.06:,.0f}")
            print(f"      └── SOL: 📊 Range ${sol_price * 0.95:,.0f} - ${sol_price * 1.08:,.0f}")
        else:
            print(f"      ├── BTC: ⚠️ Risque baisse → Support ${btc_price * 0.92:,.0f}")
            print(f"      ├── ETH: ⚠️ Risque baisse → Support ${eth_price * 0.90:,.0f}")
            print(f"      └── SOL: ⚠️ Risque baisse → Support ${sol_price * 0.88:,.0f}")
    
    # ═══════════════════════════════════════════════════════════════
    # RÉSUMÉ FINAL
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ - CE QUE LE BOT VA FAIRE")
    print("=" * 70)
    
    if score >= 70:
        print("""
   🤖 Le bot est en mode ACTIF
   
   ✅ Recherche active d'opportunités
   ✅ Leverage activé ({})
   ✅ Positions plus grosses (risque {}%)
   ✅ Hold plus long si marché reste favorable
   
   📊 Cryptos surveillées: BTC, ETH, SOL
   ⏰ Prochain scan: Dans quelques minutes
        """.format(leverage, risk))
    elif score >= 55:
        print("""
   🤖 Le bot est en mode PRUDENT
   
   ⚠️ Trades sélectifs uniquement
   ⚠️ Pas de leverage
   ⚠️ Positions réduites
   ⚠️ Take profit rapide
   
   📊 Cryptos surveillées: BTC, ETH principalement
   ⏰ Prochain scan: Dans quelques minutes
        """)
    else:
        print("""
   🤖 Le bot est en mode ATTENTE
   
   🛑 Pas de nouveaux trades
   🛑 Protection des positions existantes
   🛑 Attente de meilleures conditions
   
   📊 Surveillance continue du marché
   ⏰ Réévaluation: Toutes les 5 minutes
        """)
    
    print("=" * 70)
    
    return {
        'score': score,
        'action': action,
        'leverage': leverage,
        'fear_greed': fear_greed,
        'market': crypto_global,
        'prices': prices
    }

if __name__ == "__main__":
    result = analyze_and_predict()

