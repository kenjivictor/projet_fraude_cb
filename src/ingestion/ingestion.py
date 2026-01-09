import os
import pandas as pd
from pandas_gbq import to_gbq

# Permet de récupérer la clé GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

df = pd.read_csv("data/PaySim_historical.csv")

# adresse de destination dans BigQuery
destination = "projet-fraude-paysim.paysim_raw.historical_transactions"

# Fonction pour envoyer les données vers BigQuery
to_gbq(df, destination, project_id="projet-fraude-paysim", if_exists="replace")

print("Historique des transactions importé dans BigQuery avec succès.")