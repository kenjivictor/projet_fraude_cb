import pandas as pd
import os


df = pd.read_csv("data/PaySim.csv")
print(df.shape[0])

#On récupère 90% des données pour l'entrainement
nb_historique = int(len(df)*0.90)

df_historical = df.iloc[:nb_historique]
df_stream = df.iloc[nb_historique:]


if len(df_historical) + len(df_stream) == len(df):
    decoupe1 = True
    print("Les deux fichiers font bien la somme du fichier initial.")
else:
    decoupe1 = False
if len(df_historical) == nb_historique:
    decoupe2= True
    print("Le fichier historique fait bien 90% du fichier initial.")
else:
    decoupe2= False
if len(df_stream) == len(df) - nb_historique:
    decoupe3= True
    print("Le fichier de stream fait bien 10% du fichier initial.")
else:
    decoupe3= False
    
if decoupe1 and decoupe2 and decoupe3:
    print("La découpe a été effectuée correctement.")
    df_historical.to_csv("data/PaySim_historical.csv", index=False)
    df_stream.to_csv("data/PaySim_stream.csv", index=False)
    
