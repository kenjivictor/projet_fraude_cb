import redis
import json
import time
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# connexion à Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("GCP_DATASET")
# On crée la connexion. decode_responses=True permet de recevoir du texte 
# au lieu de données binaires
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

continuer = False
# test de connexion
try:
    r.ping()
    print("Connexion Redis réussie !", flush=True)
    continuer = True
except redis.exceptions.ConnectionError as e:
    print(f"ERREUR : Impossible de joindre Redis. Vérifie le docker-compose.\nMESSAGE : {e}", flush=True)

if continuer:
    print("Le Worker est démarré et surveille la file d'attente...")

    # infos pour BigQuery 
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"
    client = bigquery.Client(project=PROJECT_ID)
    TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.predictions_transaction"

    while True:
        paquet_a_envoyer = []
        
        for _ in range(2000):
            # Recupère la donnée et la supprime
            donnee_brute = r.rpop("flux_global")
            
            # Verifie si redis a retourné une donnée
            if donnee_brute:
                transaction = json.loads(donnee_brute)
                transaction.pop('probabilite', None)
                paquet_a_envoyer.append(transaction)
            #Si pas de donnée, on sort
            else:
                break
            
            
        if paquet_a_envoyer:
            print(f"Tentative d'envoi {len(paquet_a_envoyer)} lignes vers BigQuery...", flush=True)
            errors = client.insert_rows_json(TABLE_ID, paquet_a_envoyer)

            if errors == []:
                print(f"Succès : {len(paquet_a_envoyer)} lignes insérées.", flush=True)
                r.set("last_insert_count", len(paquet_a_envoyer))
                r.set("last_insert_time", time.time())
            else:
                print("ERREUR GOOGLE :", flush=True)
                print(errors, flush=True)
                
            print("Envoi réussi !")
        
        time.sleep(30)
        
else:
    print("Le worker BigQuery n'a pas pu démarrer.")