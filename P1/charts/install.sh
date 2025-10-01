#!/bin/bash
set -e

# bootstrap
cd bootstrap
rm -f Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install bootstrap bootstrap
sleep 20

# monitoring-stack
cd monitoring-stack
rm -f Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install monitoring-stack monitoring-stack
sleep 20

# databases
cd databases
rm -f Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install databases databases
sleep 60

# app
helm upgrade --install app app
sleep 20

# app UI
helm upgrade --install application-web application-web
sleep 20

# grafana-config
cd grafana-config
rm -f Chart.lock
rm -rf charts
helm dependency update
cd ..
helm upgrade --install grafana-config grafana-config
