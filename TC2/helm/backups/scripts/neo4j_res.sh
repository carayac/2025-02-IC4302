#!/bin/bash
set -e

echo "Descargando backup desde S3..."
mkdir -p /restore
aws s3 cp s3://$BUCKET_NAME/$BACKUP_PATH/${BACKUP_NAME}.gz /restore/${BACKUP_NAME}.gz

gunzip /restore/${BACKUP_NAME}.gz

neo4j-admin database load neo4j \
  --from-path=/restore \
  --overwrite-destination=true

echo "Restauración completada exitosamente."

