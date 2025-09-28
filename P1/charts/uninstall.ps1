
# Listar los releases de Helm
helm list

# Desinstalar aplicación
helm uninstall app
Start-Sleep -Seconds 15

#Desinstalar aplicación web
helm uninstall application-web
Start-Sleep -Seconds 15

# Desinstalar bases de datos
helm uninstall databases
Start-Sleep -Seconds 60

