from numpy import test
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
import os
import time

# Page conffig
st.set_page_config(
    page_title="Détection de Fraude",
    layout="wide", 
    initial_sidebar_state="expanded")

def metric_card(label, value, color="#f0f2f6"):
    st.markdown(
        f"""
        <div style="
            background-color: {color};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #ddd;
            margin-bottom: 10px;">
            <p style="margin: 0; font-size: 14px; color: #555; font-weight: bold;">{label}</p>
            <h2 style="margin: 0; color: black;">{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


# Page config
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

list_pourcent_fraude = []

#-------------SIDE BAR-----------------

with st.sidebar:
    page_selection = option_menu(
        menu_title="Navigation", 
        options=["Tableau de bord", "Performance du modèle"],
        icons=["speedometer2", "graph-up-arrow"], 
        menu_icon="cast")
    
#---------- PAge stats    
#actualisation de la vue en temps réel

def page_stats():
    placeholder1 = st.empty()

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
            
            with placeholder1.container():
                st.title("Détection de fraude")
                st.header("🎯Tableau de bord")
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
        
        
#--------Page performance modèle

def page_performance_modele():
    placeholder2 = st.empty()

    while True:
        with placeholder2.container():
            coltitle1, coltitle2, coltitle3 = st.columns([3.5,6,1])
            with coltitle2:
                st.title("Performance du modèle")
                
            st.divider()
            
            report = get_report()
            m = report["matrix"]
            
            #Calcul recal
            total_f = m["vrais_positifs"] + m["faux_negatifs"]
            recall = (m["vrais_positifs"] / total_f * 100) if total_f > 0 else 0
            
            # affichage matrice de confusion
            
            col1nn,col2nn, col3nn = st.columns([4,6,1])
            with col1nn:
                st.write("")
            with col2nn:
                st.subheader("Matrice de confusion du modèle")
            with col3nn:
                st.write("")                
                
            col1, col2 = st.columns(2)            
            with col1:
                metric_card("VRAIS NÉGATIFS (SAINS)", m["vrais_negatifs"], color="#d4edda") 
                metric_card("FAUX NÉGATIFS (RATÉS)", m["faux_negatifs"], color="#f8d7da")  
                
            with col2:
                metric_card("FAUX POSITIFS (ALERTES)", m["faux_positifs"], color="#fff3cd") 
                metric_card("VRAIS POSITIFS (FRAUDES)", m["vrais_positifs"], color="#d1ecf1") 

            # affichage recall
            st.divider()
            col1nnn,col2nnn, col3nnn = st.columns([4,6,1])
            with col2nnn:
                st.subheader("Différentes métriques du modèle")
            st.success(f"### Taux de détection (Recall) : {recall:.2f}%")
            
            time.sleep(1)

#------------Navigation des pages



if page_selection == "Tableau de bord":
    page_stats()
elif page_selection == "Performance du modèle":
    page_performance_modele()
    
