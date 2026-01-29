
# Détection de fraude bancaire en temps réel

Ce projet a été réalisé dans le cadre de la formation Data Analyst à la Wild Code School. Il simule un flux de transactions bancaires, les analyse via un modèle de Machine Learning (XGBoost) et monitore les performances en temps réel.

## L'Équipe
* **Frédéric Bayen** - *Architecture MLOps, Bigquery, Streamlit, FastAPI & Automatisation*
* **Kenji Victor** - *Streamlit, Grafana & Prometheus, FastAPI*
* **Jean-Baptiste Leduc** - *Data Visualization, Streamlit Dashboards, Redis & Modélisation XGBoost*

## Vision Business & storytelling

**Le constat : Une hémorragie financière**

Imaginez une banque digitale en pleine expansion. Chaque jour, des milliers de clients effectuent des transactions cruciales depuis leur mobile. Cette ouverture numérique est devenue la cible privilégiée des réseaux criminels spécialisés dans le détournement de fonds. Pour notre institution, cette faille de sécurité se chiffrait par des pertes réelles de **plusieurs centaines de millions d'euros par an.**


**La problématique : L'équilibre entre sécurité et fluidité**

Le défi posé à notre équipe : stopper la fraude sans dégrader l'expérience utilisateur.

 - **Rapidité absolue** : La décision (bloquer ou autoriser) doit tomber en quelques millisecondes pour ne pas ralentir le client.

 - **Satisfaction Client** : Un "Faux Positif" (client honnête bloqué par erreur) est une catastrophe commerciale et a un coût financier non négligeable.


**La Solution : Un système vivant et auto-adaptatif**

Plutôt qu'un modèle statique, nous avons conçu une infrastructure évolutive. Grâce à notre pipeline MLOps, le système apprend en continu. Dès que de nouvelles typologies de fraude apparaissent, le modèle se réentraîne automatiquement pour s'adapter aux nouvelles menaces, garantissant une protection toujours à jour.


**Le Pilotage**

Pour garder un contrôle total sur la solution, nous avons déployé deux centres de commandement :

 - Pour garder le contrôle, nous avons développé un **panneau de suivi Streamlit**. Il permet de visualiser les flux en temps réel, d'analyser les comportements suspects et de piloter la stratégie de sécurité de la banque. C'est ici que l'intelligence artificielle rencontre l'humaine.

 - **La supervision infrastructure (Grafana & Prometheus)** : Fidèle aux standards du Data Engineering, cette interface surveille la santé technique du système. Nous suivons en temps réel la consommation CPU/RAM de chaque conteneur et la latence de l'API pour garantir une haute disponibilité et des performances constantes sous la charge.


**La Victoire sur la fraude**

1. **Le Bouclier (Recall de 87 %)** : Nous interceptons désormais la grande majorité des tentatives de fraude.

2. **Le Respect du Client (Précision de 63 %)** : Nous protégeons 99,4 % de nos clients honnêtes, tout en ciblant avec précision les fraudeurs.

---

## Architecture du Pipeline

L'application repose sur une architecture micro-services conteneurisée avec Docker.

```text
[ SOURCE : Données CSV ]
      |
      | Lecture (streamenvoi.py)
      v
[ CERVEAU : Docker - API ] <---------------------------+
+-----------------------+       +-------------------+  |
|  streamrecepteur.py   | ----> |  ML_XGBoost.ipynb |  | 
|     (FastAPI)         | <---- |  Modèle XGBoost   |  |    
+-----------------------+       +-------------------+  |
      |                                                |
      | Résultats (LPUSH)                              |
      v                                                |
[ STOCKAGE : Redis ]                                   |
+------------------------------------------+           |
|              REDIS (Cache)               |           |
|  - flux_global (Archive BigQuery)        |           |
|  - flux_streamlit (Affichage direct)     |           |
+------------------------------------------+           |
      |                     |                          |
      |                     | Archivage                |
      |                     v                          |
      |                +-------------------+    [ MLOPS : Prefect ]
      |                |   worker_bq.py    |    +-----------------+
      |                | (Envoi BigQuery)  |--->|  retrain.py     |
      |  Monitoring    +-------------------+    |  (Auto-Train)   |
      v                                         +-----------------+
      +----------------------------------------------------------+
      |                                                          |     
      v                                                          v
[ SUPERVISION : Prometheus & Grafana ]             [ TABLEAU DE BORD : Streamlit]
+------------------------------------------+    +------------------------------------------+
| - Metrics système (CPU/RAM conteneurs)   |    | dashboard.py                             |
| - Metrics business (Taux de fraude)      |    | - Dashboarding & Alerting Temps Réel     |
| - Dashboarding & Alerting Temps Réel     |    | - EDA                                    |
+------------------------------------------+    +------------------------------------------+
```

---

## Gestion des données

