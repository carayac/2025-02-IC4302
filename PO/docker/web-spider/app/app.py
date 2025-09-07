from functions import *

#Ciclo Principal con Paginacion
def main():
    retstart = 0 
    # Conexión MariaDB
    conn, cursor = conectar_MariaDB()
    table_name = os.getenv('MARIADB_TABLE')

    # Conexión RabbitMQ
    connection, channel, queue_name = conectar_rabbitmq()

    # Obtener count
    count = obtener_count(url_base, db, term, retstart, retmax)

    # Paginación
    while retstart < count:
        lista_ids = obtener_ids(url_base, db, term, retstart, retmax)

        # Crear job
        job = crear_job(lista_ids)

        insertar_job(cursor, conn, table_name, job)
        enviar_rabbitmq(job["id"], channel, queue_name)

        retstart += retmax  # Incrementamos retstart de 20 en 20

    # Cierres
    cursor.close()
    conn.close()
    connection.close()



if __name__ == "__main__":
    main()
