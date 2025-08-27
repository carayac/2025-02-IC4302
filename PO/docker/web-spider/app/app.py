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
    response = requests.get(new_url)
    data = response.text  # datos en formato xml
    datosFormatted = ET.fromstring(data)
    # Guardamos Count
    return int(datosFormatted.find(".//Count").text)



def obtener_ids(url_base, db, term, retstart, retmax):
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
    # Enviamos un request
    response = requests.get(new_url)
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



def enviar_rabbitmq(job_id):
    """Luego enviamos el id del job por RabbitMQ"""
    RABBIT_MQ = os.getenv('RABBITMQ')
    RABBIT_MQ_PASSWORD = os.getenv('RABBITMQ_PASS')
    QUEUE_NAME = os.getenv('RABBITMQ_QUEUE')

    credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    msg = str(job_id)
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=msg)
    time.sleep(1)
    connection.close()






#Ciclo Principal con Paginacion
conn, cursor = conectar_MariaDB()
table_name = os.getenv('MARIADB_TABLE')
count = obtener_count(url_base, db, term, retstart, retmax)

# Paginación
while retstart < count:
    lista_ids = obtener_ids(url_base, db, term, retstart, retmax)

    # Creamos un job
    job = {
        "id": uuid.uuid4(),  
        "estado": "pending",
        "lista_ids": lista_ids,
        "omitido": [],
        "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_final": None
    }

    insertar_job(cursor, conn, table_name, job)
    enviar_rabbitmq(job["id"])

    retstart += retmax

cursor.close()
conn.close()
