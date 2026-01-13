
# Application de détection de fraude à la carte bancaire
Ce projet est réalisé dans le cadre de la formation DATA ANALYST de la WILD CODE SCHOOL.

# Lancement Fast api
streamenvoi.py : python src/API/streamenvoi.py
streamrecepteur.py : uv run uvicorn src/API/streamrecepteur:app --reload
Pour acceder au rapport du nombre de fraudes : http://127.0.0.1:8000/report



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