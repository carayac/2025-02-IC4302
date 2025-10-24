# build-helm.ps1
# Uso: .\build-helm.ps1

# Ir a bootstrap y actualizar dependencias
Set-Location bootstrap
Remove-Item -Force Chart.lock -ErrorAction SilentlyContinue
helm dependency update
Set-Location ..

helm upgrade --install bootstrap bootstrap

Start-Sleep -Seconds 20

# Ir a databases y actualizar dependencias
Set-Location databases
Remove-Item -Force Chart.lock -ErrorAction SilentlyContinue
helm dependency update
Set-Location ..

helm upgrade --install databases databases

Start-Sleep -Seconds 60

# Actualizar aplicación
helm upgrade --install application application