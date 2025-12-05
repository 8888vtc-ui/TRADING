# 🔐 Configuration des Clés API Alpaca

## ⚠️ SÉCURITÉ IMPORTANTE

**NE JAMAIS PARTAGER OU COMMITER VOS CLÉS API !**

## 📋 Fichiers de Configuration

- `alpaca_api_keys.env` - Contient vos clés API (NE PAS COMMITER)

## 🔑 Utilisation dans le Code

### Méthode 1 : Variables d'environnement

```python
import os
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env
load_dotenv('alpaca_api_keys.env')

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
```

### Méthode 2 : Variables d'environnement système

**Windows PowerShell :**
```powershell
$env:ALPACA_API_KEY = "617407d8-f99a-471e-ae4b-df3fb39607b3"
$env:ALPACA_SECRET_KEY = "votre_secret_key"
$env:ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

## ✅ Vérification

Pour tester votre configuration :

```python
import os
from alpaca_trade_api import REST

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')

api = REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
account = api.get_account()
print(f"✅ Connexion réussie ! Cash: ${float(account.cash):,.2f}")
```

## 📝 Notes

- Mode actuel : **Paper Trading** (argent fictif)
- Base URL Paper : `https://paper-api.alpaca.markets`
- Base URL Live : `https://api.alpaca.markets` (quand vous serez prêt)

