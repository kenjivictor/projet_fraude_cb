from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


# Defini le Json attendu en entree
class TransmissionRequest(BaseModel):
    step: int
    type: str
    amount: float

#Réception et traitement des donnees! Prediciton se fera ioci   
@app.post("/predict")
async def recevoir_transaction(transaction: TransmissionRequest):
    print(f"Reçu dans le récepteur : {transaction.amount}€")
    return {"status": "success"}