#!/bin/bash
set -e

# yum update -y

# cat <<EOT > /etc/yum.repos.d/mongodb-org-7.0.repo
# [mongodb-org-7.0]
# name=MongoDB Repository
# baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/7.0/x86_64/
# gpgcheck=1
# enabled=1
# gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
# EOT
# yum update -y
# yum install mongodb-database-tools -y
apk add --no-cache jq

mkdir -p /restore/$BACKUP_NAME

aws s3 cp s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz /restore/${BACKUP_NAME}.gz



gunzip /restore/${BACKUP_NAME}.gz #descomprime
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X DELETE "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" || true #se limpia antes de hacer restore
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X PUT "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB"


jq '{docs: [.rows[].doc]}' /restore/${BACKUP_NAME} > /restore/docs.json #el backup debe ser un json para ser aceptado por couchdb

curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @/restore/docs.json \
  "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_bulk_docs" #bulk_docs sube documentos en bulk