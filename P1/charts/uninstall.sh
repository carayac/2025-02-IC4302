#!/bin/bash
set -e

# Listar los releases de Helm
helm list

# Desinstalar aplicación
helm uninstall app
sleep 15

# Desinstalar aplicación web
helm uninstall application-web
sleep 15

# Desinstalar bases de datos
helm uninstall databases
sleep 60
