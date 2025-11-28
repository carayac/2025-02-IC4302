#!/bin/bash
set -e

DATE=$(date '+%Y%m%d%H%M')
BACKUP_DIR="/neo4jdump/$DATE"

mkdir -p "$BACKUP_DIR"

neo4j-admin database dump neo4j \
  --to-path="$BACKUP_DIR" \
  --overwrite-destination=true

gzip "$BACKUP_DIR/neo4j.dump"

aws s3 cp "$BACKUP_DIR/neo4j.dump.gz" \
  "s3://$BUCKET_NAME/$BACKUP_PATH/${DATE}.gz"

echo "Backup completado exitosamente."


