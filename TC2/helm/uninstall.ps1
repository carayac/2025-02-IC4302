# cleanup-helm.ps1
# Uso: .\cleanup-helm.ps1

# Mostrar lista de releases
helm list

# Desinstalar chart 'backups'
helm uninstall backups

Start-Sleep -Seconds 10

# Desinstalar chart 'app'
helm uninstall app

Start-Sleep -Seconds 10

# Desinstalar chart 'databases'
helm uninstall databases
Start-Sleep -Seconds 60

# Desinstalar chart 'bootstrap'
 helm uninstall bootstrap

