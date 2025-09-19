#!/bin/bash

set -e

# Verificar que se haya pasado el nombre de usuario
if [ -z "$1" ]; then
  echo "Uso: ./build.sh <docker-username>"
  exit 1
fi

USERNAME=$1

# Login a Docker
docker login

# #------------------------- FLASK APP ----------------------------
# cd FlaskApp
# docker build -t "$USERNAME/flask-example" .
# docker push "$USERNAME/flask-example"
# cd ..

# #------------------------- DATASEEDER ----------------------------
# cd DataSeeder
# docker build -t "$USERNAME/dataseeder" .
# docker push "$USERNAME/dataseeder"
# cd ..

# #------------------------- CHROMADB ----------------------------
# cd ChromaDBPackage/ChromaDB
# docker build -t "$USERNAME/chroma" .
# docker push "$USERNAME/chroma"
# cd ../Chroma-Memcached
# docker build -t "$USERNAME/chroma-memcached" .
# docker push "$USERNAME/chroma-memcached"
# cd ../Chroma-Redis
# docker build -t "$USERNAME/chroma-redis" .
# docker push "$USERNAME/chroma-redis"
# cd ../..

#------------------------- ELASTICSEARCH ----------------------------
cd ElasticSearchPackage/Elasticsearch
docker build -t "$USERNAME/elasticsearch" .
docker push "$USERNAME/elasticsearch"
#cd ../ElasticSearch-Memcached
#docker build -t "$USERNAME/elasticsearch-memcached" .
#docker push "$USERNAME/elasticsearch-memcached"
#cd ../ElasticSearch-Redis
#docker build -t "$USERNAME/elasticsearch-redis" .
#docker push "$USERNAME/elasticsearch-redis"
cd ../..

#------------------------- MARIA DB ----------------------------
# cd MariaDBPackage/MariaDB
# docker build -t "$USERNAME/mariadb" .
# docker push "$USERNAME/mariadb"
# cd ../MariaDB-Memcached
# docker build -t "$USERNAME/mariadb-memcached" .
# docker push "$USERNAME/mariadb-memcached"
# cd ../MariaDB-Redis
# docker build -t "$USERNAME/mariadb-redis" .
# docker push "$USERNAME/mariadb-redis"
# cd ../..

# #------------------------- POSTGRESQL ----------------------------
# cd PostgreSQLPackage/PostgreSQL
# docker build -t "$USERNAME/postgresql" .
# docker push "$USERNAME/postgresql"
# cd ../PostgreSQL-Memcached
# docker build -t "$USERNAME/postgresql-memcached" .
# docker push "$USERNAME/postgresql-memcached"
# cd ../PostgreSQL-Redis
# docker build -t "$USERNAME/postgresql-redis" .
# docker push "$USERNAME/postgresql-redis"
# cd ../..

# #------------------------- VESPA AI ----------------------------
# cd VespaAIPackage/VespaAI
# docker build -t "$USERNAME/vespaai" .
# docker push "$USERNAME/vespaai"
# cd ../VespaAI-Memcached
# docker build -t "$USERNAME/vespaai-memcached" .
# docker push "$USERNAME/vespaai-memcached"
# cd ../VespaAI-Redis
# docker build -t "$USERNAME/vespaai-redis" .
# docker push "$USERNAME/vespaai-redis"
# cd ../..

echo "Todas las imágenes fueron construidas y subidas correctamente."