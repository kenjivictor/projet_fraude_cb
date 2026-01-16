import streamlit as st
import requests
import pandas as pd
import time

# Configuration de la page
st.set_page_config(page_title="Anti-Fraud Monitor", layout="wide")

st.title("🛡️ Surveillance des Flux en Temps Réel")
st.markdown("---")

# Zone pour les statistiques globales qui s'actualisent
placeholder_metrics = st.empty()
placeholder_table = st.empty()

while True:
    try:
        # Récupération des données depuis ton API
        response = requests.get("http://127.0.0.1:8000/report")
        data = response.json()
        
        # On extrait la liste des fraudes
        liste_fraudes = data.get('details', [])
        nb_fraudes = data.get('nb_fraudes_detectees', 0)
        
        df = pd.DataFrame(liste_fraudes)

        # 1. Mise à jour des Metrics
        with placeholder_metrics.container():
            col1, col2, col3 = st.columns(3)
            
            col1.metric("🚨 Alertes Fraude", nb_fraudes)
            
            if not df.empty:
                total_montant = df['montant'].sum()
                moyenne = df['montant'].mean()
                col2.metric("💰 Total Intercepté", f"{total_montant:,.2f} €")
                col3.metric("📊 Moyenne / Fraude", f"{moyenne:,.2f} €")
            else:
                col2.metric("💰 Total Intercepté", "0.00 €")
                col3.metric("📊 Moyenne / Fraude", "0.00 €")

        # 2. Mise à jour du Tableau
        with placeholder_table.container():
            if not df.empty:
                st.subheader("📋 Journal des transactions suspectes")
                # On trie pour avoir les plus récentes (step le plus haut) en premier
                df_sorted = df.sort_values(by='step', ascending=False)
                
                # Affichage du tableau stylisé
                st.dataframe(
                    df_sorted, 
                    use_container_width=True,
                    column_config={
                        "step": "Heure (Step)",
                        "montant": st.column_config.NumberColumn("Montant (€)", format="%.2f"),
                        "client": "ID Client",
                        "type": "Type"
                    }
                )
                
                # Petit bonus : Graphique de répartition par type de transaction
                st.write("---")
                st.subheader("📈 Répartition des types de fraude")
                st.bar_chart(df['type'].value_counts())
            else:
                st.info("Aucune fraude détectée pour le moment. Le système analyse le flux...")

    except Exception as e:
        st.error(f"Erreur de connexion à l'API : {e}")
    
    # Rafraîchissement toutes les secondes
    time.sleep(1)