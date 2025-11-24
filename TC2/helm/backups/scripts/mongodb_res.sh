#!/bin/bash
set -e
yum update -y

cat <<EOT > /etc/yum.repos.d/mongodb-org-7.0.repo
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOT
yum update -y
yum install mongodb-database-tools -y
mkdir -p /restore/$BACKUP_NAME

aws s3 cp s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz /restore/${BACKUP_NAME}.gz
mongorestore --gzip --archive=/restore/${BACKUP_NAME}.gz  --nsInclude="animalsdb.*" --host="$MONGO_CONNECTION_STRING" -u "$MONGO_USERNAME" -p "$MONGO_PASSWORD" --drop

