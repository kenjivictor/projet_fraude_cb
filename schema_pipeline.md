[ SOURCE : Ton Ordinateur ]
      |
      | (1) Lecture ligne par ligne
      v
+-----------------------+  
|   streamenvoi.py      | 
|   (L'émetteur)        |    
+-----------------------+    
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
+--------------------------------------------------------------+
|                     REDIS (Cache)                            |
|  - Liste "flux_global" : Toutes les transactions             |  (Données persistantes
|  - Liste "flux streamlit" : ASert a l'affichage Streamlit    |   grâce au Volume Docker)
+--------------------------------------------------------------+
      |                               |
      | (4a) Lecture (GET /report)     | (4b) Extraction (RPOP)
      v                               v
[ VISUALISATION : Docker ]      [ ARCHIVAGE : Docker ]
+-----------------------+       +-----------------------+
|     dashboard.py      |       |    worker_bq.py       |
|      (Streamlit)      |       |      (Worker)         |
|  (Affiche les KPIs)   |       | (Envoi vers BigQuery) |
+-----------------------+       +-----------------------+