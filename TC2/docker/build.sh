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

# #------------------------- DATASEEDER ----------------------------
# cd DataSeeder
# docker build -t "$USERNAME/dataseeder" .
# docker push "$USERNAME/dataseeder"
# cd ..
