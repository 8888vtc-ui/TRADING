"""
Script pour configurer directement les variables d'environnement sur Railway
Utilise l'ID du service directement
"""
import requests
import json

# Configuration
RAILWAY_TOKEN = "c5d27e96-a521-43fa-8014-ed1079cc12c4"
SERVICE_ID = "c0298d41-6636-40f0-b649-018adb9ec29b"
RAILWAY_API_URL = "https://backboard.railway.app/graphql/v1"

# Variables à configurer
VARIABLES = {
    "ALPACA_API_KEY": "PKQYJSXQ6NLKKHVUJHA4W3RJI4",
    "ALPACA_SECRET_KEY": "AQUJqSXwrvtnpfXHVy7tn7qFSwWSWUUtnZPtRGLhhDw",
    "ALPACA_BASE_URL": "https://paper-api.alpaca.markets"
}

def get_headers():
    """Retourne les headers pour l'API Railway"""
    return {
        "Authorization": f"Bearer {RAILWAY_TOKEN}",
        "Content-Type": "application/json"
    }

def set_variables(service_id, variables):
    """Définit les variables d'environnement pour un service"""
    mutation = """
    mutation($serviceId: String!, $variables: [VariableInput!]!) {
        variablesSet(serviceId: $serviceId, variables: $variables) {
            id
        }
    }
    """
    
    # Convertir le dictionnaire en format VariableInput
    variables_input = [{"key": k, "value": v} for k, v in variables.items()]
    
    try:
        response = requests.post(
            RAILWAY_API_URL,
            headers=get_headers(),
            json={
                "query": mutation,
                "variables": {
                    "serviceId": service_id,
                    "variables": variables_input
                }
            }
        )
        
        print(f"📡 Statut HTTP: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.text}")
            return False
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Erreurs GraphQL: {json.dumps(data['errors'], indent=2)}")
            return False
        
        if 'data' in data and data['data']:
            return True
        
        print(f"⚠️ Réponse inattendue: {json.dumps(data, indent=2)}")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 CONFIGURATION DES VARIABLES RAILWAY")
    print("=" * 60)
    print()
    print(f"📦 Service ID: {SERVICE_ID}")
    print()
    
    # Afficher les variables à configurer
    print("📋 Variables à configurer:")
    for key, value in VARIABLES.items():
        # Masquer partiellement la secret key
        if 'SECRET' in key:
            display_value = value[:10] + "..." + value[-5:]
        else:
            display_value = value
        print(f"   • {key} = {display_value}")
    print()
    
    # Configurer les variables
    print("🔧 Configuration en cours...")
    print()
    
    if set_variables(SERVICE_ID, VARIABLES):
        print("=" * 60)
        print("✅ TOUTES LES VARIABLES ONT ÉTÉ CONFIGURÉES !")
        print("=" * 60)
        print()
        print("📋 Variables configurées avec succès:")
        for key in VARIABLES.keys():
            print(f"   ✅ {key}")
        print()
        print("💡 Railway redéploiera automatiquement avec les nouvelles variables")
        print("   Vérifiez les logs dans Railway pour confirmer le déploiement")
    else:
        print()
        print("=" * 60)
        print("❌ ERREUR LORS DE LA CONFIGURATION")
        print("=" * 60)
        print()
        print("💡 Solutions possibles:")
        print("   1. Vérifiez que le Service ID est correct")
        print("   2. Vérifiez que le token Railway est valide")
        print("   3. Configurez manuellement dans Railway → Settings → Variables")
        print()
        print("📋 Variables à ajouter manuellement:")
        for key, value in VARIABLES.items():
            print(f"   {key} = {value}")

if __name__ == "__main__":
    main()

