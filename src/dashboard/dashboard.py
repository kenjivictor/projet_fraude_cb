from numpy import test
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
import os
import time
import plotly.express as px

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

def format_chiffres(n):
    if n >= 1000000000:
        return f"{n / 1000000000:.2f} Md€"
    if n >= 1000000:
        return f"{n / 1000000:.1f} M€"
    if n >= 1000:
        return f"{n / 1000:.1f} k€"
    return f"{n} €"

def format_metriques(n):
    n= float(n)
    return f"{n:,.0f}".replace(",", " ")

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

def get_reload():
    try:
        response = requests.get(REPORT_URL + "/reload", timeout=2)
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
    st.page_link("http://localhost:3000/", label = "Grafana métrics 🏃‍➡️")
    
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
                coltitlee1, coltitlee2, coltitlee3 = st.columns([3.5,6,1])
                with coltitlee2:
                    st.title("Détection de fraudes")
                st.divider()
                
                col1nn,col2nn, col3nn = st.columns([5,6,1])
                with col1nn:
                    st.write("")
                with col2nn:
                    st.subheader("Tableau de bord")
                with col3nn:
                    st.write("")    

                col1, col2, col3 = st.columns(3)
                with col1:
                    metric_card("Nombre de transactions", format_metriques(nb_transactions),  color="#d4edda")
                    metric_card("Montant total intercepté",f"{format_chiffres(montant_total_intercepte)}", color="#fff3cd")
                with col2:
                    metric_card("Nombre de fraudes", format_metriques(nb_fraudes_detectees), color="#f8d7da")
                    metric_card("Montant moyen par fraude", f"{format_chiffres(moyenne_par_fraude)}", color="#d1ecf1")
                with col3:
                    metric_card("Taux de fraudes", f"{pourcent_fraude} %", color="#e0c5d6")
                    if pourcent_fraude > 0.5: # Seuil arbitraire pour la démo
                     status_alerte = "🔴 CRITIQUE"
                    elif pourcent_fraude > 0:
                        status_alerte = "🟠 ACTIF"
                    else:
                        status_alerte = "🟢 CALME"

                    metric_card(label="État du Système", value=status_alerte)
  # affichage des détails des fraudes détectées
                st.divider()
                if nb_fraudes_detectees >0:
                    col1_tina, col2_tina, col3_tina = st.columns([3,3,2])
                    with col2_tina :
                        st.write("### Détails des fraudes détectées")
                        st.write(" ")
                    colonnes_a_garder = ['type', 'amount', 'nameOrig', 'oldbalanceOrg', 'nameDest', 'oldbalanceDest']
                    df_display = df[colonnes_a_garder].copy()
                    df_display.columns = ['Type', 'Montant (€)', 'ID Origine', 'Solde Orig.', 'ID Destinataire', 'Solde Dest.']
                    st.dataframe(df_display, use_container_width=True)
                    
                    # GRaphiques
                    
                    st.divider()
                    colgraph1, colgraph2 = st.columns(2)
                    #gRPAHE 1
                    with colgraph1:
                        col1_tin, col2_tin, col3_tin = st.columns([3,6,1])
                        with col2_tin :
                            st.write("### Evolution du taux de fraude (%)")
                        df_line = pd.DataFrame({
                                "Temps": range(len(list_pourcent_fraude)),
                                "Taux (%)": list_pourcent_fraude
                            })
                        fig_line = px.line(df_line, x="Temps", y="Taux (%)")
                        fig_line.update_traces(line_color='#e0c5d6') 
                        fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_line, use_container_width=True, key=f"plotly_line_chart{time.time()}")
                     # Graphe 2   
                    with colgraph2:
                        col1_ti, col2_ti, col3_ti = st.columns([3,6,1])
                        with col2_ti : 
                            st.write("### Répartition par type de transfert")
                        type_counts = df['type'].value_counts().reset_index()
                        type_counts.columns = ['Type', 'Nombre']
                        
                        fig_bar = px.bar(type_counts, x='Type', y='Nombre',
                                        text='Nombre', 
                                        template="plotly_white",
                                        color='Type',
                                        color_discrete_sequence=px.colors.qualitative.Pastel)
                        
                        fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, showlegend=False)
                        fig_bar.update_xaxes(title_text="Type de transaction")
                        fig_bar.update_yaxes(title_text="Total détecté")
                        
                        st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_chart_type{time.time()}")          
        time.sleep(1)
        
        
