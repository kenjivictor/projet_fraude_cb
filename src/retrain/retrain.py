import pandas_gbq
import joblib  
from xgboost import XGBClassifier
from datetime import datetime
import os
import requests

# Permet de récupérer la clé GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

try:
    pipeline = joblib.load("src/models/pipeline_latest.joblib")
    print("Dernier pipeline chargé pour mise à jour.")
except:
    pipeline = joblib.load("src/models/pipeline_v1.joblib")
    print("Chargement de la V1 (première exécution).")

# Faire une requete pour voir s'il y a des données dans la table
sql = """
    SELECT count(*) as nombre_lignes
    FROM `projet-fraude-paysim.paysim_raw.historical_transactions`    
"""
df = pandas_gbq.read_gbq(sql, project_id="projet-fraude-paysim")
print(df)

# Nombres de lignes de base dans data historical
# 5726358
with open('src/retrain/last_count.txt', 'r') as f:
    contenu = f.read()
    historical_count = int(contenu)
print("Nombre de lignes historiques :", historical_count)

# Faire un seuil de déclenchement pour reentrainer le modèle (+ 15000 lignes)

number_lines = df['nombre_lignes'][0]
print(number_lines)

# Condition d'avoir  5000 nouvelles lignes
if number_lines >= historical_count +5000 :
    print("Nouvelle données détectées, réentrainment du modèle en cours...")
    historical_count = number_lines +15000
    # on récuypere les données et on les retransforme
    # On prend toutes les fraudes + un echantillon de non fraude pour eviter d'avoir un dataset trop gros
    # Pas forcément utile dans notre démo mais important en prod
    
    retrain_sql = """
    # On récupere toutes les fraudes
    (SELECT 
        LEFT(nameOrig, 1) AS nameOrig, LEFT(nameDest, 1) AS nameDest,
        MOD(step, 24) AS hour, type, amount, oldbalanceOrg, oldbalanceDest, isFraud
    FROM `projet-fraude-paysim.paysim_raw.historical_transactions`
    WHERE isFraud = 1)

    UNION ALL

    (SELECT 
        LEFT(nameOrig, 1) AS nameOrig, LEFT(nameDest, 1) AS nameDest,
        MOD(step, 24) AS hour, type, amount, oldbalanceOrg, oldbalanceDest, isFraud
    FROM `projet-fraude-paysim.paysim_raw.predictions_transaction`
    WHERE isFraud = 1)

    UNION ALL

    -- 2. On complète avec un échantillon de 500k transactions normales
    (SELECT 
        LEFT(nameOrig, 1) AS nameOrig, LEFT(nameDest, 1) AS nameDest,
        MOD(step, 24) AS hour, type, amount, oldbalanceOrg, oldbalanceDest, isFraud
    FROM `projet-fraude-paysim.paysim_raw.historical_transactions`
    WHERE isFraud = 0
    ORDER BY RAND()
    LIMIT 500000)
    """
    
    new_data = pandas_gbq.read_gbq(retrain_sql, project_id="projet-fraude-paysim")

    # X y
    X_new = new_data.drop('isFraud', axis=1)
    y_new = new_data['isFraud']
    
    # Calcul ratio dynamique
    count_norm = (y_new == 0).sum()
    count_fraud = (y_new == 1).sum()
    new_ratio = count_norm / count_fraud
    
    # Recup les parametre de l'ancien mod_le
    pipeline.set_params(model__scale_pos_weight=new_ratio)

    # Entranement (Fit)
    print("Entraînement du modèle en cours...")
    pipeline.fit(X_new, y_new)

    # Sauvegarde et versionning
    timestamp = datetime.now().strftime("%Y%m%d")
    archive_name = f"src/models/pipeline_{timestamp}.joblib"
    latest_name = "src/models/pipeline_latest.joblib"

    # On sauvegarde deux fois
    joblib.dump(pipeline, archive_name) # L'archive 
    joblib.dump(pipeline, latest_name)  # Le fichier que le script chargera au début

    print(f"Archive créée : {archive_name}")
    print(f"Fichier 'latest' mis à jour.")
    
    with open('src/retrain/last_count.txt', 'w') as f:
        f.write(str(number_lines))
    
    print(f"Compteur mis à jour : {number_lines} lignes.")
    
    # Pour lancer la mise à jour sur l'API
    print("📡 Notification de l'API pour le rechargement...")
        # Script pour simumler le clic et la maj du modéle
    url_api = "http://localhost:8000/reload" 
    response = requests.get(url_api)
    
    if response.status_code == 200:
        resultat = response.json()
        print(f"Nouveau modèle en prod : {resultat['modele_du']}")
    else:
        print(f"Echec de la mise à jour du modèle. Réponse API : {response.status_code}")

else :
    print("Pas assez de nouvelles données pour réentraîner le modèle.")