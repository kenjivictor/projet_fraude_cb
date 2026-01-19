
# Application de détection de fraude à la carte bancaire

Ce projet est réalisé dans le cadre de la formation DATA ANALYST de la WILD CODE SCHOOL.


# Prérequis

- **Docker** et **Docker Compose** installés sur votre machine.
- Le fichier de données `PaySim_stream.csv` et `PaySim_historical.csv` placé dans le dossier `./data/`.

# Lancement Fast api

1. **Cloner le projet**
2. **Lancer l'environnement avec Docker Compose :**

    ```
   docker-compose up --build
    ```

# Ouvrir streamlit

http://localhost:8501/ Dans la barre d'url'

# Afficher les rapports/docu API

http://localhost:8000/report

http://localhost:8000/docs

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
```