#--------Page performance modèle

def page_performance_modele():
    placeholder2 = st.empty()
    reload_data = get_reload()
    
    while True:
        with placeholder2.container():
            coltitle1, coltitle2, coltitle3 = st.columns([3.5,6,1])
            with coltitle2:
                st.title("Performance du modèle")
                if reload_data and reload_data.get("status") == "success":
                    st.caption(f"Modèle actif mis à jour le : **{reload_data['modele_du']}**")
                
            st.divider()
            
            report = get_report()
            m = report["matrix"]
            
            #Calcul metriques
            total_f = m["vrais_positifs"] + m["faux_negatifs"]
            recall = (m["vrais_positifs"] / total_f * 100) if total_f > 0 else 0
            precision = (m["vrais_positifs"] / (m["vrais_positifs"] + m["faux_positifs"]) * 100) if (m["vrais_positifs"] + m["faux_positifs"]) > 0 else 0
            f1_score = (2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0
            taux_fp = (m["faux_positifs"] / (m["faux_positifs"] + m["vrais_negatifs"]) * 100) if (m["faux_positifs"] + m["vrais_negatifs"]) > 0 else 0
            
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
                metric_card("VRAIS NÉGATIFS (SAINS)", format_metriques(m["vrais_negatifs"]), color="#d4edda") 
                metric_card("FAUX NÉGATIFS (RATÉS)", format_metriques(m["faux_negatifs"]), color="#f8d7da")  
                
            with col2:
                metric_card("FAUX POSITIFS (ALERTES)", format_metriques(m["faux_positifs"]), color="#fff3cd") 
                metric_card("VRAIS POSITIFS (FRAUDES)", format_metriques(m["vrais_positifs"]), color="#d1ecf1") 

            # affichage metriques
            st.divider()
            col1nnn,col2nnn, col3nnn = st.columns([4,6,1])
            with col2nnn:
                st.subheader("Différentes métriques du modèle")
            st.write(" ")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                metric_card(label="🎯 Recall (Sécurité)", value=f"{recall:.2f}%", color="#d4edda")

            with col2:
                metric_card(label="⚖️ Précision", value=f"{precision:.2f}%",color="#f8d7da")

            with col3:
                metric_card(label="📈 F1-Score", value=f"{f1_score:.2f}%", color="#fff3cd")

            with col4:
                metric_card(label="🛡️ Taux FP", value=f"{taux_fp:.2f}%", color="#d1ecf1")

            # --- Section Explications ---
            st.write(" ")
            with st.expander("ℹ️ Comprendre ces indicateurs", expanded = True):
                st.markdown(f"""
                * **Recall ({recall:.2f}%)** : Sur 100 tentatives de fraude, le système en stoppe **{int(recall)}**. C'est l'indicateur de protection contre la fraude.
                * **Précision ({precision:.2f}%)** : Une alerte sur **{int(100/precision) if precision > 0 else 0}** est une vraie fraude. Cela représente l'efficacité du modèle.
                * **F1-Score ({f1_score:.2f}%)** : C'est la **moyenne équilibrée** entre la détection (Recall) et la fiabilité (Précision). Plus il est haut, plus le modèle est stable.
                * **Taux de Faux Positifs ({taux_fp:.2f}%)** : Seuls **{taux_fp:.2f}%** des clients honnêtes sont impactés. C'est l'indicateur de satisfaction client.
                """)
            
            time.sleep(1)

    
#------------Navigation des pages



if page_selection == "Tableau de bord":
    page_stats()
elif page_selection == "Performance du modèle":
    page_performance_modele()
