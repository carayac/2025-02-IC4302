#!/bin/bash
USERNAME=$1

# Login a Docker
docker login

# ---------------------------------------- BeautifulSoup ----------------------------------------
cd BeautifulSoup || exit
docker build -t "$USERNAME/beautiful-soup" .
docker push "$USERNAME/beautiful-soup"
cd ..

# # ----------------------------------------Controller----------------------------------------
cd Controller || exit
docker build -t "$USERNAME/controller" .
docker push "$USERNAME/controller"
cd ..

# # # ---------------------------------------- Spacy Entity Extractor ----------------------------------------
cd SpacyEntityExtractor || exit
docker build -t "$USERNAME/spacy-entity-extractor" .
docker push "$USERNAME/spacy-entity-extractor"
cd ..

# # ---------------------------------------- Spark Processor Job ----------------------------------------
cd SparkProcessorJob || exit
docker build -t "$USERNAME/spark-processor-job" .
docker push "$USERNAME/spark-processor-job"
cd ..