Le projet utilise le dataset PaySim [(disponible ici sur Kaggle)](https://www.kaggle.com/datasets/mtalaltariq/paysim-data).

Pour simuler un environnement de production réel, nous avons créé un script ```decoupe.py``` pour segmenter les données :

 - **90% (Historique)** : Utilisés pour l'entraînement initial et stockés comme base de référence.

 - **10% (Flux Stream)** : Isolés pour simuler l'envoi de transactions ligne par ligne par streamenvoi.py.

Cette méthode garantit que le modèle est testé sur des données qu'il n'a jamais rencontrées lors de sa phase d'apprentissage initiale.

---

## Lancement rapide

**Prérequis**

   - Docker & Docker Compose installés.

   - Clé Google Cloud ```gcp-key.json``` à la racine pour l'accès à BigQuery.

   - Dataset ```PaySim_stream.csv``` et ```PaySim_historical.csv``` dans le dossier ./data/ récupérés grâce à ```decoupe.py```



**Installation**

1. **Cloner le projet.**

2. **Lancer l'infrastructure :**

      ```docker compose up --build```



**Accès aux services**

 - **Dashboard Streamlit** : http://localhost:8501

 - **Documentation API** : http://localhost:8000/docs / http://localhost:8000/report / http://localhost:8000/reload

 - **Monitoring Grafana** : http://localhost:3000

 - **Prometheus** : http://localhost:9090

 - **Processus de réentrainement** : ```docker logs -f retrain-automation```

---

## Performance du modèle (XGBoost)

Compte tenu du fort déséquilibre des données (99,4 % de transactions saines vs 0,6 % de fraudes), l'Accuracy (précision globale) n'est pas un indicateur pertinent. Nous nous concentrons sur la capacité du modèle à détecter les fraudes réelles.

**Résultats sur le Test Set de la v1**

Métrique|Valeur|Interprétation
| :--- | :--- | :--- |
| **Recall** | 87 % | Le modèle identifie avec succès 87 % des tentatives de fraude. | 
|** Précision ** | 63 % | Lorsqu'on prédit une fraude, elle est réelle dans 63 % des cas. | 
|** F1-Score ** | 0.73 | Un excellent équilibre pour un système de détection en temps réel. | 

---

## Automatisation MLOps

Le conteneur retrain-automation surveille la table BigQuery via Prefect.

 - Modularité : Le seuil de déclenchement (```min_rows_to_retrain```), le nombre de transactions récupéres sur BigQuery  (```limit_sql```) et l'intervalle de vérification (```check_interval_secondes```) sont modifiables sans redémarrage dans ```state.json```.

 - Action : Dès que le seuil est atteint, le modèle est réentraîné sur les nouvelles données, archivé, et l'API est notifiée pour charger la nouvelle version instantanément.

---

## Structure du dossier

```
├── data/                  # Datasets (CSV historiques et flux stream)
├── grafana/               # Configuration du monitoring
│   ├── dashboards/        # Fichiers JSON des dashboards (RAM, Principal, etc.)
│   └── provisioning/      # Configuration automatique des sources de données
├── notebooks/             # Travail exploratoire et recherche
│   ├── decoupe.py         # Script de split du dataset (90/10)
│   ├── EDA_PaySim.ipynb   # Analyse exploratoire des données
│   └── ML_XGBoost.ipynb   # Entraînement et tests du modèle
├── src/                   # Code source applicatif
│   ├── API/               # streamrecepteur (FastAPI), streamenvoi et worker_bq
│   ├── dashboard/         # Interface utilisateur Streamlit (dashboard.py)
│   ├── ingestion/         # Scripts de traitement des données
│   ├── models/            # Fichiers .joblib (pipeline_latest, archives)
│   └── retrain/           # Automatisation MLOps (retrain.py)
├── docker-compose.yml     # Orchestration des services Docker
├── Dockerfile             # Configuration de l'image Python/UV
├── prometheus.yml         # Configuration de la collecte des métriques
├── state.json             # État dynamique et configuration du réentraînement
└── README.md              # Documentation du projet
```

---

## Maintenance et réinitialisation

Pour remettre le projet à zéro :

1. Vider Redis (les conteneurs doivent être allumés): ```docker exec -it redis-service redis-cli FLUSHALL```

2. Vider BigQuery : ```TRUNCATE TABLE paysim_raw.predictions_transaction```

3. Reset l'automation : Mettre ```last_count``` à 0 dans le fichier ```state.json```.

---

## Problèmes rencontrés & solutions apportées


| Défi Technique | Impact | Solution apportée |
| :--- | :--- | :--- |
| **Déséquilibre des classes** | Dataset à 0.6% de fraudes, biaisant fortement les prédictions initiales. | Utilisation de `scale_pos_weight` calculé dynamiquement sur le ratio réel Fraude/Normal lors du réentraînement. |
| **Performance de l'entraînement** | RandomForest trop lent pour l'optimisation par GridSearch (estimé à plusieurs mois). | Passage à **XGBoost (CUDA/GPU)** et utilisation de **RandomizedSearch** pour une optimisation rapide. |
| **Affichage Temps Réel** | Interface Streamlit statique par défaut, ne reflétant pas le flux entrant. | Boucle `while True` avec placeholders `st.empty()` pour rafraîchir les KPIs sans rechargement de page. |
| **Saturation de Redis** | Réinitialisation du dashboard dû à chaque envoi sur BigQuery. | Mise en place d'un **double flux** : un flux persistant pour l'UI Streamlit et un autre pour l'archivage BigQuery. |
| **Choix de l'Orchestrateur** | Airflow s'est révélé trop complexe et gourmand en ressources pour ce projet. | Pivot vers **Prefect**, plus léger, moderne et parfaitement adapté à notre architecture événementielle. |
| **Apprentissage Docker** | Complexité des réseaux inter-conteneurs et des dépendances pour des novices. | Gestion rigoureuse des ordres de démarrage (`depends_on`) et isolation des réseaux internes (`networks`). |
| **Synchronisation du Pipeline** | Risque de charger un modèle incomplet pendant l'écriture disque. | Système de **notification Push** : l'API recharge le modèle via `/reload` uniquement après confirmation de sauvegarde complète. |
| **Data Leakage (Fuite)** | Score de performance artificiellement élevé (99.9%) via les variables `newbalance`. | **Suppression préventive** des variables "du futur" (`newbalanceOrig/Dest`). Le modèle n'utilise que le solde initial et le montant. |














# Prérequis

- **Docker** et **Docker Compose** installés sur votre machine.
- Le fichier de données `PaySim_stream.csv` et `PaySim_historical.csv` placé dans le dossier `./data/`.

# Lancement Fast api

1. **Cloner le projet**
2. **Lancer l'environnement avec Docker Compose :**

    ```
   docker compose up --build
    ```
   # arrêter le processus
    ```
   docker compose down
    ```
   # effacer le cache
    ```
   docker system prune -f
    ```

# Comment réinitialiser tout à 0 :

1. Lancer le container Redis

2. Excuter la commande : ``` docker exec -it redis-service redis-cli FLUSHALL ```

3. Fermer le container 

4. Lancer bigquery pour réionitialiser la table

5. Excuter la commande :  : ``` TRUNCATE TABLE paysim_raw.predictions_transaction ```

6. Mettre à jour le fichier src/retrain/lastcount : changer la valeur à 0




# Ouvrir streamlit

http://localhost:8501/ Dans la barre d'url'

# Afficher les rapports/docu API

http://localhost:8000/report

http://localhost:8000/docs


# poru lancer sans docker

uv run python src/API/streamrecepteur.py

uv run uvicorn src.API.streamrecepteur:app --reload --port 8000

# Pour vérifier le process de réentrainement du modèle : 

```
docker logs -f retrain-automation
```

# Structure du projet

```
fjbk-fraud-detection/
├── data/                  # Stockage des datasets bruts et transformés (ignorer via .gitignore)
├── docs/                  # Documentation technique et choix du dataset
├── /grafana               # Configuration du monitoring avec Grafana
│   ├── /dashboards        # Exports des dashboards depuis Grafana
│   └── /provisioning      # Configuration du provisioning
│       ├── /dashboards    # Fichiers de déclaration
│       └── /datasources   # Fichiers de sources de données
├── model/                 # Stockage modèle, preprocessor
├── notebooks/             # EDA et Visualisation 
├── src/                   # Code source modulaire
│   ├── ingestion/         # Scripts pour lire les données 
│   ├── API                # API
│   ├── processing/        # Nettoyage et Feature Engineering 
│   ├── models/            # Entraînement et évaluation (ML)
│   └── dashboard/         # Interface Streamlit 
├── tests/                 # Tests unitaires pour le pipeline 
├── requirements.txt       # Bibliothèques
└── README.md              # Guide du projet et méthodologie



# redis 

1. faire un uv lock afin de modifier le Dockerfile

2. pour se connecter au conteneur redis:
   => docker exec -it redis-service redis-cli
    
   pour lister les listes dans le redis 
   => KEYS *

   pour vider toutes les listes redis (les conteneurs doivent être allumés)
   => docker exec -it redis-service redis-cli FLUSHALL

3. lancer manuellement streamenvoi
   => python src/API/streamenvoi.py

4. pour afficher l'intégralité de la liste
   => LRANGE liste_fraudes 0 -1 

5. LOGS dans BASH: afin d'obtenir "ALERTE" dès que redis reçoit une fraude
   => docker-compose logs -f api-recepteur | grep "ALERTE"
   récupérer les LOGS worker-bigquery
   => docker logs -f worker-bigquery

6. pour arrêter les contenurs Docker:
   => docker-compose stop

   pour supprimer les volumes persistans (suppression aussi de la configuration redis)
   => docker-compose down -v

7. Supprimer dans bigquery : TRUNCATE TABLE `paysim_raw.predictions_transaction`
