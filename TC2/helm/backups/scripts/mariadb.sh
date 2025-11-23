#!/bin/bash
# Fecha y hora actual en formato YYYYMMDDHHMM
DATE=$(date '+%Y%m%d%H%M')
# Directorio temporal para dumps
DIR=/mariadump

# Función para eliminar backups antiguos
removeoldbackups() {
    # Listar backups en S3 y guardar en archivo temporal
    aws s3 ls s3://$BUCKET_NAME/$BACKUP_PATH/ > /tmp/backups.txt

    # Contar número de backups
    CNT=$(cat /tmp/backups.txt | wc -l)
    if [ $CNT -gt $MAX_BACKUPS ]; then
        # Eliminar backups excedentes
        for ((i = 0; i < $[$CNT - $MAX_BACKUPS]; i++)); do
            read -r line;
            # Obtener nombre del archivo a eliminar
            line=$(echo $line | cut -d " " -f 4);
            aws s3 rm s3://$BUCKET_NAME/$BACKUP_PATH/$line
        done < /tmp/backups.txt;

        echo "Backups eliminados (máximo de backups es $MAX_BACKUPS). Backups actuales:"
        aws s3 ls s3://$BUCKET_NAME/$BACKUP_PATH/
    fi

    # Limpiar archivo temporal
    rm /tmp/backups.txt
}

# Crear directorio temporal
mkdir -p $DIR/$DATE
# Actualizar repositorios de yum
yum update -y

# Instalar MariaDB disponible en Amazon Linux 2023
yum install -y mariadb105

# Extraer host y puerto de CONNECTION_STRING
MARIADB_HOST=$(echo $CONNECTION_STRING | cut -d':' -f1)
MARIADB_PORT=$(echo $CONNECTION_STRING | cut -d':' -f2)

# Si es backup
if [ "$TYPE" == "backup" ]; then
    echo "*-*-* MODO BACKUP *-*-*"

    echo "Creando dump de la base de datos..."
    # Crear dump de todas las bases de datos
    mysqldump --host=$MARIADB_HOST --port=$MARIADB_PORT --user=$DB_USERNAME --password=$DB_PASSWORD --lock-tables --all-databases > $DIR/$DATE/$DATE.sql

    echo "Copiando a AWS..."
    # Subir dump a S3
    aws s3 cp $DIR/$DATE/$DATE.sql s3://$BUCKET_NAME/$BACKUP_PATH/

    echo "Backups actuales:"
    aws s3 ls s3://$BUCKET_NAME/$BACKUP_PATH/

    # Eliminar backups antiguos
    removeoldbackups

    echo "*-*-* BACKUP FINALIZADO *-*-*"

# Si es restore
else
    echo "*-*-* MODO RESTORE *-*-*"

    echo "Backups actuales:"
    aws s3 ls s3://$BUCKET_NAME/$BACKUP_PATH/

    echo "Copiando desde AWS..."
    # Descargar backup de S3
    aws s3 cp s3://$BUCKET_NAME/$BACKUP_PATH/$BACKUP_FILE $DIR/$DATE/$BACKUP_FILE

    echo "Restaurando en la base de datos..."
    # Restaurar dump en la base de datos
    mysql --host=$MARIADB_HOST --port=$MARIADB_PORT --user=$DB_USERNAME --password=$DB_PASSWORD < $DIR/$DATE/$BACKUP_FILE

    echo "*-*-* RESTAURACIÓN FINALIZADA *-*-*"
fi

# Limpiar directorio temporal
rm -rf $DIR/$DATE