"""
💰 PROJECTION 1 AN AVEC €1,000
"""

capital = 1000

print("=" * 70)
print("💰 PROJECTION 1 AN AVEC 1,000 EUR - SYSTEME V2.0")
print("=" * 70)

# Scénarios mensuels réalistes
scenarios = {
    'PIRE': {'prob': 0.10, 'return': -0.05},
    'MAUVAIS': {'prob': 0.15, 'return': 0.00},
    'MOYEN': {'prob': 0.35, 'return': 0.05},
    'BON': {'prob': 0.25, 'return': 0.10},
    'EXCELLENT': {'prob': 0.15, 'return': 0.20},
}

expected_monthly = sum(s['prob'] * s['return'] for s in scenarios.values())

print("""
PARAMETRES DU SYSTEME:
   - 3 bots en parallele (Swing, Scalping, Crypto)
   - Capital Protector active (-1% max/trade)
   - Leverage jusqu a 5x sur opportunites fortes
   - Score unifie V2.0 pour decisions
""")

print("=" * 70)
print("SCENARIOS MENSUELS:")
print("=" * 70)
for name, s in scenarios.items():
    emoji = '[-]' if s['return'] < 0 else '[=]' if s['return'] == 0 else '[+]' if s['return'] < 0.15 else '[!]'
    print(f"   {emoji} {name:12} ({s['prob']*100:.0f}%): {s['return']*100:+.0f}%")

print(f"\n   Esperance mensuelle: {expected_monthly*100:+.1f}%\n")

# PROJECTION CONSERVATRICE
print("=" * 70)
print("PROJECTION CONSERVATRICE (Esperance mathematique)")
print("=" * 70)

proj = capital
for month in range(1, 13):
    proj *= (1 + expected_monthly)
    if month in [1, 3, 6, 12]:
        gain = proj - capital
        pct = (proj/capital - 1) * 100
        print(f"   Mois {month:2}: {capital} EUR -> {proj:,.0f} EUR  (Gain: {gain:+,.0f} EUR | {pct:+.1f}%)")

print(f"\n   APRES 1 AN: {proj:,.0f} EUR\n")

# PROJECTION MEILLEUR CAS
print("=" * 70)
print("MEILLEUR CAS (Que des mois BON/EXCELLENT)")
print("=" * 70)

proj_best = capital
for month in range(1, 13):
    monthly = 0.15 if month % 3 == 0 else 0.10
    proj_best *= (1 + monthly)
    if month in [3, 6, 9, 12]:
        gain = proj_best - capital
        pct = (proj_best/capital - 1) * 100
        print(f"   Mois {month:2}: {capital} EUR -> {proj_best:,.0f} EUR  (Gain: {gain:+,.0f} EUR | {pct:+.1f}%)")

print(f"\n   MEILLEUR CAS 1 AN: {proj_best:,.0f} EUR\n")

# PROJECTION ULTRA-OPTIMISTE
print("=" * 70)
print("AU MIEUX ABSOLU (Leverage 5x + marche bull constant)")
print("=" * 70)

proj_ultra = capital
for month in range(1, 13):
    proj_ultra *= 1.20
    if month in [3, 6, 9, 12]:
        gain = proj_ultra - capital
        pct = (proj_ultra/capital - 1) * 100
        print(f"   Mois {month:2}: {capital} EUR -> {proj_ultra:,.0f} EUR  (Gain: {gain:+,.0f} EUR | {pct:+.1f}%)")

print(f"\n   AU MIEUX ABSOLU 1 AN: {proj_ultra:,.0f} EUR\n")

# RÉSUMÉ
print("=" * 70)
print("RESUME - AVEC 1,000 EUR EN 1 AN:")
print("=" * 70)
print(f"""
+=====================================================================+
|                                                                     |
|  CAPITAL INITIAL: 1,000 EUR                                         |
|                                                                     |
+=====================================================================+
|                                                                     |
|  CONSERVATEUR (realiste):                                           |
|     1,000 EUR -> {proj:,.0f} EUR                                        |
|     Gain: {proj-capital:+,.0f} EUR                                              |
|     Rendement: {(proj/capital-1)*100:+.0f}%                                              |
|                                                                     |
|  MEILLEUR CAS (marche favorable):                                   |
|     1,000 EUR -> {proj_best:,.0f} EUR                                       |
|     Gain: {proj_best-capital:+,.0f} EUR                                             |
|     Rendement: {(proj_best/capital-1)*100:+.0f}%                                             |
|                                                                     |
|  AU MIEUX ABSOLU (leverage max + bull run):                         |
|     1,000 EUR -> {proj_ultra:,.0f} EUR                                      |
|     Gain: {proj_ultra-capital:+,.0f} EUR                                            |
|     Rendement: {(proj_ultra/capital-1)*100:+.0f}%                                            |
|                                                                     |
+=====================================================================+

ATTENTION: Le "meilleur cas" et "au mieux absolu" necessitent:
    - Un marche constamment favorable
    - Des decisions parfaites
    - Pas de crash ni de black swan
    - Beaucoup de chance!

OBJECTIF REALISTE: 1,500 a 2,500 EUR en 1 an
   C est deja TRES BIEN: +50% a +150%!
""")

