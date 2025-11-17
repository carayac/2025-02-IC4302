# install-helm.ps1
# Uso: .\install-helm.ps1

# Instalar chart 'bootstrap'
Set-Location bootstrap
Remove-Item -Force Chart.lock -ErrorAction SilentlyContinue
helm dependency update
Set-Location ..
helm upgrade --install bootstrap bootstrap

Start-Sleep -Seconds 20

# Instalar chart 'databases'
Set-Location databases
Remove-Item -Force Chart.lock -ErrorAction SilentlyContinue
helm dependency update
Set-Location ..
helm upgrade --install databases databases

Start-Sleep -Seconds 20

# Instalar chart 'app'
Set-Location app
Remove-Item -Force Chart.lock -ErrorAction SilentlyContinue
helm dependency update
Set-Location ..
helm upgrade --install app app
