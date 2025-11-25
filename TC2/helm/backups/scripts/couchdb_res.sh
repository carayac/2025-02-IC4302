#!/bin/bash
set -e
yum install -y gzip jq

mkdir -p /restore/$BACKUP_NAME

aws s3 cp s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz /restore/${BACKUP_NAME}.gz



gunzip /restore/${BACKUP_NAME}.gz 
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X DELETE "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" || true
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X PUT "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB"


jq '{docs: [.rows[].doc]}' /restore/${BACKUP_NAME} > /restore/docs.json 

curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @/restore/docs.json \
  "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_bulk_docs" 