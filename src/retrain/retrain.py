import pandas_gbq
import joblib  
from sklearn import pipeline
from xgboost import XGBClassifier
from datetime import datetime
import os
import requests
from prefect import task, flow
import time
import json
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score, precision_score, f1_score, accuracy_score

load_dotenv()

# On récupère les variables du .env
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("GCP_DATASET")

# Permet de récupérer la clé GCP
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

# Creation des taches Prefect
@task(name = "Vérifier les nouvelles données")
def check_new_data() :
    sql = f"""
    SELECT count(*) as nombre_lignes
    FROM `{PROJECT_ID}.{DATASET_ID}.predictions_transaction`    
    """
    df = pandas_gbq.read_gbq(sql, project_id=PROJECT_ID)
    number_lines = df['nombre_lignes'][0]
    print(number_lines)
    return number_lines

@task(name="Réentraînement du modèle")
def retrain_model(nouveau_nombre_lignes):    
    with open('state.json', 'r') as f:
        state = json.load(f)
    
    limite_echantillon = state.get("limit_sql", 200000)
    try:
        pipeline = joblib.load("src/models/pipeline_latest.joblib")
        print("Dernier pipeline chargé pour mise à jour.")
    except:
        pipeline = joblib.load("src/models/pipeline_v1.joblib")
        print("Chargement de la V1 (première exécution).")
    retrain_sql = f"""
    # On récupere toutes les fraudes
    (SELECT 
        LEFT(nameOrig, 1) AS nameOrig, LEFT(nameDest, 1) AS nameDest,
        MOD(step, 24) AS hour, type, amount, oldbalanceOrg, oldbalanceDest, isFraud
    FROM `{PROJECT_ID}.{DATASET_ID}.historical_transactions`
    WHERE isFraud = 1)

    UNION ALL

    (SELECT 
        LEFT(nameOrig, 1) AS nameOrig, LEFT(nameDest, 1) AS nameDest,
        MOD(step, 24) AS hour, type, amount, oldbalanceOrg, oldbalanceDest, isFraud
    FROM `{PROJECT_ID}.{DATASET_ID}.predictions_transaction`
    WHERE isFraud = 1)

    UNION ALL

    -- 2. On complète avec un échantillon de 200k transactions normales
    (SELECT 
        LEFT(nameOrig, 1) AS nameOrig, LEFT(nameDest, 1) AS nameDest,
        MOD(step, 24) AS hour, type, amount, oldbalanceOrg, oldbalanceDest, isFraud
    FROM `{PROJECT_ID}.{DATASET_ID}.historical_transactions`
    WHERE isFraud = 0
    ORDER BY RAND()
    LIMIT {limite_echantillon})
    """
    
    new_data = pandas_gbq.read_gbq(retrain_sql, project_id=PROJECT_ID)

    # X y
    X_new = new_data.drop('isFraud', axis=1)
    y_new = new_data['isFraud']
    
    # X train
    
    X_train, X_val, y_train, y_val = train_test_split(X_new, y_new, test_size=0.2, stratify=y_new)
    
    # Calcul ratio dynamique
    count_norm = (y_new == 0).sum()
    count_fraud = (y_new == 1).sum()
    new_ratio = count_norm / count_fraud
    
    # Recup les parametre de l'ancien mod_le
    pipeline.set_params(
    model__scale_pos_weight=new_ratio,
    model__n_jobs=4,
    model__tree_method='hist',
    model__device='cpu')

    # Entranement (Fit)
    print("Entraînement du modèle en cours...")
    pipeline.fit(X_train, y_train)
    
    # On prédit sur les 20% restants
    y_pred = pipeline.predict(X_val)
    
    metrics_simple = {
        "recall": round(recall_score(y_val, y_pred, pos_label=1) * 100, 2),
        "precision": round(precision_score(y_val, y_pred, pos_label=1) * 100, 2),
        "f1": round(f1_score(y_val, y_pred, pos_label=1) * 100, 2),
        "accuracy": round(accuracy_score(y_val, y_pred) * 100, 2)
    }
    
    # Réentrainement sur l'ensemble des données
    pipeline.fit(X_new, y_new)

    # Sauvegarde et versionning
    timestamp = datetime.now().strftime("%Y%m%d")
    archive_name = f"src/models/archives/pipeline_{timestamp}.joblib"
    latest_name = "src/models/pipeline_latest.joblib"

    # On sauvegarde deux fois
    joblib.dump(pipeline, archive_name) # L'archive 
    joblib.dump(pipeline, latest_name)  # Le fichier que le script chargera au début

    print(f"Archive créée : {archive_name}")
    print(f"Fichier 'latest' mis à jour.")
    
    # Envoi des scores a l'API
    try:
        payload = {
            "version_id": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "metrics": metrics_simple
        }
        requests.post("http://api-recepteur:8000/update_metrics", json=payload, timeout=5)
        print("Métriques envoyées à l'API.")
    except Exception as e:
        print(f"Erreur envoi API : {e}")
    
    state["last_count"] = int(nouveau_nombre_lignes)
    with open('state.json', 'w') as f:
        json.dump(state, f, indent = 4)
    
    print(f"Compteur mis à jour : {nouveau_nombre_lignes} lignes.")


   # Pour lancer la mise à jour sur l'API
@task(name="Notifier l'API")
def notify_api():
    url_api = "http://api-recepteur:8000/reload"
    response = requests.get(url_api)
    
    if response.status_code == 200:
        resultat = response.json()
        print(f"Nouveau modèle en prod : {resultat['modele_du']}")
    else:
        print(f"Echec de la mise à jour du modèle. Réponse API : {response.status_code}")

# Le chef d'orchestre
@flow(name = "Réentrainement du modèle de détection de fraude")
def start_pipeline() :
    with open('state.json', 'r') as f:
        config = json.load(f)
    seuil = config.get("min_rows_to_retrain", 5000)
    ancien = config.get("last_count", 0)
    nouveau = check_new_data()
    print(f"Ancien: {ancien}, Nouveau: {nouveau}")
    
    if nouveau >= ancien + seuil :
        print("On réentraîne.")
        retrain_model(nouveau)
        notify_api()
    else :
        print("Pas assez de nouvelles données pour réentraîner le modèle.")

#delai poru réentrainement toutes les 2 minutes (intervalle=120 sec)
if __name__ == "__main__":

    print("Démarrage de l'automatisation de réentraînement...")  
    while True:
        try:
            start_pipeline() 
            with open('state.json', 'r') as f:
                config = json.load(f)
            
            attente = config.get("check_interval_secondes")
        except Exception as e:
            print(f"Erreur : {e}")
            
        print(f"Attente de {attente} secondes avant la prochaine vérification...")
        time.sleep(attente) 