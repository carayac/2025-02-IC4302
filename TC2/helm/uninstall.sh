#!/bin/bash
set -e

# cleanup-helm.sh
# Uso: ./cleanup-helm.sh

# Mostrar lista de releases
helm list

# Desinstalar chart 'backups'
helm uninstall backups
sleep 10

# Desinstalar chart 'app'
helm uninstall app
sleep 10

# Desinstalar chart 'databases'
helm uninstall databases
sleep 60

# Desinstalar chart 'bootstrap'
helm uninstall bootstrap
