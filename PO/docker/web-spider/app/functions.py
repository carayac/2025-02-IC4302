import os
import time
import pika
import requests
import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import mariadb
import sys

#Parametros
url_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

#Parametros en la url
db = "pubmed"
term = "science[journal]"
retstart = 0
JOB_SIZE = 20
retmax = JOB_SIZE


def obtener_count(url_base, db, term, retstart, retmax):
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
    # Enviamos un request
    try:
        response = requests.get(new_url)
    except:
        print(f"Error consultando API")
    data = response.text  # datos en formato xml
    datosFormatted = ET.fromstring(data)
    # Guardamos Count
    return int(datosFormatted.find(".//Count").text)



def obtener_ids(url_base, db, term, retstart, retmax):
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
    # Enviamos un request
    try:
        response = requests.get(new_url)
    except:
        print(f"Error consultando API")
    data = response.text  # datos en formato xml
    datosFormatted = ET.fromstring(data)
    # Guardamos los datos
    lista_ids = []
    for elem in datosFormatted.findall(".//Id"):
        lista_ids.append(elem.text)
    return lista_ids



def conectar_MariaDB():
    conn = mariadb.connect(
        host=os.getenv('MARIADB'),
        user=os.getenv('MARIADB_USER'),
        password=os.getenv('MARIADB_PASS')
    )
    cursor = conn.cursor()

    # Crear la base de datos si no existe
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('MARIADB_DB')}")
    cursor.execute(f"USE {os.getenv('MARIADB_DB')}")

    # Crear la tabla si no existe
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {os.getenv('MARIADB_TABLE')} (
        id VARCHAR(36) PRIMARY KEY,
        estado VARCHAR(20),
        lista_ids TEXT,
        omitido TEXT,
        fecha_inicio DATETIME,
        fecha_final DATETIME
    )
    """)
    conn.commit()
    return conn, cursor



def insertar_job(cursor, conn, table_name, job):
    insert_query = f"""
        INSERT INTO {table_name}
        (id, estado, lista_ids, omitido, fecha_inicio, fecha_final)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        cursor.execute(insert_query, (
            str(job["id"]),
            job["estado"],
            str(job["lista_ids"]),
            str(job["omitido"]),
            job["fecha_inicio"],
            job["fecha_final"]
        ))
        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        print(f"Error insertando job: {e}")



def conectar_rabbitmq():
    RABBIT_MQ = os.getenv('RABBITMQ')
    RABBIT_MQ_PASSWORD = os.getenv('RABBITMQ_PASS')
    QUEUE_NAME = os.getenv('RABBITMQ_QUEUE')
    try:
        credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
        parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        return connection, channel, QUEUE_NAME
    except Exception as e:
        print(f"Error conectando a RabbitMQ: {e}")
        sys.exit(1)


def enviar_rabbitmq(job_id, channel, queue_name):
    try:
        msg = str(job_id)
        channel.basic_publish(exchange='', routing_key=queue_name, body=msg)
    except Exception as e:
        print(f"Error enviando job-id por RabbitMQ: {e}")
    time.sleep(1)


def crear_job(lista_ids):
    """Crea un job con un id único y estado inicial"""
    return {
        "id": uuid.uuid4(),
        "estado": "pending",
        "lista_ids": lista_ids,
        "omitido": [],
        "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_final": None
    }



#Ciclo Principal con Paginacion
def main():
    # Conexión MariaDB
    conn, cursor = conectar_MariaDB()
    table_name = os.getenv('MARIADB_TABLE')

    # Conexión RabbitMQ
    connection, channel, queue_name = conectar_rabbitmq()

    # Obtener count
    count = obtener_count(url_base, db, term, retstart, retmax)

    # Paginación
    global retstart
    while retstart < count:
        lista_ids = obtener_ids(url_base, db, term, retstart, retmax)

        # Crear job
        job = crear_job(lista_ids)

        insertar_job(cursor, conn, table_name, job)
        enviar_rabbitmq(job["id"], channel, queue_name)

        retstart += retmax

    # Cierres
    cursor.close()
    conn.close()
    connection.close()
