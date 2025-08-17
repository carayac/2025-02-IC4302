# uninstall-helm.ps1
# Uso: .\uninstall-helm.ps1

# Mostrar lista de releases
helm list

# Desinstalar application
helm uninstall application
Start-Sleep -Seconds 15

# Desinstalar databases
helm uninstall databases
Start-Sleep -Seconds 60

# Desinstalar bootstrap
helm uninstall bootstrap
