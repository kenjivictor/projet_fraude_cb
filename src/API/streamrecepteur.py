from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime

app = FastAPI()

# Chargement du pipeline
pipeline = joblib.load('src/models/pipeline_latest.joblib')

# Liste pour stocker les fraudes detectees  
frauds_detected = []
infos = {"nb_transactions" : 0}

# Defini le Json attendu en entree
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
    isFlaggedFraud: int
    
#Réception et traitement des donnees! Prediciton se fera ioci   
@app.post("/predict")
async def recevoir_transaction(transaction: TransmissionRequest):
    #Conversion json en DataFrame
    df = pd.DataFrame([transaction.dict()])
    # Manipulation des données pour correspondre au modèle
    df['hour'] = df['step'] % 24
    df['nameOrig'] = df['nameOrig'].str[0]
    df['nameDest'] = df['nameDest'].str[0]
    prediction = pipeline.predict(df)
        
    verdict = "FRAUDE" if prediction[0] == 1 else "SAIN"
    infos["nb_transactions"] += 1

    if prediction[0] == 1:
        frauds_detected.append({
            "step": transaction.step,
            "montant": transaction.amount,
            "client": transaction.nameOrig,
            "type": transaction.type
        })
        print(f"ALERTE : Fraude détectée ! Montant: {transaction.amount}€")
    else:
        print(f"Transaction saine : {transaction.amount}€")
        
    return {"prediction": verdict, "status": "success"}

@app.get("/report")
async def get_report():
    return {
        "nb_fraudes_detectees": len(frauds_detected),
        "details": frauds_detected,
        "infos": infos,
    }


@app.get("/reload")
async def reload_model():
    global pipeline
    # On récuprer l'heure du fichier et le model le plus récent pour le versionning
    pipeline = joblib.load('src/models/pipeline_latest.joblib')
    timestamp = os.path.getmtime('src/models/pipeline_latest.joblib')
    date_formatee = datetime.fromtimestamp(timestamp).strftime('%d/%m %H:%M:%S')
    return {"status": "success", "modele_du": date_formatee}



# Pour lancer le serveur : uv run uvicorn src.API.streamrecepteur:app --reload
# Pour acceder au rapport : http://127.0.0.1:8000/report