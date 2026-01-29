import pandas as pd
import requests
import time
import os

FILE_PATH = "data/PaySim_stream.csv"
#adresse de l'api qui envoie
BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API = f"{BASE_URL}/predict"

#Tentative de connexion
while True:
    try:
        requests.get(BASE_URL) 
        print("API en ligne !")
        break
    except:
        time.sleep(1)


df = pd.read_csv(FILE_PATH)

for index, row in df.iterrows():
    transaction = row.to_dict()
    time.sleep(0.01)
    print(transaction)
    response = requests.post(API, json=transaction)
    print(response.status_code)
    
