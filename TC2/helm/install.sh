#!/bin/bash
set -e

# install-helm.sh
# Uso: ./install-helm.sh

# Instalar chart 'bootstrap'
cd bootstrap
rm -f Chart.lock
helm dependency update
cd ..
helm upgrade --install bootstrap bootstrap

sleep 20

# Instalar chart 'databases'
cd databases
rm -f Chart.lock
helm dependency update
cd ..
helm upgrade --install databases databases

sleep 20

# Instalar chart 'app'
cd app
rm -f Chart.lock
helm dependency update
cd ..
helm upgrade --install app app

sleep 20

# Instalar chart 'backups'
cd backups
rm -f Chart.lock
helm dependency update
cd ..
helm upgrade --install backups backups
