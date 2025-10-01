#!/bin/bash
USERNAME=$1

# Login a Docker
docker login

# ---------------------------------------- Backend UI ----------------------------------------
cd BackendUI || exit
docker build -t "$USERNAME/backend-ui" .
docker push "$USERNAME/backend-ui"

# # ---------------------------------------- UI ----------------------------------------
# cd FrontendUI || exit
# docker build -t "$USERNAME/frontend-ui" .
# docker push "$USERNAME/frontend-ui"

# ---------------------------------------- Ingest CSV ----------------------------------------
cd Ingest-CSV || exit
docker build -t "$USERNAME/ingest-csv" .
docker push "$USERNAME/ingest-csv"

# ---------------------------------------- Ingest Parquet ----------------------------------------
cd Ingest-Parket || exit
docker build -t "$USERNAME/ingest-parket" .
docker push "$USERNAME/ingest-parket"

# ---------------------------------------- Spark HuggingFace ----------------------------------------
cd HuggingFace || exit
docker build -t "$USERNAME/huggingface" .
docker push "$USERNAME/huggingface"

# ---------------------------------------- Volver a la carpeta inicial ----------------------------------------
cd ..
