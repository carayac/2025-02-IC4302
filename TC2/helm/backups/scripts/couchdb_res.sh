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

mkdir -p /restore/$BACKUP_NAME

aws s3 cp s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz /restore/${BACKUP_NAME}.gz

gunzip /restore/${BACKUP_NAME}.gz #descomprime

curl -X DELETE "http://$COUCHDB_USERNAME:$COUCHDB_PASSWORD@$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" #se limpia la bd antes de hacer restore
curl -X PUT    "http://$COUCHDB_USERNAME:$COUCHDB_PASSWORD@$COUCHDB_CONNECTION_STRING/$COUCHDB_DB"

curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @/restore/${BACKUP_NAME} \
  "http://$COUCHDB_USERNAME:$COUCHDB_PASSWORD@$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_bulk_docs" #bulk_docs sube documentos en bulk