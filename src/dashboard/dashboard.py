import streamlit as st
import pandas as pd
import requests
import os
import time

# Page conffig
st.set_page_config(
    page_title="Détection de Fraude",
    layout="wide", 
    initial_sidebar_state="expanded")


# Page conffig
st.set_page_config(
    page_title="Détection de Fraude",
    layout="wide", 
    initial_sidebar_state="expanded")

API_BASE_URL = os.getenv("API_URL", "http://api-recepteur:8000")
REPORT_URL = f"{API_BASE_URL}"

def get_report():
    try:
        response = requests.get(REPORT_URL + "/report", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
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
            montant_total_intercepte = round(df["amount"].sum(),2)
            moyenne_par_fraude = round(df["amount"].mean(),2)
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
            col1.metric("Nombre de transactions", nb_transactions)
            col2.metric("Nombre de  fraudes", nb_fraudes_detectees)
            col3.metric("Pourcentage de fraudes", f"{pourcent_fraude} %")
            
            col1, col2 = st.columns(2)
            col1.metric("Montant total intercepté",f"{montant_total_intercepte} €")
            col2.metric("Montant moyen par fraude", f"{moyenne_par_fraude} €")
            
            if nb_fraudes_detectees >0:
                col1_tina, col2_tina, col3_tina = st.columns([3,3,2])
                with col2_tina :
                    st.write("### Détails des fraudes détectées")
                st.dataframe(df)
                colgraph1, colgraph2 = st.columns(2)
                with colgraph1:
                    col1_tin, col2_tin, col3_tin = st.columns([3,3,2])
                    with col2_tin :
                        st.write("### Pourcentage de fraudes")
                    st.line_chart({"data": list_pourcent_fraude})
                
                with colgraph2:
                    col1_ti, col2_ti, col3_ti = st.columns([3,3,2])
                    with col2_ti :
                        st.write("### Répartition des fraudes")
                    type_counts = df['type'].value_counts()
                    st.bar_chart(type_counts)

            
        time.sleep(1)

