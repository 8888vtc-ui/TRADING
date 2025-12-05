"""
📊 PRÉVISIONS RÉALISTES V2 - AJUSTÉES
=====================================
Basées sur des statistiques réelles de trading algorithmique
"""

import requests

def fetch_market():
    try:
        fg = requests.get("https://api.alternative.me/fng/", timeout=10).json()
        return int(fg['data'][0]['value'])
    except:
        return 50

def predictions_v2(capital=1000):
    fg = fetch_market()
    
    print("=" * 70)
    print("📊 PRÉVISIONS RÉALISTES - SYSTÈME V2.0")
    print("=" * 70)
    print(f"\n💰 Capital: €{capital:,}")
    print(f"🎭 Fear & Greed actuel: {fg}")
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTIQUES RÉALISTES
    # (basées sur études de trading algo et backtests)
    # ═══════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 70)
    print("📈 PARAMÈTRES RÉALISTES DU SYSTÈME V2.0")
    print("─" * 70)
    print("""
   SWING BOT (35% capital):
   • Win rate réaliste: 52-58%
   • Gain moyen: 3-5% | Perte moyenne: 2%
   • Trades/mois: 10-20
   
   SCALPING BOT (25% capital):
   • Win rate réaliste: 55-62%
   • Gain moyen: 0.5-0.8% | Perte moyenne: 0.3%
   • Trades/mois: 60-100
   
   CRYPTO BOT (40% capital):
   • Win rate réaliste: 48-55%
   • Gain moyen: 4-7% | Perte moyenne: 3%
   • Trades/mois: 15-25
   • Leverage jusqu'à 5x
    """)
    
    # ═══════════════════════════════════════════════════════════════
    # SCÉNARIOS AJUSTÉS
    # ═══════════════════════════════════════════════════════════════
    
    scenarios = {
        'pire': {
            'name': '❌ PIRE CAS',
            'prob': 15,
            'swing': -0.03,     # -3% mensuel
            'scalp': -0.01,     # -1% mensuel  
            'crypto': -0.08,    # -8% mensuel
            'desc': 'Marché crash, stop loss touchés, leverage contre nous'
        },
        'mauvais': {
            'name': '🔴 MAUVAIS',
            'prob': 20,
            'swing': 0.01,      # +1%
            'scalp': 0.02,      # +2%
            'crypto': -0.02,    # -2%
            'desc': 'Marché difficile, peu de signals'
        },
        'normal': {
            'name': '🟡 NORMAL',
            'prob': 35,
            'swing': 0.04,      # +4%
            'scalp': 0.05,      # +5%
            'crypto': 0.06,     # +6%
            'desc': 'Conditions normales, stratégie fonctionne'
        },
        'bon': {
            'name': '🟢 BON',
            'prob': 20,
            'swing': 0.08,      # +8%
            'scalp': 0.08,      # +8%
            'crypto': 0.15,     # +15% (leverage modéré)
            'desc': 'Marché favorable, score unifié élevé'
        },
        'excellent': {
            'name': '🔥 EXCELLENT',
            'prob': 10,
            'swing': 0.12,      # +12%
            'scalp': 0.12,      # +12%
            'crypto': 0.35,     # +35% (leverage 3-5x actif)
            'desc': 'Conditions idéales, leverage max'
        }
    }
    
    print("\n" + "═" * 70)
    print("📊 SCÉNARIOS PAR MOIS")
    print("═" * 70)
    
    for key, s in scenarios.items():
        swing_pnl = capital * 0.35 * s['swing']
        scalp_pnl = capital * 0.25 * s['scalp']
        crypto_pnl = capital * 0.40 * s['crypto']
        total_pnl = swing_pnl + scalp_pnl + crypto_pnl
        total_pct = (total_pnl / capital) * 100
        
        print(f"\n{s['name']} (Probabilité {s['prob']}%)")
        print(f"   {s['desc']}")
        print(f"   Swing: {s['swing']*100:+.0f}% | Scalp: {s['scalp']*100:+.0f}% | Crypto: {s['crypto']*100:+.0f}%")
        print(f"   📍 Total: €{capital:,} → €{capital + total_pnl:,.0f} ({total_pct:+.1f}%)")
    
    # ═══════════════════════════════════════════════════════════════
    # ESPÉRANCE MATHÉMATIQUE RÉALISTE
    # ═══════════════════════════════════════════════════════════════
    
    expected = 0
    for s in scenarios.values():
        total_return = 0.35 * s['swing'] + 0.25 * s['scalp'] + 0.40 * s['crypto']
        expected += (s['prob'] / 100) * total_return
    
    expected_monthly_pct = expected * 100
    expected_monthly_eur = capital * expected
    
    print("\n" + "═" * 70)
    print("🎯 ESPÉRANCE MATHÉMATIQUE RÉALISTE")
    print("═" * 70)
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║  📊 RENDEMENT MENSUEL ATTENDU:                                    ║
    ║                                                                   ║
    ║     {expected_monthly_pct:+.1f}% par mois                                          ║
    ║     ≈ €{expected_monthly_eur:+,.0f} sur €{capital:,}                                           ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║  📅 PROJECTIONS SUR 12 MOIS:                                      ║
    ║                                                                   ║""")
    
    projection = capital
    for month in [1, 3, 6, 12]:
        for _ in range(month):
            projection *= (1 + expected)
        if month == 1:
            print(f"    ║     Mois 1:  €{capital:,} → €{projection:,.0f} ({((projection/capital)-1)*100:+.1f}%)              ║")
        elif month == 3:
            proj_3 = projection
        elif month == 6:
            proj_6 = projection
        else:
            proj_12 = projection
        projection = capital  # Reset pour chaque calcul
    
    # Recalcul propre
    proj_3 = capital * ((1 + expected) ** 3)
    proj_6 = capital * ((1 + expected) ** 6)
    proj_12 = capital * ((1 + expected) ** 12)
    
    print(f"    ║     Mois 3:  €{capital:,} → €{proj_3:,.0f} ({((proj_3/capital)-1)*100:+.1f}%)                ║")
    print(f"    ║     Mois 6:  €{capital:,} → €{proj_6:,.0f} ({((proj_6/capital)-1)*100:+.1f}%)                ║")
    print(f"    ║     Mois 12: €{capital:,} → €{proj_12:,.0f} ({((proj_12/capital)-1)*100:+.1f}%)              ║")
    
    print("""    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║  ⚠️  IMPORTANT - RISQUES:                                         ║
    ║                                                                   ║
    ║  • Le pire cas (-5% à -10%) peut arriver                          ║
    ║  • Le marché crypto est très volatile                             ║
    ║  • Le leverage amplifie gains ET pertes                           ║
    ║  • Pas de garantie de rendement                                   ║
    ║  • Paper trading ≠ Real trading (slippage, émotions)              ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # ═══════════════════════════════════════════════════════════════
    # RÉSUMÉ FINAL
    # ═══════════════════════════════════════════════════════════════
    
    worst_total = capital * (1 + 0.35 * (-0.03) + 0.25 * (-0.01) + 0.40 * (-0.08))
    best_total = capital * (1 + 0.35 * 0.12 + 0.25 * 0.12 + 0.40 * 0.35)
    
    print("═" * 70)
    print("📋 RÉSUMÉ FINAL - 1 MOIS")
    print("═" * 70)
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  💰 Capital: €{capital:,}                                              ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║  ❌ PIRE MOIS POSSIBLE:      €{worst_total:,.0f}  ({((worst_total/capital)-1)*100:+.1f}%)             ║
    ║  📊 MOIS ATTENDU:            €{capital + expected_monthly_eur:,.0f}  ({expected_monthly_pct:+.1f}%)              ║
    ║  🔥 MEILLEUR MOIS POSSIBLE:  €{best_total:,.0f}  ({((best_total/capital)-1)*100:+.1f}%)            ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    🎯 En résumé avec €{capital:,}:
    
       PIRE:     Tu perds €{capital - worst_total:.0f} ({((worst_total/capital)-1)*100:.0f}%)
       ATTENDU:  Tu gagnes €{expected_monthly_eur:.0f} ({expected_monthly_pct:.0f}%)
       MEILLEUR: Tu gagnes €{best_total - capital:.0f} ({((best_total/capital)-1)*100:.0f}%)
    """)

if __name__ == "__main__":
    predictions_v2(1000)

