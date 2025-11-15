

cd databases
helm uninstall databases
cd ..

cd bootstrap
helm uninstall bootstrap 
cd ..

kubectl delete pvc -l app.kubernetes.io/instance=databases --ignore-not-found