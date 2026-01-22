[ SOURCE : Ton Ordinateur ]
      |
      | (1) Lecture ligne par ligne
      v
+-----------------------+       +-----------------------+
|   streamenvoi.py      | <---> |     pointer.txt       |  (Sauvegarde la progression
|   (L'Émetteur)        |       |    (Le Marque-page)   |   pour éviter les doublons)
+-----------------------+       +-----------------------+
      |
      | (2) Envoi des données (Requête POST /predict)
      v
[ CERVEAU : Docker - API ]
+-----------------------+       +-----------------------+
|  streamrecepteur.py   | ----> |    Modèle XGBoost     |  (Analyse la transaction
|     (FastAPI)         | <---- |     (Intelligence)    |   et rend un verdict)
+-----------------------+       +-----------------------+
      |
      | (3) Stockage des résultats (LPUSH)
      v
[ STOCKAGE : Docker - Redis ]
+-------------------------------------------------------+
|                     REDIS (Cache)                     |
|  - Liste "flux_global" : Toutes les transactions      |  (Données persistantes
|  - Liste "liste_fraudes" : Uniquement les alertes     |   grâce au Volume Docker)
+-------------------------------------------------------+
      |                               |
      | (4a) Lecture (GET /report)     | (4b) Extraction (RPOP)
      v                               v
[ VISUALISATION : Docker ]      [ ARCHIVAGE : Docker ]
+-----------------------+       +-----------------------+
|     dashboard.py      |       |    worker_bq.py       |
|      (Streamlit)      |       |      (Worker)         |
|  (Affiche les KPIs)   |       | (Envoi vers BigQuery) |
+-----------------------+       +-----------------------+