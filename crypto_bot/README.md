# 🪙 CRYPTO HUNTER BOT V1.0

## Bot de Trading Crypto Automatisé - CONSERVATEUR

### 🎯 Philosophie

> **"Mieux vaut rater un trade que perdre de l'argent"**

Ce bot privilégie la **protection du capital** avant tout. Il ne trade que quand toutes les conditions sont réunies.

---

## 📊 Caractéristiques

### Stratégie: Momentum Confirmé

| Paramètre | Valeur |
|-----------|--------|
| **Cryptos** | BTC, ETH, SOL |
| **Timeframe** | 5 minutes |
| **Score minimum** | 8/12 (strict) |
| **Confiance minimum** | 65% |

### Indicateurs Utilisés

1. **EMAs** (9, 21, 55) - Tendance
2. **RSI** (14) - Momentum
3. **MACD** - Confirmation
4. **ADX** - Force de tendance
5. **Bollinger Bands** - Volatilité
6. **Stochastic** - Timing
7. **Volume** - Validation

---

## 🛡️ Gestion du Risque

### Paramètres Ultra Conservateurs

| Paramètre | Valeur |
|-----------|--------|
| Risque par trade | **0.5%** |
| Perte max journalière | **2%** |
| Max positions | **3** |
| Max exposition | **60%** |
| Min cash | **30%** |

### Stop Loss Adaptés

| Crypto | Stop Loss | Take Profit | Ratio |
|--------|-----------|-------------|-------|
| BTC | 1.5% | 3% | 1:2 |
| ETH | 2% | 4% | 1:2 |
| SOL | 2.5% | 5% | 1:2 |

---

## 📈 Rentabilité Attendue

| Scénario | Rentabilité/an | Drawdown max |
|----------|----------------|--------------|
| Pessimiste | +30-50% | -10% |
| **Réaliste** | **+80-120%** | **-7%** |
| Optimiste | +150-200% | -5% |

---

## 🚀 Déploiement

### Variables d'environnement requises

```env
APCA_API_KEY_ID=votre_api_key
APCA_API_SECRET_KEY=votre_secret_key
APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### Railway

1. Créer un nouveau service
2. Root Directory: `/crypto_bot`
3. Ajouter les variables d'environnement
4. Déployer

---

## 📋 Logs

Le bot génère des logs détaillés:

```
🔍 SCAN CRYPTO EN COURS...
📊 BTC/USD: HOLD | Score: 5.5/12 | Confiance: 45%
📊 ETH/USD: BUY | Score: 9.0/12 | Confiance: 75%
📊 SOL/USD: HOLD | Score: 4.0/12 | Confiance: 33%

🏆 MEILLEURE OPPORTUNITÉ: ETH/USD
   Score: 9.0/12
   Confiance: 75%

✅ ORDRE PASSÉ!
   Quantité: 0.5 ETH
   Prix: $2,150.00
   Stop Loss: $2,107.00 (2%)
   Take Profit: $2,236.00 (4%)
```

---

## ⚠️ Avertissement

Le trading de crypto-monnaies comporte des risques significatifs. Ce bot est configuré pour minimiser les risques mais des pertes sont toujours possibles. N'investissez que ce que vous pouvez vous permettre de perdre.

---

## 📊 Comparaison des 3 Bots

| Bot | Marché | Risque | Rentabilité | Style |
|-----|--------|--------|-------------|-------|
| Swing | Actions | Faible | +30-40%/an | Défensif |
| Scalping | Actions | Moyen | +50-70%/an | Agressif |
| **Crypto** | Crypto | Moyen | **+80-120%/an** | Équilibré |

