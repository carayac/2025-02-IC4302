param (
    [Parameter(Mandatory = $true)]
    [string]$Username
)

# Login a Docker
docker login

# Ir a la carpeta FlaskApp
Set-Location FlaskApp

# Construir la imagen
docker build -t "$Username/flask-example" .
# Subir la imagen
docker push "$Username/flask-example"

#INSTALACION DE IMAGENES DE CHROMA----------------------------------------------------------------
#CHROMA-REDIS
# Ir a la carpeta Chroma-Redis
Set-Location ../Chroma-Redis
# Construir la imagen
docker build -t "$Username/chroma-redis" .
# Subir la imagen
docker push "$Username/chroma-redis"

