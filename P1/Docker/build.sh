#!/bin/bash
# $1 is the username

USERNAME=$1

if [ -z "$USERNAME" ]; then
  echo "Uso: ./build.sh <docker-username>"
  exit 1
fi

docker login



# cd FlaskApp
# docker build -t $1/flask-example .
# docker push $1/flask-example

#------------------------- S3 CRAWLER ----------------------------
cd S3Crawler
docker build -t "$USERNAME/s3-crawler" .
docker push "$USERNAME/s3-crawler"
cd ..
#-----------------------------------------------------------------
cd ..
echo "Todas las imágenes fueron construidas y subidas correctamente."