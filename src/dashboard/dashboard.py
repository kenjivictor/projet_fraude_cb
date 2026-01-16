import streamlit as st
import pandas as pd
import requests
import time

API_LINK = "http://127.0.0.1:8000"

def get_report():
    response = requests.get(API_LINK + "/report")
    if response.status_code == 200:
        return response.json()
    else:
        return None



st.title("Détection de fraude")
st.header("🎯Tableau de bord")


placeholder = st.empty()
list_pourcent_fraude = []

#actualisation de la vue en temps réel
while True:
    report = get_report()
    if report is not None:
        df = pd.DataFrame(report['details'])
        
        #calcul des métriques
        
        if len(df):
            montant_total_intercepte = round(df["montant"].sum(),2)
            moyenne_par_fraude = round(df["montant"].mean(),2)
        else:
            montant_total_intercepte = 0
            moyenne_par_fraude = 0
        
        nb_transactions = report['infos']['nb_transactions']
        nb_fraudes_detectees = report['nb_fraudes_detectees']
        if nb_transactions >0:
            pourcent_fraude = round((nb_fraudes_detectees/nb_transactions)*100,2)
            list_pourcent_fraude.append(pourcent_fraude)
        else:
            pourcent_fraude = 0
        
        
        #affichage des KPIs de façon dynamique
        
        with placeholder.container():
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Nb transactions", nb_transactions)
            col2.metric("Nb fraudes", nb_fraudes_detectees)
            col3.metric("% " + "fraudes", f"{pourcent_fraude} %")
            
            col1, col2 = st.columns(2)
            col1.metric("Montant total intercepté", montant_total_intercepte)
            col2.metric("Montant moyen par fraude", moyenne_par_fraude)
            
            if nb_fraudes_detectees >0:
                st.dataframe(df)
                st.line_chart({"data": list_pourcent_fraude})
            
            
            time.sleep(5)

