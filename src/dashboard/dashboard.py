from numpy import test
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
import os
import time
import redis
import plotly.express as px
from pathlib import Path
import matplotlib.colors as mcolors

# Page conffig
st.set_page_config(
    page_title="Détection de Fraude",
    layout="wide", 
    initial_sidebar_state="expanded")

# CSS 
st.markdown(f"<style>{Path('src/dashboard/assets/style.css').read_text()}</style>", unsafe_allow_html=True)


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

# Connexion à Redis
r_dash = redis.Redis(host="redis-service", port=6379, db=0, decode_responses=True)

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
        options=["Tableau de bord", "Performance du modèle", "Le projet"],
        icons=["speedometer2", "graph-up-arrow", "book"], 
        menu_icon="cast")
    st.link_button("⚡ Accéder au Monitoring", "http://localhost:3000/", width = "stretch")
    st.link_button("⚙️ MLOps & Automatisation", "http://localhost:4200/dashboard", width = "stretch")
#---------- PAge stats    
#actualisation de la vue en temps réel

@st.fragment(run_every=1)
def page_stats():
#placeholder1 = st.empty()
    if "last_processed_time" not in st.session_state:
        st.session_state.last_processed_time = 0
    if "history_fraude" not in st.session_state:
        st.session_state.history_fraude = []

    #while True:
    last_count = r_dash.get("last_insert_count")
    last_time = r_dash.get("last_insert_time")

    if last_count and last_time:
        last_time = float(last_time)
        if last_time > st.session_state.last_processed_time:
            st.toast(f"{last_count} transactions envoyées à BigQuery !", icon="✅")
            st.session_state.last_processed_time = last_time


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
            st.session_state.history_fraude.append(pourcent_fraude)
        else:
            pourcent_fraude = 0
        
        
        
    #with placeholder1.container():
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
        st.write(" ")

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
            colors = ["#ffb3ba", "#ffffba", "#baffc9"]
            cmap_pastel = mcolors.LinearSegmentedColormap.from_list("pastel_rdylgn", colors)
            colonnes_a_garder = ['type', 'amount','probabilite', 'nameOrig', 'oldbalanceOrg', 'nameDest', 'oldbalanceDest']
            df_display = df[colonnes_a_garder].copy()
            df_display.columns = ['Type', 'Montant (€)','Confiance (%)', 'ID Origine', 'Solde Orig.', 'ID Destinataire', 'Solde Dest.']
            st.dataframe(
                df_display.style.format({
                    "Confiance (%)": "{:.2f} %",
                    "Montant (€)": "{:,.2f} €",    
                    "Solde Orig.": "{:,.2f} €",    
                    "Solde Dest.": "{:,.2f} €" })
                .background_gradient(subset=['Confiance (%)'], 
                                cmap=cmap_pastel, 
                                vmin=50, 
                                vmax=100), use_container_width=True)
            st.write("")
            with st.expander("ℹ️ Comprendre le score de confiance (Probabilité)"):
                st.markdown("""
                **Ce score n'est pas une simple réponse Oui/Non.**
                
                Il représente la **probabilité** estimée par le modèle que la transaction soit frauduleuse (ce qu'on appelle `predict_proba` en Data Science).
                > *Plus le score est proche de 100%, plus les motifs de cette transaction ressemblent à des fraudes passées.*
                """)
                
            # GRaphiques
            
            st.divider()
            colgraph1, colgraph2 = st.columns(2)
            #gRPAHE 1
            with colgraph1:
                col1_tin, col2_tin, col3_tin = st.columns([3,6,1])
                with col2_tin :
                    st.write("### Evolution du taux de fraude (%)")
                df_line = pd.DataFrame({
                        "Temps": range(len(st.session_state.history_fraude)),
                        "Taux (%)": st.session_state.history_fraude
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
            st.divider()         
    #time.sleep(1)

        
#--------Page performance modèle

@st.fragment(run_every=1)
def page_performance_modele():
    reload_data = get_reload()
    
    # Notif
    
    if reload_data and reload_data.get("status") == "success":
        new_id = reload_data.get("version_id")
        if "current_version_id" not in st.session_state:
            st.session_state.current_version_id = new_id
        elif new_id != st.session_state.current_version_id:
            st.toast(f"Modèle XGBoost réentraîné ! ({reload_data['modele_du']})", icon="✅")
            st.session_state.current_version_id = new_id 
    
    coltitle1, coltitle2, coltitle3 = st.columns([4,6,2])
    with coltitle2:
        st.title("Performance du modèle")
    coltitlee1, coltitlee2, coltitlee3 = st.columns([6.2,5.5,7])
    with coltitlee2:
        if reload_data and reload_data.get("status") == "success":
            st.info(f"🛡️ **Modèle en production** | Version du : {reload_data['modele_du']}")
        
    st.divider()
    
    # Récupération des données
    report = get_report()
    
    if report:
        m = report["matrix"]
        
        # Calcul des métriques globales 
        total_f = m["vrais_positifs"] + m["faux_negatifs"]
        recall = (m["vrais_positifs"] / total_f * 100) if total_f > 0 else 0
        precision = (m["vrais_positifs"] / (m["vrais_positifs"] + m["faux_positifs"]) * 100) if (m["vrais_positifs"] + m["faux_positifs"]) > 0 else 0
        f1_score = (2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0
        taux_fp = (m["faux_positifs"] / (m["faux_positifs"] + m["vrais_negatifs"]) * 100) if (m["faux_positifs"] + m["vrais_negatifs"]) > 0 else 0
        
        # Matrice confusion ---
        col1nn,col2nn, col3nn = st.columns([4,6,1])
        with col2nn:
            st.subheader("Matrice de confusion du modèle")
        st.write(" ")   
            
        col1, col2 = st.columns(2)            
        with col1:
            metric_card("VRAIS NÉGATIFS (SAINS)", format_metriques(m["vrais_negatifs"]), color="#d4edda") 
            metric_card("FAUX NÉGATIFS (RATÉS)", format_metriques(m["faux_negatifs"]), color="#f8d7da")  
            
        with col2:
            metric_card("FAUX POSITIFS (ALERTES)", format_metriques(m["faux_positifs"]), color="#fff3cd") 
            metric_card("VRAIS POSITIFS (FRAUDES)", format_metriques(m["vrais_positifs"]), color="#d1ecf1") 
            
        # Affichage Métriques Globales ---
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
            metric_card(label="🛡️ Taux FP", value=f"{taux_fp:.2f}%", color="#d1ecf1")        # Affichage Métriques Globales ---
        
        # explications 
        st.write("")
        st.write(" ")
        with st.expander("ℹ️ Comprendre ces indicateurs", expanded = True):
            st.markdown(f"""
            * **Recall ({recall:.2f}%)** : Sur 100 tentatives de fraude, le système en stoppe **{int(recall)}**. C'est l'indicateur de protection contre la fraude.
            * **Précision ({precision:.2f}%)** : Une alerte sur **{int(100/precision) if precision > 0 else 0}** est une vraie fraude. Cela représente l'efficacité du modèle.
            * **F1-Score ({f1_score:.2f}%)** : C'est la moyenne équilibrée entre la détection (Recall) et la fiabilité (Précision).
            * **Taux de Faux Positifs ({taux_fp:.2f}%)** : Seuls **{taux_fp:.2f}%** des clients honnêtes sont impactés.
            """)
            
        st.divider()
        
        # --- Historique des version ---
        col_h1, col_h2, col_h3 = st.columns([4.3,6,1])
        with col_h2:
            st.subheader("Comparatif des versions")
        st.write(" ")

        if "history" in report and report["history"]:
            data_clean = []
            for version in report["history"]:
                row = {
                    "Version": version["version_id"],
                    "Recall (%)": version["metrics"]["recall"],
                    "Précision (%)": version["metrics"]["precision"],
                    "F1-Score (%)": version["metrics"]["f1"],
                    "Accuracy (%)": version["metrics"]["accuracy"]
                }
                data_clean.append(row)
            
            # Affichage du DataFrame
            # Création de la palette Pastel (Rouge -> Jaune -> Vert)
            # Hex codes: Rouge pastel (#ffb3ba), Jaune pastel (#ffffba), Vert pastel (#baffc9)
            colors = ["#ffb3ba", "#ffffba", "#baffc9"]
            cmap_pastel = mcolors.LinearSegmentedColormap.from_list("pastel_rdylgn", colors)
            df_history = pd.DataFrame(data_clean)
            st.dataframe(
                df_history.style
                .format("{:.2f}", subset=["Recall (%)", "Précision (%)", "F1-Score (%)", "Accuracy (%)"]) # Force 2 décimales
                .background_gradient(cmap=cmap_pastel, subset=["Recall (%)", "F1-Score (%)"]),
                use_container_width=True,
                hide_index=True
            )
            st.write("")
            
            with st.expander("ℹ️ Pourquoi ces écarts ? Comprendre les métriques et l'échantillon"):
                st.markdown("""
                ##### 1. Périmètre de l'évaluation (Phase de réentraînement)
                Les scores affichés dans le tableau comparatif sont calculés lors du réentraînement sur un échantillon de validation (20%). Cet échantillon est extrait d'un jeu de données hybride (200 000 transactions saines + l'intégralité des fraudes).
                
                Comme la proportion de fraudes est artificiellement élevée dans cet échantillon pour optimiser l'apprentissage, les scores théoriques y sont mécaniquement très hauts (Précision > 90%).

                ##### 2. Performance en conditions réelles
                Sur le flux en temps réel, la fraude est extrêmement rare. Pour éviter que le modèle ne devienne trop sensible à cause de son entraînement sur-échantillonné, nous appliquons un **coefficient d'ajustement de 0.05**.
                
                Cela explique la différence de précision : nous bridons volontairement la "paranoïa" du modèle pour garantir un **taux de faux positifs quasi nul**, privilégiant ainsi une expérience utilisateur fluide tout en maintenant une détection efficace.

                ##### 3. Stabilisation statistique
                Le volume de données joue également :
                * **Entraînement massif :** Basé sur l'historique de millions de transactions.
                * **Simulation actuelle :** Ne contient pour l'instant que quelques milliers de lignes.
                
                Les indicateurs statistiques s'affineront et se stabiliseront à mesure que le volume de données traitées augmentera.
                """)
            
        st.divider()    

##-------------------------------- EDA ----------------------------
def page_eda():
    title = "Présentation du projet"
    st.title(title, text_alignment="center")
    st.write("---")

    #---------------création des onglets
    onglet_projet, onglet_stack, onglet_eda, onglet_flux_de_donnees, onglet_equipe = st.tabs(["Le projet", "La stack", "L'analyse (EDA)", "Flux de données", "L'équipe",])
    
    with onglet_projet:
        
        (st.write(""))  
        col1title, col2title, col3title = st.columns([4,6,1])
        with col2title:
            st.markdown("### <u> Vision Business & storytelling</u>", unsafe_allow_html=True)
        (st.write(""))
        
        with st.expander("**Le constat : Une hémorragie financière**"): 
            st.markdown("""
            Imaginez une banque digitale en pleine expansion. Chaque jour, des milliers de clients effectuent des transactions cruciales depuis leur mobile. Cette ouverture numérique est devenue la cible privilégiée des réseaux criminels spécialisés dans le détournement de fonds. Pour notre institution, cette faille de sécurité se chiffrait par des pertes réelles de plusieurs centaines de millions d'euros par an.
            """)
        
        with st.expander("**La problématique : L'équilibre entre sécurité et fluidité**"):
            st.markdown("""
Le défi posé à notre équipe : stopper la fraude sans dégrader l'expérience utilisateur.

* **Rapidité** : La décision (bloquer ou autoriser) doit être rendue en quelques millisecondes pour ne pas ralentir le client.
* **Satisfaction Client** : Un "Faux Positif" (client honnête bloqué par erreur) est commercialement problématique et a un coût financier non négligeable.
    """)
            
        with st.expander("**La solution : Une architecture innovante de détection en temps réel**"):
            st.markdown("""
Plutôt qu'un modèle statique, nous avons conçu une infrastructure évolutive.

Grâce à notre pipeline MLOps, le système apprend en continu.
Dès que de nouvelles typologies de fraude apparaissent, le modèle se réentraîne automatiquement pour s'adapter aux nouvelles menaces, garantissant une protection toujours à jour.""")
            
        with st.expander("**Les résultats : Une efficacité prouvée**"):
            st.markdown("""
* **Le Bouclier (Recall de 87 %)** : Nous interceptons désormais la grande majorité des tentatives de fraude.

* **La fluidité client (Spécificité de 99,4 %)** : Nous garantissons une expérience sans problème. 99,4 % des transactions légitimes sont validées instantanément, minimisant ainsi le mécontentement client.

* **L'efficacité des alertes (Précision de 63 %)** : Sur l'ensemble des transactions bloquées pour suspicion, près de 2 sur 3 sont réellement des fraudes. Ce score élevé permet aux équipes de sécurité de se concentrer sur des menaces hautement probables plutôt que de traiter un volume ingérable de fausses alertes.""")
            
        with st.expander('**Note sur la simulation de la "Vérité Terrain"**'):   
            st.markdown("""Dans ce projet, les transactions envoyées vers BigQuery incluent la valeur réelle de fraude.

Pourquoi ce choix ? Dans un environnement bancaire réel, il existe un décalage temporel : le modèle prédit une fraude à l'instant T, et la confirmation réelle (le "retour client" ou le signalement) arrive plus tard.

Pour les besoins de la démonstration en temps réel et pour permettre au cycle d'auto-apprentissage (MLOps) de fonctionner de manière fluide, nous avons "compressé le temps". Nous simulons ce retour d'information instantanément afin de démontrer la capacité du pipeline à :

* Détecter l'apparition de nouveaux patterns.

* Déclencher un réentraînement automatique basé sur des données vérifiées.

* Comparer immédiatement la prédiction du modèle avec la réalité pour calculer les métriques de performance.""")


            
        st.write("---")
        
        col1title, col2title, col3title = st.columns([4.2,6,1])
        with col2title:
            st.markdown("### <u>Dataset et méthodologie</u>", unsafe_allow_html=True)           
        (st.write(""))
        
        st.markdown("##### <u> Aperçu du Dataset complet utilisé pour la détection de fraude :</u>", unsafe_allow_html=True)
        (st.write(""))
        col1_dataset, col2_dataset, col3_dataset= st.columns(3)
        with col1_dataset:
            metric_card("Dataframe de base", "6 353 307 lignes", color="#d1ecf1")           
        with col2_dataset:
            metric_card("Fraudes identifiées", "8 213", color="#d4edda")
        with col3_dataset:
            metric_card("Taux de fraude", "0.13 %", color="#e0c5d6")
        
        (st.write(""))
        st.markdown("##### <u>Séparation des données historiques pour l'entraînement et le flux temps réel (production)</u> :", unsafe_allow_html=True)
        (st.write(""))
        with st.expander("**Détails de la séparation des datasets**"):
            st.markdown("""
Pour simuler un environnement de production réel, nous avons créé un script pour segmenter les données :

* **90% (Historique)** : Utilisés pour l'entraînement initial et stockés comme base de référence.

* **10% (Flux Stream)** : Isolés pour simuler l'envoi de transactions ligne par ligne.

Cette méthode garantit que le modèle est testé sur des données qu'il n'a jamais rencontrées lors de sa phase d'apprentissage initiale.""")
        (st.write(""))
                                
        col1, col2, col3 = st.columns(3)
        with col1: 
            metric_card("Dataframe d'entraînement", "5 726 358 lignes", color="#d1ecf1")   
            metric_card("Dataframe de production", "636 262 lignes", color="#d1ecf1")         
        with col2:
            metric_card("Fraudes identifiées", "4 449", color="#d4edda")
            metric_card("Fraudes identifiées", "3 764", color="#d4edda")
        with col3:
            metric_card("Taux de fraude", "0.07 %", color="#e0c5d6")
            metric_card("Taux de fraude", "0.59 %", color="#e0c5d6")
            
        st.write("---")    
#-------------------ONGLET STACK TECHNIQUE-------------------------
    
    with onglet_stack:
        
        (st.write(""))   
        col1title, col2title, col3title = st.columns([5,6,1])
        with col2title:
            st.markdown("### <u>Stack Technique</u>", unsafe_allow_html=True)
        (st.write("")) 
        (st.write("")) 
    
        row1_col1, row1_col2, row1_col3 = st.columns(3)

        with row1_col1:
            with st.container(border=True):
                _, centre, _ = st.columns([1.5, 2, 1])
                with centre: st.image("images/fastapi.png", width=180)
                st.markdown("**Communication** : Reçoit les flux et interroge le modèle. Il renvoie le verdict instantanément avant d'envoyer les données vers Redis.")

        with row1_col2:
            with st.container(border=True):
                st.write(" ")
                st.write(" ")
                _, centre, _ = st.columns([1.5, 2, 1])

                with centre: st.image("images/redis.png", width=115)
                st.write(" ")
                st.write(" ")
                st.markdown("**Mémoire Vive** : Stocke temporairement les données pour absorber les pics de charge et garantir qu'aucune transaction n'est perdue.")


        with row1_col3:
            with st.container(border=True):
                _, centre, _ = st.columns([1, 2, 1])
                with centre: st.image("images/bigquery.png", width=180)
                st.markdown("**Cloud** : Archive l'historique complet des transactions pour permettre le réentraînement régulier du modèle XGBoost.")


        row2_col1, row2_col2, row2_col3 = st.columns(3)

        with row2_col1:
            with st.container(border=True):
                _, centre, _ = st.columns([1.5, 2, 1])
                with centre: st.image("images/grafana.png", width=175)
                st.markdown("**Monitoring** : Visualise en temps réel la santé de l'infrastructure et l'état des flux de données via des dashboards interactifs.")

        with row2_col2:
            with st.container(border=True):
                st.write(" ")
                _, centre, _ = st.columns([1.5, 2, 1])
                with centre: st.image("images/prometheus.png", width=160)
                st.markdown("**Collecteur** : Interroge chaque service pour récupérer les métriques (CPU, RAM, latence) et les fournir à Grafana.")

        with row2_col3:
            with st.container(border=True):
                st.write(" ")
                st.write(" ")
                st.write(" ")
                _, centre, _ = st.columns([1.2, 2, 1])
                with centre: 
                    st.image("images/xgboost.png", width=180)
                    st.write(" ")
                    st.write(" ")
                    st.write(" ")
                    st.write(" ")
                st.markdown("**Intelligence** : Modèle de ML (Gradient Boosting) qui analyse les patterns complexes pour calculer la probabilité de fraude.")

        # --- LIGNE 3 : OPS & VITRINE ---
        row3_col1, row3_col2, row3_col3 = st.columns(3)

        with row3_col1:
            with st.container(border=True):
                st.write(" ")
                st.write(" ")
                st.write(" ")
                _, centre, _ = st.columns([1.5, 2, 1])
                with centre: 
                    st.write(" ")
                    st.image("images/docker.png", width=160)
                    st.write(" ")
                    st.write(" ")
                    st.write(" ")
                    st.write(" ")
                st.markdown("**Docker** : Garantit une exécution homogène et isolée de chaque service dans n'importe quel environnement.")
                st.write(" ")

        with row3_col2:
            with st.container(border=True):
                _, centre, _ = st.columns([1, 2, 1])
                with centre: st.image("images/streamlit.png", width=180)
                st.markdown("**Vitrine** : Interface interactive permettant de présenter les résultats, les fraudes et les mètriques clés du modèle.")

        with row3_col3:
            with st.container(border=True):
                st.write(" ")
                _, centre, _ = st.columns([1.5, 2, 1])
                with centre: 
                    st.image("images/prefect.png", width=140)
                    st.write(" ")
                    st.write(" ")
                st.markdown("**Prefect** : Orchestre et automatise le pipeline de données et le cycle de réentraînement du modèle.")
            
    with onglet_eda:
        (st.write(""))   
        col1title, col2title, col3title = st.columns([5,6,3])
        with col2title:
            st.markdown("### <u>Analyse exploratoire des données</u>", unsafe_allow_html=True)
        (st.write(""))
        st.markdown("Voici un résumé des principales découvertes issues de notre analyse exploratoire des données (EDA) sur le dataframe d'entrainement du modèle.")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.write("")
                st.write("")
                st.write("")
                st.write(" ")
                st.write("")
                st.image("images/bar_chart_types.png")
                st.write("")
                st.write("")
                st.write("")
                st.write(" ")
                st.write("")
                st.markdown("##### 1. Répartition des fraudes par type de transaction")
                st.markdown("Les fraudes sont inégalement réparties selon le type de transaction. Les types 'TRANSFER' et 'CASH_OUT' représentent la majorité des fraudes détectées, suggérant que les fraudeurs privilégient ces méthodes pour leurs activités illicites.")

        with col2:      
            with st.container(border=True):
                st.image("images/pie_chart_fraude.png", width=715)
                st.markdown("##### 2. Proportion de transactions frauduleuses")
                st.markdown("Le graphique circulaire montre que les transactions frauduleuses sur les données de productions constituent une très faible proportion du total des transactions (0.1%).")
                st.write("")
            

        col1a, col2a = st.columns(2)
        with col1a:
            with st.container(border=True):
                st.write(" ")
                st.write(" ")
                st.image("images/histplot_heures.png", width=1200)
                st.write(" ")
                st.write(" ")
                st.write(" ")
                st.write(" ")
                st.markdown("##### 3. Distribution des fraudes par heure de la journée")
                st.markdown("L'analyse horaire révèle que les fraudes n'ont pas de période spécifique dans la journée. Peut-être en raison de la nature automatisée des attaques, les fraudeurs opèrent à toute heure, rendant la détection basée sur le temps plus complexe.")

        with col2a:
            with st.container(border=True):
                st.write(" ")
                st.write(" ")
                st.write(" ")
                st.image("images/histogramme_final.png", width=705)
                st.markdown("##### 4. Montants des fraudes par type de transaction")
                st.markdown("""
L'analyse de la distribution montre que la majorité des fraudes porte sur des montants significatifs, 
avec un pic marqué entre **100 000 € et 1 000 000 €**. La présence d'une barre isolée à l'extrémité droite 
suggère l'existence d'un **plafond transactionnel** fréquemment atteint par les fraudeurs.
""")  

# --------------------------- ONGLET FLUX DE DONNEES ----------------------------- 

    with onglet_flux_de_donnees:
        (st.write(""))
        with st.container(border=True, horizontal_alignment="center"):   
            st.markdown("### <u> Flux de données</u>", text_alignment="center", unsafe_allow_html=True)
            st.write("")
            st.markdown("#### Architecture du pipeline de détection de fraude en temps réel", text_alignment="center", unsafe_allow_html=True)
            st.image("images/pipeline2.png", width=1000)

# --------------------------- ONGLET L'EQUIPE -----------------------------

    with onglet_equipe:
        (st.write(""))   
        col1title, col2title, col3title = st.columns([6,6,1])
        with col2title:
            st.markdown("### <u>L'équipe</u>", unsafe_allow_html=True)
        (st.write("")) 
        (st.write("")) 
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                _, centre, _ = st.columns([1, 2, 1])
                with centre:
                    st.image("images/kenji_victor.png", width=250)
                    st.markdown("**Kenji VICTOR**  \n ###### Streamlit, Grafana & Prometheus, FastAPI  \n")
                    st.markdown("###### [LinkedIn](https://www.linkedin.com/in/kenji-victor/)")
                    st.write("")
                    st.write("")
        with col2: 
            with st.container(border=True):     
                _, centre, _ = st.columns([1, 2, 1])
                with centre:
                    st.image("images/frederic_bayen.png", width=250)
                    st.markdown("**Frédéric BAYEN**  \n ###### Architecture MLOps, Bigquery, Streamlit, FastAPI & Automatisation \n")
                    st.markdown("###### [LinkedIn](https://www.linkedin.com/in/fr%C3%A9d%C3%A9ric-bayen/)")
                    st.write("")
        with col3: 
            with st.container(border=True):     
                _, centre, _ = st.columns([1, 2, 1])
                with centre:
                    st.image("images/jb_leduc.jpg", width=250)
                    st.markdown("**Jean-Baptiste LEDUC**  \n ###### Data Visualization, Streamlit Dashboards, Buffer Redis, Modélisation XGBoost \n")
                    st.markdown("###### [LinkedIn](https://www.linkedin.com/in/leduc-jean-baptiste/)")
                    st.write("")

#------------Navigation des pages


if page_selection == "Tableau de bord":
    page_stats()
elif page_selection == "Performance du modèle":
    page_performance_modele()
elif page_selection == "Le projet":
    page_eda()

if page_selection == "Tableau de bord":
    page_stats()
elif page_selection == "Performance du modèle":
    page_performance_modele()
