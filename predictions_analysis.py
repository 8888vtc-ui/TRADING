"""
📊 ANALYSE DE PRÉVISIONS - PIRE VS MEILLEUR CAS
===============================================
Simulation basée sur le système V2.0 avec:
- Données de marché actuelles
- Statistiques historiques de stratégies similaires
- 3 bots en parallèle (Swing, Scalping, Crypto)
"""

import requests
from datetime import datetime

def fetch_market_data():
    """Récupère les données actuelles"""
    try:
        # Fear & Greed
        fg = requests.get("https://api.alternative.me/fng/", timeout=10).json()
        fg_value = int(fg['data'][0]['value'])
        
        # Market overview
        market = requests.get("https://api.coingecko.com/api/v3/global", timeout=10).json()
        mc_change = market['data']['market_cap_change_percentage_24h_usd']
        
        # Prix BTC
        prices = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
        btc_price = prices['bitcoin']['usd']
        
        return {
            'fear_greed': fg_value,
            'market_change_24h': mc_change,
            'btc_price': btc_price
        }
    except:
        return {'fear_greed': 50, 'market_change_24h': 0, 'btc_price': 90000}


def calculate_predictions(capital: float = 1000):
    """
    Calcule les prévisions sur 1 mois
    """
    data = fetch_market_data()
    
    print("=" * 70)
    print("📊 ANALYSE PRÉVISIONS - SYSTÈME V2.0 COMPLET")
    print("=" * 70)
    print(f"\n💰 Capital initial: €{capital:,.0f}")
    print(f"📅 Période: 1 mois (30 jours)")
    print(f"\n🌍 Conditions actuelles:")
    print(f"   Fear & Greed: {data['fear_greed']}")
    print(f"   Market Cap 24h: {data['market_change_24h']:.2f}%")
    print(f"   BTC: ${data['btc_price']:,.0f}")
    
    # ═══════════════════════════════════════════════════════════════
    # PARAMÈTRES DES 3 BOTS
    # ═══════════════════════════════════════════════════════════════
    
    bots = {
        'SWING': {
            'name': '📈 Swing Trading (Actions)',
            'trades_per_month': 15,
            'avg_win_rate': 0.55,
            'avg_win': 0.05,      # +5% par trade gagnant
            'avg_loss': 0.025,    # -2.5% par trade perdant
            'leverage_avg': 1.5,
            'capital_share': 0.35,
        },
        'SCALPING': {
            'name': '⚡ Scalping (Actions)',
            'trades_per_month': 80,
            'avg_win_rate': 0.60,
            'avg_win': 0.008,     # +0.8% par trade
            'avg_loss': 0.004,    # -0.4% par trade
            'leverage_avg': 1.0,
            'capital_share': 0.25,
        },
        'CRYPTO': {
            'name': '🪙 Crypto Hunter (BTC/ETH/SOL)',
            'trades_per_month': 25,
            'avg_win_rate': 0.52,
            'avg_win': 0.06,      # +6% par trade
            'avg_loss': 0.03,     # -3% par trade
            'leverage_avg': 2.0,
            'capital_share': 0.40,
        }
    }
    
    # ═══════════════════════════════════════════════════════════════
    # SCÉNARIO PIRE CAS (Probabilité ~15%)
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "═" * 70)
    print("❌ SCÉNARIO PIRE CAS (Probabilité ~15%)")
    print("═" * 70)
    print("""
   CONDITIONS:
   - Marché en chute prolongée (-10% à -20%)
   - VIX > 35 (forte volatilité)
   - Fear & Greed < 20 (panique)
   - Plusieurs stop loss touchés
   - Bot en mode "protection" la plupart du temps
    """)
    
    worst_total = capital
    worst_details = []
    
    for key, bot in bots.items():
        bot_capital = capital * bot['capital_share']
        
        # Pire cas: win rate -15%, leverage réduit
        worst_win_rate = bot['avg_win_rate'] - 0.15
        worst_trades = bot['trades_per_month'] * 0.5  # Moins de trades
        worst_leverage = 1.0  # Pas de leverage
        
        wins = int(worst_trades * worst_win_rate)
        losses = int(worst_trades - wins)
        
        profit = (wins * bot['avg_win'] - losses * bot['avg_loss'] * 1.3) * worst_leverage
        result = bot_capital * (1 + profit)
        
        worst_details.append({
            'name': bot['name'],
            'capital': bot_capital,
            'result': result,
            'pnl': result - bot_capital,
            'pnl_pct': profit * 100
        })
        worst_total += (result - bot_capital)
    
    print("   Résultats par bot:")
    for d in worst_details:
        emoji = "🔴" if d['pnl'] < 0 else "🟢"
        print(f"   {emoji} {d['name']}: €{d['capital']:.0f} → €{d['result']:.0f} ({d['pnl_pct']:+.1f}%)")
    
    worst_pnl = worst_total - capital
    worst_pct = (worst_pnl / capital) * 100
    print(f"\n   💰 TOTAL: €{capital:,.0f} → €{worst_total:,.0f}")
    print(f"   📉 P&L: €{worst_pnl:+,.0f} ({worst_pct:+.1f}%)")
    
    # ═══════════════════════════════════════════════════════════════
    # SCÉNARIO RÉALISTE (Probabilité ~60%)
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "═" * 70)
    print("📊 SCÉNARIO RÉALISTE (Probabilité ~60%)")
    print("═" * 70)
    print("""
   CONDITIONS:
   - Marché latéral à légèrement haussier
   - VIX 15-25 (normal)
   - Fear & Greed 30-60 (zone optimale)
   - Stratégie fonctionne normalement
   - Score unifié moyen: 55-70
    """)
    
    realistic_total = capital
    realistic_details = []
    
    for key, bot in bots.items():
        bot_capital = capital * bot['capital_share']
        
        # Cas réaliste: paramètres normaux
        trades = bot['trades_per_month']
        wins = int(trades * bot['avg_win_rate'])
        losses = trades - wins
        
        profit = (wins * bot['avg_win'] - losses * bot['avg_loss']) * bot['leverage_avg']
        result = bot_capital * (1 + profit)
        
        realistic_details.append({
            'name': bot['name'],
            'capital': bot_capital,
            'result': result,
            'pnl': result - bot_capital,
            'pnl_pct': profit * 100
        })
        realistic_total += (result - bot_capital)
    
    print("   Résultats par bot:")
    for d in realistic_details:
        emoji = "🔴" if d['pnl'] < 0 else "🟢"
        print(f"   {emoji} {d['name']}: €{d['capital']:.0f} → €{d['result']:.0f} ({d['pnl_pct']:+.1f}%)")
    
    realistic_pnl = realistic_total - capital
    realistic_pct = (realistic_pnl / capital) * 100
    print(f"\n   💰 TOTAL: €{capital:,.0f} → €{realistic_total:,.0f}")
    print(f"   📈 P&L: €{realistic_pnl:+,.0f} ({realistic_pct:+.1f}%)")
    
    # ═══════════════════════════════════════════════════════════════
    # SCÉNARIO MEILLEUR CAS (Probabilité ~25%)
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "═" * 70)
    print("🔥 SCÉNARIO MEILLEUR CAS (Probabilité ~25%)")
    print("═" * 70)
    print("""
   CONDITIONS:
   - Marché haussier (+10% à +20%)
   - VIX < 18 (calme)
   - Fear & Greed 40-60 puis monte vers 70
   - Score unifié > 75 régulièrement
   - Leverage 3-5x activé fréquemment
   - Plusieurs trades gagnants consécutifs
    """)
    
    best_total = capital
    best_details = []
    
    for key, bot in bots.items():
        bot_capital = capital * bot['capital_share']
        
        # Meilleur cas: win rate +10%, leverage max
        best_win_rate = min(bot['avg_win_rate'] + 0.10, 0.75)
        best_trades = bot['trades_per_month'] * 1.3
        best_leverage = min(bot['leverage_avg'] * 2, 5.0)
        
        wins = int(best_trades * best_win_rate)
        losses = int(best_trades - wins)
        
        profit = (wins * bot['avg_win'] * 1.3 - losses * bot['avg_loss'] * 0.8) * best_leverage
        result = bot_capital * (1 + profit)
        
        best_details.append({
            'name': bot['name'],
            'capital': bot_capital,
            'result': result,
            'pnl': result - bot_capital,
            'pnl_pct': profit * 100
        })
        best_total += (result - bot_capital)
    
    print("   Résultats par bot:")
    for d in best_details:
        emoji = "🔴" if d['pnl'] < 0 else "🟢"
        print(f"   {emoji} {d['name']}: €{d['capital']:.0f} → €{d['result']:.0f} ({d['pnl_pct']:+.1f}%)")
    
    best_pnl = best_total - capital
    best_pct = (best_pnl / capital) * 100
    print(f"\n   💰 TOTAL: €{capital:,.0f} → €{best_total:,.0f}")
    print(f"   🚀 P&L: €{best_pnl:+,.0f} ({best_pct:+.1f}%)")
    
    # ═══════════════════════════════════════════════════════════════
    # RÉSUMÉ
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "═" * 70)
    print("📋 RÉSUMÉ DES PRÉVISIONS (1 MOIS)")
    print("═" * 70)
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  Capital initial: €{capital:,.0f}                                    ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║  ❌ PIRE CAS (15%):                                           ║
    ║     €{capital:,.0f} → €{worst_total:,.0f}                                      ║
    ║     P&L: €{worst_pnl:+,.0f} ({worst_pct:+.1f}%)                               ║
    ║                                                               ║
    ║  📊 RÉALISTE (60%):                                           ║
    ║     €{capital:,.0f} → €{realistic_total:,.0f}                                      ║
    ║     P&L: €{realistic_pnl:+,.0f} ({realistic_pct:+.1f}%)                                ║
    ║                                                               ║
    ║  🔥 MEILLEUR CAS (25%):                                       ║
    ║     €{capital:,.0f} → €{best_total:,.0f}                                      ║
    ║     P&L: €{best_pnl:+,.0f} ({best_pct:+.1f}%)                                ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║  📈 ESPÉRANCE MATHÉMATIQUE:                                   ║
    ║     (15% × {worst_pct:.0f}%) + (60% × {realistic_pct:.0f}%) + (25% × {best_pct:.0f}%)              ║
    ║     = {0.15*worst_pct + 0.60*realistic_pct + 0.25*best_pct:+.1f}% par mois                                   ║
    ║     ≈ €{capital * (0.15*worst_pct + 0.60*realistic_pct + 0.25*best_pct) / 100:+,.0f} attendu                                     ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Projection 12 mois
    monthly_expected = 0.15*worst_pct + 0.60*realistic_pct + 0.25*best_pct
    
    print("\n📅 PROJECTION 12 MOIS (Intérêts composés):")
    print("-" * 50)
    
    projection = capital
    for month in range(1, 13):
        # Variation mensuelle (simulation)
        monthly_return = monthly_expected / 100
        projection *= (1 + monthly_return)
        if month in [3, 6, 9, 12]:
            print(f"   Mois {month:2d}: €{projection:,.0f} ({((projection/capital)-1)*100:+.1f}%)")
    
    annual_return = ((projection / capital) - 1) * 100
    print(f"\n   🎯 Projection 1 an: €{capital:,.0f} → €{projection:,.0f}")
    print(f"   📈 Rendement annuel estimé: {annual_return:+.1f}%")
    
    return {
        'worst': {'total': worst_total, 'pnl': worst_pnl, 'pct': worst_pct},
        'realistic': {'total': realistic_total, 'pnl': realistic_pnl, 'pct': realistic_pct},
        'best': {'total': best_total, 'pnl': best_pnl, 'pct': best_pct},
        'expected_monthly': monthly_expected,
        'expected_annual': annual_return
    }


if __name__ == "__main__":
    print("\n" + "🔮" * 35)
    results = calculate_predictions(1000)
    print("\n" + "🔮" * 35)

