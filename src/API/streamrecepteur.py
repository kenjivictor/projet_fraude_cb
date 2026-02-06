from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import redis
import json 
import os
from datetime import datetime
from prometheus_fastapi_instrumentator import Instrumentator
import time

app = FastAPI()

# configuration & connexion au conteneur redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis") 
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# chargement du pipeline
try:
    # version la plus récente
    pipeline = joblib.load('src/models/pipeline_latest.joblib')
    print("API : Dernier pipeline chargé au démarrage.")
except Exception:
    # Si le fichier n'existe pas encore on prend v1
    pipeline = joblib.load('src/models/pipeline_v1.joblib')
    print("API : Chargement de la V1 (modèle de secours).")
    
# Historique metrique modele v1
historique_versions = [{"version_id": "V1 (Initiale)",
        "metrics": {
            "recall": 87.00,
            "precision": 63.00,
            "f1": 73.00,
            "accuracy": 100.00}}]  

# défini le Json attendu en entree
class TransmissionRequest(BaseModel):
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float
    isFraud: int #Uniquement pour connaitre la verite terrain. En tant normal, on aurait un retour client
    isFlaggedFraud: int
    
 # Initialisation de la matrice de confusion   
matrix_stats = {"vrais_positifs": 0,
                        "faux_positifs": 0, 
                        "vrais_negatifs": 0, 
                        "faux_negatifs": 0}
    
    
    
    

# réception et traitement des donnees
@app.post("/predict")
async def recevoir_transaction(transaction: TransmissionRequest):
    # Manipulation des données pour correspondre au modèle
    df = pd.DataFrame([transaction.model_dump()])   
    # On recupere la fraude pour les metriques
    realite = df.pop('isFraud').iloc[0]
    df['hour'] = df['step'] % 24
    df['nameOrig'] = df['nameOrig'].str[0]
    df['nameDest'] = df['nameDest'].str[0]
    prediction = pipeline.predict(df)
    
    # Maj pour matrice de confusion
    if prediction == 0 and realite == 0: 
        matrix_stats["vrais_negatifs"] += 1
    elif prediction == 1 and realite == 0: 
        matrix_stats["faux_positifs"] += 1
    elif prediction == 0 and realite == 1: 
        matrix_stats["faux_negatifs"] += 1
    elif prediction == 1 and realite == 1: 
        matrix_stats["vrais_positifs"] += 1
        
    verdict = "FRAUDE" if prediction[0] == 1 else "SAIN"
    probabilite = pipeline.predict_proba(df)[0][1] * 100  # Probabilité de fraude
    
    # modèle de stockage dans redis au format dictionnaire
    res_to_store = {
            "step": int(transaction.step),
            "type": str(transaction.type),
            "amount": float(transaction.amount),
            "nameOrig": str(transaction.nameOrig),
            "oldbalanceOrg": float(transaction.oldbalanceOrg), 
            "newbalanceOrig": float(transaction.newbalanceOrig), 
            "nameDest": str(transaction.nameDest), 
            "oldbalanceDest": float(transaction.oldbalanceDest), 
            "newbalanceDest": float(transaction.newbalanceDest), 
            "isFraud": int(transaction.isFraud),                
            "isFlaggedFraud": int(transaction.isFlaggedFraud),  
            "verdict": verdict,
            "probabilite": float(round(probabilite, 2))                                  
        }
    # convertir en texte pour Redis
    json_data = json.dumps(res_to_store)

    # --- --Flux Bigquery ------------
    r.lpush("flux_global", json_data)   
    
    # ------ Flux Streamlit -----------
    r.lpush("flux_streamlit", json_data)
    

    if prediction[0] == 1:
        r.lpush("liste_fraudes", json_data)
        # r.expire("liste_fraudes", 172800) => Facultatif on garde 2j la liste
        print(f"ALERTE : Fraude détectée ! Montant: {transaction.amount}€")
    else:
        print(f"Transaction saine : {transaction.amount}€")
    return {"prediction": verdict,"probabilite": f"{round(probabilite, 2)}%", "status": "success"}

# Metriques modele
@app.post("/update_metrics")
async def update_metrics(data: dict):
    global historique_versions
    
    historique_versions.insert(0, data)
    #Uniquement 5 dernieres versions
    historique_versions = historique_versions[:5]
    
    return {"status": "success"}



@app.get("/report")
async def report():
    total_traitees = r.llen("flux_streamlit")
    fraudes_brutes = r.lrange("liste_fraudes", 0, -1) 
    
    # dictionnaire des fraudes détectées
    fraudes_decodees = [json.loads(f) for f in fraudes_brutes]
    
    # réponse pour Streamlit
    return {
        "infos":  {"nb_transactions" : total_traitees},
        "details": fraudes_decodees,
        "nb_fraudes_detectees": len(fraudes_decodees),
        "matrix": matrix_stats,
        "history": historique_versions
    }


# Pour le rechargement du modèle
@app.get("/reload")
async def reload_model():
    global pipeline
    # On récuprer l'heure du fichier et le model le plus récent pour le versionning
    try:
        # On tente de charger, si ça rate on passe dans le 'except'
        new_pipeline = joblib.load('src/models/pipeline_latest.joblib')
        pipeline = new_pipeline
        mtime = os.path.getmtime('src/models/pipeline_latest.joblib')
        date_formatee = datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M:%S')
        return {"status": "success", "modele_du": date_formatee, "version_id": mtime}
    except Exception as e:
        print(f"Erreur rechargement : {e}")
        return {"status": "error", "message": "Conservation de l'ancien modèle"}

#exposition des métriques de FastApi
Instrumentator().instrument(app).expose(app)

