import os
import shutil
import json
import subprocess
import time
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("GCP_DATASET")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"
modele_latest_path = 'src/models/pipeline_latest.joblib'
archive_dir_path = 'src/models/archives/'


# Suppression des anciens modèles
if os.path.exists(modele_latest_path):
    os.remove(modele_latest_path)
    print(f"Version latest supprimée : {modele_latest_path}")
else:
    print(f"Aucune version 'latest' trouvée")

#Suppression des archives
try: 
    shutil.rmtree(archive_dir_path)
    print(f"Le dossier '{archive_dir_path}' et son contenu ont été supprimés.")
except FileNotFoundError: print(f"Pas de dossier {archive_dir_path} trouvés.")

# Recréation du dossier d'arcives vide
os.makedirs(archive_dir_path, exist_ok=True)
print(f"Dossier d'archives recréé : {archive_dir_path}")

# Reinitialisation du compteur
with open('state.json', 'r') as f:
    state = json.load(f)

state["last_count"] = 0
state['best_recall'] = 87
with open('state.json', 'w') as f:
    json.dump(state, f, indent = 4)
    
    
# Réinitialisation de redis
subprocess.run(["docker", "start", "redis-service"])
print("Demarrage du conteneur redis")
time.sleep(2)  #Attendre que le conteneur demarre
subprocess.run(["docker", "exec", "redis-service", "redis-cli", "FLUSHALL"])
print("Redis réinitialisé.")
time.sleep(2) 
subprocess.run(["docker", "stop", "redis-service"])
print("Arrêt du conteneur redis")

# Réinitialisation de Prefect 
try:
    print("Réinitialisation forcée de la base Prefect...")
    
    # Arret du conteneur
    subprocess.run(["docker", "stop", "prefect-server"], check=True)
    
    # supression du fichier de base de données (qui contient les runs flows log etc)
    #Le chemin est  /root/.prefect/prefect.db
    subprocess.run([
        "docker", "run", "--rm", 
        "--volumes-from", "prefect-server", 
        "busybox", "rm", "/root/.prefect/prefect.db"
    ], check=True)
    
    print("Fichier de base de données supprimé.")

    # redemarre conteneur
    subprocess.run(["docker", "start", "prefect-server"], check=True)
    print("Serveur Prefect redémarré avec une base vierge.")
    
except subprocess.CalledProcessError as e:
    print(f"Erreur lors du reset forcé : {e}")

# Réinitialisation de Bigquery
try :
    print("Réinitialisation des tables BigQuery")
    client = bigquery.Client()
    reset_sql = f"""TRUNCATE TABLE `{PROJECT_ID}.{DATASET_ID}.predictions_transaction`;"""
    query = client.query(reset_sql)
    query.result()
    
except Exception as e:
    print("Erreur lors de la réinitialisation des tables BigQuery :", e)

print("Table BigQuery réinitialisée.")

