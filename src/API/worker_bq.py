import redis
import json
import time
import os
from google.cloud import bigquery

# connexion à Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# test de connexion
try:
    r.ping()
    print("Connexion Redis réussie !", flush=True)
except redis.exceptions.ConnectionError:
    print("ERREUR : Impossible de joindre Redis. Vérifie le docker-compose.", flush=True)

print("Le Worker est démarré et surveille la file d'attente...")

# infos pour BigQuery 
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/API/gcp-key.json"
client = bigquery.Client()
table_id = "projet-fraude-paysim.paysim_raw.predictions_transaction"

while True:
    paquet_a_envoyer = []
    
    for _ in range(200):
        donnee_brute = r.rpop("flux_global")
        
        if donnee_brute:
            transaction = json.loads(donnee_brute)
            paquet_a_envoyer.append(transaction)
        else:
            break

        if paquet_a_envoyer:
            print(f"Tentative d'envoi vers BigQuery...", flush=True)
            errors = client.insert_rows_json(table_id, paquet_a_envoyer)

        if errors == []:
            print("Succès : Google a accepté le paquet !", flush=True)
        else:
            print("ERREUR GOOGLE :", flush=True)
            print(errors, flush=True)
            
        time.sleep(1) # Simule le temps de réponse de Google
        print("Envoi réussi !")
    
    time.sleep(5)