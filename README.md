
# Application de détection de fraude à la carte bancaire
Ce projet est réalisé dans le cadre de la formation DATA ANALYST de la WILD CODE SCHOOL.

# Lancement Fast api
1. Lancement du serveur : `uv run uvicorn src/API/streamrecepteur:app --reload`
2. Envoi des requêtes : `python src/API/streamenvoi.py`
3. Acceder au rapport du nombre de fraudes en temps réel : `http://{serverURI}:{serverPort}/report`



# Structure du projet
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