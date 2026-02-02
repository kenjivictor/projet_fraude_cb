import os
import pandas as pd
from pandas_gbq import to_gbq
from dotenv import load_dotenv

# Permet de récupérer la clé GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

#Charger variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les configurations (avec des valeurs par défaut au cas où)
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "projet-fraude-paysim")
DATASET_ID = os.getenv("GCP_DATASET", "paysim_raw")

df = pd.read_csv("data/PaySim_historical.csv")

# adresse dynamique
destination_hist = f"{PROJECT_ID}.{DATASET_ID}.historical_transactions"
destination_pred = f"{PROJECT_ID}.{DATASET_ID}.predictions_transaction"

# Envoi de l'historique
to_gbq(df, destination_hist, project_id=PROJECT_ID, if_exists="replace")

df_pred_schema = df.head(0).copy()
df_pred_schema['verdict'] = ""

# Création de la table de prédictions vide
to_gbq(df_pred_schema.head(0), destination_pred, project_id=PROJECT_ID, if_exists="append")

print("Historique des transactions importé dans BigQuery avec succès.")