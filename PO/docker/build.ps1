# $args[0] es el nombre de usuario pasado como parámetro
# Ejemplo de uso: .\build-and-push.ps1 usuarioDocker

docker login



Set-Location spark-job
docker build -t "$($args[0])/spark-job" .
docker push "$($args[0])/spark-job"

