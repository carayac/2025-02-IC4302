#!/bin/bash
set -e
yum install -y gzip jq

if aws s3 ls "s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz" &>/dev/null; then #si se elige backup escecifico y existe, restaura ese
    SELECTED="${BACKUP_NAME}.gz"
    SELECTED_NAME="$BACKUP_NAME"
else
    SELECTED=$(aws s3 ls "s3://$BUCKET_NAME/$BACKUP_PATH/" 2>/dev/null | tr -s ' ' | cut -d' ' -f4 | tail -n 1) #si no, se restaura el ultimo (se extrae solo el nombre de archivo quitando las demas columnas)
    SELECTED_NAME="${SELECTED%.gz}"
fi



mkdir -p /restore

aws s3 cp "s3://$BUCKET_NAME/$BACKUP_PATH/$SELECTED" "/restore/$SELECTED"




gunzip "/restore/$SELECTED"
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X DELETE "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" || true

until ! curl -sf -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
         "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" >/dev/null; do #esperar a que la base este completamente borrada
  sleep 1
done
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X PUT "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB"




jq '{new_edits: false, docs: [.rows[].doc]}' "/restore/$SELECTED_NAME" > "/restore/docs.json" #convierte a json
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
  -X POST \
  -H "Content-Type: application/json" \
  --data-binary @/restore/docs.json \
  "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_bulk_docs"
