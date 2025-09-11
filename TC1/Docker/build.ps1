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

#-------------------------INICIO DATASEEDER ----------------------------
Set-Location ../DataSeeder
docker build -t "$Username/dataseeder" .
docker push "$Username/dataseeder"
#-------------------------FIN DATASEEDER ----------------------------


#-------------------------INICIO ELASTICSEARCH ----------------------------

# Ir a la carpeta general Elasticsearch
Set-Location ../ElasticSearchPackage

#Carpeta Elasticsearch
Set-Location ./Elasticsearch
docker build -t "$Username/elasticsearch" .
docker push "$Username/elasticsearch"

#-------------------------FIN ELASTICSEARCH ----------------------------



# Volver a la carpeta inicial
Set-Location ../..