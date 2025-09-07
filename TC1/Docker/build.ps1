param (
    [Parameter(Mandatory = $true)]
    [string]$Username
)

# Login a Docker
docker login

# Ir a la carpeta FlaskApp
Set-Location FlaskApp

# Construir la imagen
docker build -t "$Username/flasktest" .

# Subir la imagen
docker push "$Username/flaskTest"

# Volver a la carpeta anterior
Set-Location ..
