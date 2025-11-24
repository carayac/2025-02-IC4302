#!/bin/bash
DATE=$(date '+%Y%m%d%H%M')
mkdir -p /couchdbdump/$DATE

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

# se hace un dump de la base de datos en un json de couch. Obtener todos los documentos = dump
curl -s -u "$COUCHDB_USERNAME:$COUCHDB_PASSWORD" \
  "http://$COUCHDB_CONNECTION_STRING/$COUCHDB_DB/_all_docs?include_docs=true&attachments=true" \
  > /couchdbdump/$DATE/${DATE}.json

# gzip del dump
gzip /couchdbdump/$DATE/${DATE}.json

# subir s3
aws s3 cp /couchdbdump/$DATE/${DATE}.json.gz s3://$BUCKET_NAME/$BACKUP_PATH/${DATE}.gz
aws s3 ls s3://$BUCKET_NAME/$BACKUP_PATH/
rm -rf /couchdbdump/$DATE/${DATE}.json.gz