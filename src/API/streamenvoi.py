import pandas as pd
import requests
import time
import os

# "marque-page" / en cas de coupures évite les doublons
OFFSET_FILE = "data/pointer.txt"

# fonction de  lecture
def get_last_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            return int(f.read().strip()) 
    return 0

# fonction de sauvegarde 
def save_offset(current_line):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(current_line))

print("Attente de l'API...")
while True:
    try:
        requests.get("http://localhost:8000/") 
        print("API prête ! Décollage...")
        break
    except:
        # Si elle ne répond pas, on attend 1 seconde et on recommence
        time.sleep(1)

last_line = get_last_offset() 

with open("data/PaySim_stream.csv", "r") as f:
    for i, line in enumerate(f):

        if i <= last_line:
            continue 
        # 1. On découpe la ligne CSV par les virgules
        val = line.strip().split(',')
        
        # 2. On crée l'objet que l'API attend (le format JSON)
        transaction = {
            "step": int(val[0]),
            "type": val[1],
            "amount": float(val[2]),
            "nameOrig": val[3],
            "oldbalanceOrg": float(val[4]),
            "newbalanceOrig": float(val[5]),
            "nameDest": val[6],
            "oldbalanceDest": float(val[7]),
            "newbalanceDest": float(val[8]),
            "isFraud": int(val[9]),
            "isFlaggedFraud": int(val[10])
        }
        try:
            response = requests.post("http://localhost:8000/predict", json=transaction)
            
            if response.status_code == 200:
                if i % 100 == 0:
                    save_offset(i)
                    print(f"Marque-page posé à la ligne : {i}")
        except:
            time.sleep(1)
            
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
    time.sleep(0.001)
    print(transaction)
    response = requests.post(API, json=transaction)
    print(response.status_code)
    
# Pour lancer le script : python src/API/streamenvoi.py