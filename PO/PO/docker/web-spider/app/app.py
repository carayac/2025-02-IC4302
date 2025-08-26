import os
import time
import pika
import requests
import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
import mariadb
import sys

url_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"


#Parametros en la url
db = "pubmed"
term = "science journal"
retstart = 0
JOB_SIZE = 20
retmax = JOB_SIZE

#Datos a extraer
count = 0


new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
#Enviamos un request
response = requests.get(new_url)
data = response.text #datos en formato xml
datosFormatted = ET.fromstring(data)
#Guardamos Count
count = int(datosFormatted.find(".//Count").text)


#Hacemos la conexión a MariaDB
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


#Paginación
while retstart < count:
    lista_ids = []
    
    #Nueva url con parametros
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"

    #Enviamos un request
    response = requests.get(new_url)
    data = response.text #datos en formato xml
    datosFormatted = ET.fromstring(data)

    #Guardamos los datos
    for elem in datosFormatted.findall(".//Id"):
        lista_ids.append(elem.text)

    #Creamos un job
    job = {
        "id": uuid.uuid4(), #libreria que genera id aleatorio y unico
        "estado": "pending",
        "lista_ids": lista_ids,
        "omitido": [],
        "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_final": None
    }

    #Aquí lo subimos a MariaDB
    #Insertar Job
    insert_query = f"""
        INSERT INTO {os.getenv('MARIADB_TABLE')}
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



    #Luego enviamos el id del job por RabbitMQ
    DATA=os.getenv('DATAFROMK8S')
    RABBIT_MQ=os.getenv('RABBITMQ')
    RABBIT_MQ_PASSWORD=os.getenv('RABBITMQ_PASS')
    QUEUE_NAME=os.getenv('RABBITMQ_QUEUE')

    hostname = os.getenv('HOSTNAME')

    credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials) 
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    msg = str(job["id"])
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=msg)
    time.sleep(1)
    connection.close()
    ###########

    retstart+=retmax

cursor.close()
conn.close()
