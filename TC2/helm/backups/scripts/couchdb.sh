#!/bin/bash
yum install -y gzip

DATE=$(date '+%Y%m%d%H%M')
mkdir -p /couchdbdump/$DATE

curl -s -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
  "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_all_docs?include_docs=true&attachments=true" \ 
  > /couchdbdump/$DATE/${DATE}.json #extrae todos los documentos de couchdb en formato json

gzip /couchdbdump/$DATE/${DATE}.json #lo comprime

aws s3 cp /couchdbdump/$DATE/${DATE}.json.gz s3://$BUCKET_NAME/$BACKUP_PATH/${DATE}.gz #sube el archivo al bucket
aws s3 ls s3://$BUCKET_NAME/$BACKUP_PATH/ #lista los archivos para confirmar
rm -rf /couchdbdump/$DATE/${DATE}.json.gz #elimina el local