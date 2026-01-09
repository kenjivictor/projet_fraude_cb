import pandas as pd
import requests
import time

FILE_PATH = "data/PaySim_stream.csv"
#adresse de l'api qui envoie
API = "http://127.0.0.1:8000/predict"

df = pd.read_csv(FILE_PATH)

for index, row in df.iterrows():
    transaction = row.to_dict()
    time.sleep(0.5)
    print(transaction)
    response = requests.post(API, json=transaction)
    print(response.status_code)