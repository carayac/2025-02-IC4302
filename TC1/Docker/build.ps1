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

#-------------------------CHROMADB ----------------------------
# Ir a la carpeta Chroma-Redis
Set-Location ../Chroma-Redis
# Construir la imagen
docker build -t "$Username/chroma-redis" .
# Subir la imagen
docker push "$Username/chroma-redis"

#Carperta de Chroma-Memcached
Set-Location ../Chroma-Memcached
# Construir la imagen
docker build -t "$Username/chroma-memcached" .
# Subir la imagen
docker push "$Username/chroma-memcached"

#Carperta de ChromaDB
Set-Location ../ChromaDB
# Construir la imagen
docker build -t "$Username/chromadb" .
# Subir la imagen
docker push "$Username/chromadb"

#-------------------------FIN CHROMADB ----------------------------

# Volver a la carpeta inicial
Set-Location ../..