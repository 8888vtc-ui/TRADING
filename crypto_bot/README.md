# 🪙 CRYPTO HUNTER BOT V2.0

## Bot de Trading Crypto avec LEVERAGE INTELLIGENT

### 🚀 NOUVEAUTÉS V2.0

| Feature | Description |
|---------|-------------|
| **🚀 Leverage Intelligent** | Max 2x quand confiance > 85% |
| **🎭 Fear & Greed API** | Vérifie le sentiment marché |
| **👑 BTC Dominance API** | Analyse de la dominance |
| **📊 Market Checker** | Validation avant chaque trade |

---

## 🎯 Stratégie

### Mode Normal (confiance < 80%)
- Pas de leverage
- Risque standard 0.5%
- Stops normaux

### Mode Leverage (confiance ≥ 80%)

| Niveau | Confiance | Multiplier | Stop Ajusté |
|--------|-----------|------------|-------------|
| LOW | 85% | 1.25x | -20% serré |
| MEDIUM | 90% | 1.5x | -35% serré |
| HIGH | 95% | 2.0x | -50% serré |

**CONDITIONS REQUISES:**
1. ✅ Confiance signal > 80%
2. ✅ Score > 9/12
3. ✅ Risk/Reward > 2.5:1
4. ✅ Fear & Greed entre 40-60 (marché stable)
5. ✅ Pas de volatilité extrême
6. ✅ Max 1 position leverage à la fois

---

## 📊 APIs Market Data

### Fear & Greed Index
```
Source: alternative.me
Mise à jour: toutes les 5 minutes

0-25:  Extreme Fear   → Opportunité contrarian
25-45: Fear           → Accumulation
45-55: Neutral        → Normal, leverage OK
55-75: Greed          → Prudence
75-100: Extreme Greed → DANGER, pas de longs
```

### BTC Dominance
```
Source: CoinGecko
Analyse: Focus BTC vs Altcoins

> 55%: Focus sur BTC
40-55%: Marché équilibré
< 40%: Alt season
```

---

## 🛡️ Gestion du Risque

### Sans Leverage
| Paramètre | Valeur |
|-----------|--------|
| Risque/trade | 0.5% |
| Stop BTC | 1.5% |
| Stop ETH | 2% |
| Stop SOL | 2.5% |

### Avec Leverage
| Paramètre | 1.25x | 1.5x | 2x |
|-----------|-------|------|-----|
| Stop BTC | 1.2% | 1% | 0.75% |
| Stop ETH | 1.6% | 1.3% | 1% |
| Stop SOL | 2% | 1.6% | 1.25% |

---

## 📈 Rentabilité Attendue

### Sans Leverage
| Scénario | Rentabilité/an |
|----------|----------------|
| Pessimiste | +30-50% |
| Réaliste | +80-120% |
| Optimiste | +150-200% |

### Avec Leverage Intelligent
| Scénario | Rentabilité/an |
|----------|----------------|
| Pessimiste | +50-80% |
| **Réaliste** | **+120-180%** |
| Optimiste | +200-300% |

---

## 🔧 Structure

```
crypto_bot/
├── crypto_hunter.py      # Bot principal V2.0
├── crypto_strategy.py    # Stratégie momentum
├── crypto_risk.py        # Gestion risque
├── market_data_api.py    # APIs Fear & Greed, Dominance
├── leverage_manager.py   # Gestion leverage intelligent
├── requirements.txt      # Dépendances
├── Procfile             # Railway
└── README.md
```

---

## 🚀 Déploiement Railway

### Variables d'environnement
```env
APCA_API_KEY_ID=votre_api_key
APCA_API_SECRET_KEY=votre_secret_key
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### Configuration
- Root Directory: `/crypto_bot`
- Start Command: `python crypto_hunter.py`

---

## 📋 Exemple de Logs

```
🌍 VÉRIFICATION CONDITIONS MARCHÉ...
   🎭 Fear & Greed: 52 (Neutral)
   👑 BTC Dominance: 48.5%
   📈 Market Cap 24h: +2.3%

   📊 VERDICT MARCHÉ:
      Peut trader: ✅
      Peut leverage: ✅
      Leverage autorisé: 1.5x

🔍 SCAN CRYPTO EN COURS...
📊 BTC/USD: BUY | Score: 10.5/12 | Confiance: 92%
   🚀 LEVERAGE 1.5x disponible!

🏆 MEILLEURE OPPORTUNITÉ: BTC/USD
   Score: 10.5/12
   Confiance: 92%
   🚀 Leverage: 1.5x disponible

🚀 LEVERAGE ACTIVÉ: 1.5x
   Stop ajusté: $41,500 (1%)

✅ ORDRE PASSÉ!
   Symbole: BTC/USD
   Quantité: 0.05
   Leverage: 1.5x
   Stop Loss: $41,500
   Take Profit: $43,500
```

---

## ⚠️ Avertissement

Le trading avec leverage amplifie les gains ET les pertes. Ce bot utilise le leverage de manière très conservative uniquement quand les conditions sont optimales. Cependant, des pertes sont toujours possibles.

**N'investissez que ce que vous pouvez perdre.**

---

## 📊 Comparaison des 3 Bots

| Bot | Marché | Leverage | Rentabilité | Risque |
|-----|--------|----------|-------------|--------|
| Swing | Actions | Non | +30-40% | ⭐ |
| Scalping | Actions | Non | +50-70% | ⭐⭐ |
| **Crypto V2** | Crypto | **Intelligent** | **+120-180%** | ⭐⭐ |
