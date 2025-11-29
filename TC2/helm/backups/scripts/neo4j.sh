#!/bin/bash
set -e


DB_DIR="/data/data/databases/neo4j"

if [ ! -d "$DB_DIR" ]; then
  echo "La ruta $DB_DIR no existe. No se puede crear el backup."
  exit 1
fi

DATE=$(date '+%Y%m%d%H%M')
BACKUP_DIR="/backup/$DATE"
mkdir -p "$BACKUP_DIR"

neo4j stop || true

neo4j-admin database dump neo4j --to-path="$BACKUP_DIR" --overwrite-destination=true

gzip "$BACKUP_DIR/neo4j.dump"

echo "Subiendo a S3..."
aws s3 cp "$BACKUP_DIR/neo4j.dump.gz" "s3://$BUCKET_NAME/$BACKUP_PATH/${DATE}.gz"

echo "Backup completado exitosamente."

neo4j start || true












