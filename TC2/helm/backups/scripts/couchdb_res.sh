#!/bin/bash
set -e
yum install -y gzip jq

if aws s3 ls "s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz" &>/dev/null; then #si se elige backup escecifico y existe, restaura ese
    SELECTED="${BACKUP_NAME}.gz"
    SELECTED_NAME="$BACKUP_NAME"
else
    echo "ERROR: Elegir un nombre de archivo válido"
    exit 1
fi



mkdir -p /restore

aws s3 cp "s3://$BUCKET_NAME/$BACKUP_PATH/$SELECTED" "/restore/$SELECTED" #descarga el archivo




gunzip "/restore/$SELECTED" #descomprimir

curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X DELETE "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" || true #borrar la base de datos

until ! curl -sf -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
         "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" >/dev/null; do #esperar a que la base este completamente borrada
  sleep 1
done
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
     -X PUT "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB" #volver a crear la base de datos




jq '{new_edits: false, docs: [.rows[].doc]}' "/restore/$SELECTED_NAME" > "/restore/docs.json" #convierte a json
curl -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
  -X POST \
  -H "Content-Type: application/json" \
  --data-binary @/restore/docs.json \
  "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_bulk_docs" #sube la nueva info en bulk
