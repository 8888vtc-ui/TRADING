"""
Script pour configurer automatiquement les variables d'environnement sur Railway
Utilise l'API Railway GraphQL
"""
import requests
import json

# Configuration
RAILWAY_TOKEN = "c5d27e96-a521-43fa-8014-ed1079cc12c4"
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

def get_projects():
    """Récupère la liste des projets Railway via GraphQL"""
    query = """
    query {
        me {
            projects {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            RAILWAY_API_URL,
            headers=get_headers(),
            json={"query": query}
        )
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('me', {}).get('projects', {}).get('edges', [])
    except Exception as e:
        print(f"❌ Erreur récupération projets: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Réponse: {e.response.text}")
        return None

def get_services(project_id):
    """Récupère les services d'un projet"""
    query = """
    query($projectId: String!) {
        project(id: $projectId) {
            services {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            RAILWAY_API_URL,
            headers=get_headers(),
            json={
                "query": query,
                "variables": {"projectId": project_id}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('project', {}).get('services', {}).get('edges', [])
    except Exception as e:
        print(f"❌ Erreur récupération services: {e}")
        return None

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
        response.raise_for_status()
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Erreurs: {data['errors']}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur définition variables: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Réponse: {e.response.text}")
        return False

def main():
    print("=" * 60)
    print("🚀 CONFIGURATION DES VARIABLES RAILWAY")
    print("=" * 60)
    print()
    
    # Récupérer les projets
    print("📋 Récupération des projets...")
    projects = get_projects()
    
    if not projects:
        print("❌ Aucun projet trouvé ou erreur d'authentification")
        print("💡 Vérifiez que votre token Railway est correct")
        return
    
    if len(projects) == 0:
        print("❌ Aucun projet trouvé")
        return
    
    print(f"✅ {len(projects)} projet(s) trouvé(s)")
    print()
    
    # Afficher les projets
    for i, project_edge in enumerate(projects, 1):
        project = project_edge['node']
        print(f"{i}. {project['name']} (ID: {project['id']})")
    
    print()
    
    # Prendre le premier projet
    project = projects[0]['node']
    project_id = project['id']
    project_name = project['name']
    
    print(f"📦 Projet sélectionné: {project_name}")
    print()
    
    # Récupérer les services
    print("🔍 Récupération des services...")
    services = get_services(project_id)
    
    if not services or len(services) == 0:
        print("❌ Aucun service trouvé")
        print("💡 Créez d'abord un service dans Railway")
        return
    
    print(f"✅ {len(services)} service(s) trouvé(s)")
    print()
    
    # Afficher les services
    for i, service_edge in enumerate(services, 1):
        service = service_edge['node']
        print(f"{i}. {service['name']} (ID: {service['id']})")
    
    print()
    
    # Prendre le premier service
    service = services[0]['node']
    service_id = service['id']
    service_name = service['name']
    
    print(f"⚙️ Service sélectionné: {service_name}")
    print()
    
    # Configurer les variables
    print("🔧 Configuration des variables...")
    print()
    
    for key in VARIABLES.keys():
        print(f"   {key}...", end=" ")
    
    print()
    
    if set_variables(service_id, VARIABLES):
        print()
        print("=" * 60)
        print("✅ TOUTES LES VARIABLES ONT ÉTÉ CONFIGURÉES !")
        print("=" * 60)
        print()
        print("📋 Variables configurées:")
        for key, value in VARIABLES.items():
            print(f"   ✅ {key}")
        print()
        print("💡 Railway redéploiera automatiquement avec les nouvelles variables")
    else:
        print()
        print("=" * 60)
        print("❌ ERREUR LORS DE LA CONFIGURATION")
        print("=" * 60)
        print()
        print("💡 Essayez de configurer manuellement dans Railway → Settings → Variables")

if __name__ == "__main__":
    main()
