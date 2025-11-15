

cd bootstrap
rm -rf Chart.lock
helm dependency build --skip-refresh
cd ..
helm upgrade --install bootstrap bootstrap
sleep 20
cd databases
rm -rf Chart.lock
helm dependency build --skip-refresh
cd ..
helm upgrade --install databases databases

