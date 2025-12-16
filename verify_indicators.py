
import pandas as pd
import numpy as np
import logging
from scalping_bot.scalping_strategy import ScalpingStrategy
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_indicators():
    print("🔍 VERIFICATION DES INDICATEURS")
    print("=============================")

    # 1. Créer des données de test contrôlées
    # Tendance haussière parfaite pour tester les EMAs et RSI
    prices = [100 + i + (i*0.1) for i in range(100)] # Prix qui montent : 100, 101.1, 102.2...
    df = pd.DataFrame({
        'close': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'volume': [1000 for _ in range(100)]
    })
    
    # 2. Calculer avec la stratégie du bot
    strategy = ScalpingStrategy()
    df_bot = strategy.calculate_indicators(df)
    
    # 3. Calculer manuellement (Source de vérité)
    rsi_ref = RSIIndicator(pd.Series(prices), window=7).rsi().iloc[-1]
    ema_9_ref = EMAIndicator(pd.Series(prices), window=9).ema_indicator().iloc[-1]
    
    # 4. Comparer
    bot_rsi = df_bot['rsi'].iloc[-1]
    bot_ema_9 = df_bot['ema_9'].iloc[-1]
    
    print(f"\n🧪 TEST 1: Précision RSI (Période 7)")
    print(f"   Référence (Library): {rsi_ref:.4f}")
    print(f"   Bot:                 {bot_rsi:.4f}")
    diff_rsi = abs(rsi_ref - bot_rsi)
    if diff_rsi < 0.001:
        print("   ✅ RSI CORRECT")
    else:
        print(f"   ❌ ERREUR RSI: Diff {diff_rsi:.4f}")

    print(f"\n🧪 TEST 2: Précision EMA 9")
    print(f"   Référence (Library): {ema_9_ref:.4f}")
    print(f"   Bot:                 {bot_ema_9:.4f}")
    diff_ema = abs(ema_9_ref - bot_ema_9)
    if diff_ema < 0.001:
        print("   ✅ EMA CORRECT")
    else:
        print(f"   ❌ ERREUR EMA: Diff {diff_ema:.4f}")

    # 5. Test VWAP (Calcul manuel vs Bot)
    # VWAP = Cumulative(Volume * Price) / Cumulative(Volume)
    # Ici Prix monte, Volume constant 1000
    # Donc VWAP devrait être la moyenne simple des prix pondérée
    vol = pd.Series([1000] * 100)
    price_series = pd.Series(prices)
    vwap_ref = (price_series * vol).cumsum() / vol.cumsum()
    vwap_ref_val = vwap_ref.iloc[-1]
    
    bot_vwap = df_bot['vwap'].iloc[-1]
    
    print(f"\n🧪 TEST 3: Précision VWAP")
    print(f"   Calcul Manuel: {vwap_ref_val:.4f}")
    print(f"   Bot:           {bot_vwap:.4f}")
    
    # Le bot utilise (High+Low+Close)/3 pour le prix typique, pas juste Close
    # Recalcul manuel avec prix typique
    tp = (df['high'] + df['low'] + df['close']) / 3
    vwap_tp_ref = (tp * vol).cumsum() / vol.cumsum()
    vwap_tp_val = vwap_tp_ref.iloc[-1]
    
    print(f"   Calcul Manuel (Typical Price): {vwap_tp_val:.4f}")
    
    diff_vwap = abs(vwap_tp_val - bot_vwap)
    if diff_vwap < 0.001:
        print("   ✅ VWAP CORRECT (Basé sur Typical Price)")
    else:
        print(f"   ❌ ERREUR VWAP: Diff {diff_vwap:.4f}")

if __name__ == "__main__":
    verify_indicators()
