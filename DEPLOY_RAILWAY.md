# 🚀 DÉPLOIEMENT SUR RAILWAY

## Étapes simples (5 minutes)

### 1️⃣ Créer un compte Railway

1. Aller sur https://railway.app
2. Cliquer sur "Login" → "Login with GitHub"
3. Autoriser Railway

---

### 2️⃣ Créer un nouveau projet

1. Cliquer sur "New Project"
2. Choisir "Deploy from GitHub repo"
3. Sélectionner votre repo (ou "Empty Project" pour uploader manuellement)

---

### 3️⃣ Configurer les variables d'environnement

Dans Railway, aller dans **Settings** → **Variables** et ajouter :

```
ALPACA_API_KEY = PKQYJSXQ6NLKKHVUJHA4W3RJI4
ALPACA_SECRET_KEY = AQUJqSXwrvtnpfXHVy7tn7qFSwWSWUUtnZPtRGLhhDw
ALPACA_BASE_URL = https://paper-api.alpaca.markets
```

---

### 4️⃣ Déployer

Si vous avez connecté GitHub :
- Le déploiement est automatique à chaque push

Si vous uploadez manuellement :
- Glisser-déposer les fichiers dans Railway

---

## 📁 Fichiers nécessaires

```
├── bot_trading.py      ✅
├── strategy.py         ✅
├── risk_manager.py     ✅
├── requirements.txt    ✅
├── Procfile            ✅
├── railway.json        ✅
```

---

## ✅ Vérification

Une fois déployé, vous verrez dans les logs :

```
🤖 DÉMARRAGE DU BOT DE TRADING NASDAQ 100
✅ Connexion API réussie
💰 Capital: $100,000.00
🚀 Bot en cours d'exécution...
```

---

## 💰 Coût

- **Plan gratuit** : 500 heures/mois (~21 jours)
- **Plan Hobby** : 5$/mois (24/7 illimité)

---

## ⚠️ Notes importantes

1. **Paper Trading** : Le bot utilise de l'argent fictif
2. **Horaires** : Le bot trade uniquement aux heures optimales
3. **Logs** : Consultez les logs dans Railway pour suivre l'activité

---

## 🔧 Commandes utiles

Redémarrer le bot :
- Railway → Deployments → Redeploy

Voir les logs :
- Railway → Deployments → View Logs

Arrêter le bot :
- Railway → Settings → Remove Service

