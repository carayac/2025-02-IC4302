#!/bin/bash
set -e

# Uso: ./build-dataseeder.sh <USERNAME>

if [ -z "$1" ]; then
  echo "Error: Debes pasar el nombre de usuario de DockerHub."
  echo "Uso: ./build-dataseeder.sh <USERNAME>"
  exit 1
fi

USERNAME="$1"

# Login a Docker
docker login

# ------------------ INICIO DATASEEDER ------------------
cd DataSeeder
docker build -t "$USERNAME/dataseeder" .
docker push "$USERNAME/dataseeder"
cd ..
# ------------------ FIN DATASEEDER ------------------
