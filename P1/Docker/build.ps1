param (
    [Parameter(Mandatory = $true)]
    [string]$Username
)

# Login a Docker
docker login

<# # Ir a la carpeta FlaskApp
Set-Location FlaskApp

# Construir la imagen
docker build -t "$Username/flask-example" .

# Subir la imagen
docker push "$Username/flask-example" #>
#----------------------------------------Backend UI----------------------------------------
Set-Location BackendUI
docker build -t "$Username/backend-ui" .
docker push "$Username/backend-ui"

#--------------------------------Backend UI Memcached----------------------------------------
Set-Location ../BackendUIMemcached
docker build -t "$Username/backend-ui-memcached" .
docker push "$Username/backend-ui-memcached"


#----------------------------------------UI ----------------------------------------
Set-Location ../FrontendUI
docker build -t "$Username/frontend-ui" .
docker push "$Username/frontend-ui"
#----------------------------------------S3 Crawler----------------------------------------
Set-Location ../S3Crawler
docker build -t "$Username/s3-crawler" .
docker push "$Username/s3-crawler"

#----------------------------------------Ingest----------------------------------------
Set-Location ../Ingest
docker build -t "$Username/ingest" .
docker push "$Username/ingest"

#----------------------------------------Spark Huggingface----------------------------------------
Set-Location ../HuggingFace
docker build -t "$Username/huggingface" .
docker push "$Username/huggingface"

# Volver a la carpeta inicial
Set-Location ../..