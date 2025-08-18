import time
import os
import sys
import pika
from datetime import datetime
import json
import hashlib
import mariadb


hostname = os.getenv('HOSTNAME')
XPATH=os.getenv('XPATH')

# RabbitMQ variables de entorno
DATA=os.getenv('DATAFROMK8S')
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITMQ_PASS')
QUEUE_NAME=os.getenv('RABBITMQ_QUEUE')

# MariaDB variables de entorno
MARIADB_HOST = os.getenv('MARIADB')
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')

#Nos conectamos a MariaDB
def connection_MariaDB():
    try:
        connection = mariadb.connect(
            host=MARIADB_HOST,
            port=3306,
            user=MARIADB_USER,
            password=MARIADB_PASS,
            database=MARIADB_DB
        )
        return connection
    except mariadb.Error as e:
        print(f"Error conectando a MariaDB: {e}")
        return None

def update_job_status(job_id, status):
    connection = connection_MariaDB()
    try:
        cursor = connection.cursor()
        query = f"UPDATE {MARIADB_TABLE} SET estado = ? WHERE id = ?"
        cursor.execute(query, (status, job_id))
        connection.commit()

        ## Verificamos si se actualizo el job
        if cursor.rowcount > 0:
            print(f"Job {job_id} actualizado a estado: {status}")
            return True
        else:
            print(f"No se encontró job con ID: {job_id}")
            return False
            
    except mariadb.Error as e:
        print(f"Error actualizando job {job_id}: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()



def callback(ch, method, properties, body):
    try:
        job_id = body.decode('utf-8').strip()
        print(f" Job ID: {job_id}")

        # Actualizamos el estado del job llamando a la funcion
        change = update_job_status(job_id, "in-progress")

    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        print(f"Body recibido: {body}")





credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials) 
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
