#!/bin/bash

Username=$1

if [ -z "$Username" ]; then
    echo "Debe especificar un nombre de usuario de Docker"
    exit 1
fi

# Login a Docker
docker login

#-------------------------INICIO FLASKAPP ----------------------------
# cd FlaskApp
# docker build -t "$Username/flask-metrics" .
# docker push "$Username/flask-metrics"
# cd ..
#-------------------------FIN FLASKAPP ----------------------------

#-------------------------INICIO DATASEEDER ----------------------------
# cd DataSeeder
# docker build -t "$Username/dataseeder" .
# docker push "$Username/dataseeder"
# cd ..
#-------------------------FIN DATASEEDER ----------------------------

#-------------------------CHROMADB ----------------------------
# cd ChromaDBPackage/ChromaDB
# docker build -t "$Username/chroma" .
# docker push "$Username/chroma"
# cd ../Chroma-Memcached
# docker build -t "$Username/chroma-memcached" .
# docker push "$Username/chroma-memcached"
# cd ../Chroma-Redis
# docker build -t "$Username/chroma-redis" .
# docker push "$Username/chroma-redis"
# cd ../../
#-------------------------FIN CHROMADB ----------------------------

#-------------------------INICIO ELASTICSEARCH ----------------------------
cd ElasticSearchPackage/Elasticsearch
docker build -t "$Username/elasticsearch" .
docker push "$Username/elasticsearch"
cd ../../
#ElasticSearch-Memcached
# cd ElasticSearchPackage/ElasticSearch-Memcached
# docker build -t "$Username/elasticsearch-memcached" .
# docker push "$Username/elasticsearch-memcached"
# cd ../
#ElasticSearch-Redis
# cd ElasticSearchPackage/ElasticSearch-Redis
# docker build -t "$Username/elasticsearch-redis" .
# docker push "$Username/elasticsearch-redis"
# cd ../../
#-------------------------FIN ELASTICSEARCH ----------------------------

#-------------------------INICIO MARIA DB ----------------------------
# cd MariaDBPackage/MariaDB
# docker build -t "$Username/mariadb" .
# docker push "$Username/mariadb"
# cd ../MariaDB-Memcached
# docker build -t "$Username/mariadb-memcached" .
# docker push "$Username/mariadb-memcached"
# cd ../MariaDB-Redis
# docker build -t "$Username/mariadb-redis" .
# docker push "$Username/mariadb-redis"
# cd ../../
#-------------------------FIN MARIA DB ----------------------------

#-------------------------INICIO POSTGRESQL ----------------------------
# cd PostgreSQLPackage/PostgreSQL
# docker build -t "$Username/postgresql" .
# docker push "$Username/postgresql"
# cd ../PostgreSQL-Memcached
# docker build -t "$Username/postgresql-memcached" .
# docker push "$Username/postgresql-memcached"
# cd ../PostgreSQL-Redis
# docker build -t "$Username/postgresql-redis" .
# docker push "$Username/postgresql-redis"
# cd ../../
#-------------------------FIN POSTGRESQL ----------------------------

# Volver a la carpeta inicial
cd ../..
