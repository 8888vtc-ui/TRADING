# 🔥 BOT DE SCALPING NASDAQ ULTRA-OPTIMISÉ

## 📊 Comparaison avec le Bot Swing Trading

| Caractéristique | Bot Swing (Original) | Bot Scalping |
|-----------------|---------------------|--------------|
| **Stratégie** | Long uniquement | Long uniquement |
| **Timeframe** | 5-15 min | 1 min |
| **Durée trades** | Heures/Jours | Minutes |
| **Trades/jour** | 1-5 | 10-20 |
| **Stop Loss** | 3% | 0.4% |
| **Take Profit** | 6% | 0.8% |
| **Win Rate cible** | 55-60% | 65-70% |
| **Indicateurs** | RSI, MACD, BB | 7 indicateurs |
| **Scan** | 5 min | 60 sec |

## 🎯 Stratégie "Confluence Scalping"

### Indicateurs utilisés (7)
1. **EMA 5/9/21** - Tendance multi-timeframe
2. **RSI (7)** - Momentum rapide
3. **VWAP** - Prix institutionnel
4. **Bollinger Bands (20,2)** - Volatilité
5. **Stochastic (14,3,3)** - Confirmation
6. **ADX (14)** - Force de tendance
7. **MACD** - Momentum

### Règles d'entrée (Score /12)
- Prix > VWAP (+2)
- EMAs alignées (+2)
- Pente EMA positive (+1)
- RSI zone favorable (+2)
- Stochastic croisement (+1)
- Bollinger position (+1)
- Volume spike (+1)
- ADX tendance forte (+1)
- MACD positif (+1)

**Signal d'achat si score ≥ 7/12 (60%+)**

## ⚡ Horaires de Trading

| Session | Heure NY | Heure Paris | Qualité |
|---------|----------|-------------|---------|
| **Ouverture** | 09:35-11:30 | 15:35-17:30 | ⭐⭐⭐⭐⭐ |
| **Power Hour** | 15:00-15:55 | 21:00-21:55 | ⭐⭐⭐⭐⭐ |

## 🛡️ Gestion du Risque

- **Risque/trade**: 0.5% max
- **Perte journalière max**: -2%
- **Profit journalier cible**: +5%
- **Max trades/jour**: 20
- **Max pertes consécutives**: 5 (stop trading)
- **Max positions simultanées**: 3

## 📈 Symboles Tradés

Haute volatilité pour scalping:
- TSLA, NVDA, AMD (très volatiles)
- QQQ, SPY (très liquides)
- META, AAPL, MSFT

## 🚀 Déploiement Railway

### 1. Créer nouveau projet Railway
```bash
cd scalping_bot
git init
git add .
git commit -m "Initial scalping bot"
git remote add origin <VOTRE_REPO>
git push -u origin main
```

### 2. Variables d'environnement Railway
```
ALPACA_API_KEY = <votre_key>
ALPACA_SECRET_KEY = <votre_secret>
ALPACA_BASE_URL = https://paper-api.alpaca.markets
```

### 3. Déployer
Connecter le repo GitHub à Railway

## 📊 Objectifs du Test (1 mois)

### Bot Swing (Original)
- Win Rate: 55-60%
- Profit mensuel cible: +10-15%
- Max drawdown: -5%

### Bot Scalping (Nouveau)
- Win Rate: 65-70%
- Profit mensuel cible: +15-25%
- Max drawdown: -5%

## ⚠️ Avertissement

Ce bot est en mode **Paper Trading** (argent virtuel).
Ne jamais trader avec de l'argent réel sans tests approfondis.

---
Créé le: Décembre 2024
Version: 2.0

