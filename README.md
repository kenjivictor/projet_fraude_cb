
# Application de détection de fraude aux transactions bancaires en temps réel

Ce projet est un travail d'équipe réalisé dans le cadre de la formation DATA ANALYST de la WILD CODE SCHOOL.


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
   docker-compose down
    ```
   # effacer le cache
    ```
   docker system prune -f
    ```


# Ouvrir streamlit

http://localhost:8501/ Dans la barre d'url'

# Afficher les rapports/docu API

http://localhost:8000/report

http://localhost:8000/docs


# poru lancer sans docker

uv run python src/API/streamrecepteur.py
uv run uvicorn src.API.streamrecepteur:app --reload --port 8000

# Structure du projet

```
fjbk-fraud-detection/
├── data/               # Stockage des datasets bruts et transformés (ignorez via .gitignore)
├── docs/               # Documentation technique et choix du dataset
├── model/              # Stockage modèle, preprocessor
├── notebooks/          # EDA et Visualisation 
├── src/                # Code source modulaire
│   ├── ingestion/      # Scripts pour lire les données 
│   ├── API             # API
│   ├── processing/     # Nettoyage et Feature Engineering 
│   ├── models/         # Entraînement et évaluation (ML)
│   └── dashboard/      # Interface Streamlit 
├── tests/              # Tests unitaires pour le pipeline 
├── requirements.txt    # Bibliothèques
└── README.md           # Guide du projet et méthodologie



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
