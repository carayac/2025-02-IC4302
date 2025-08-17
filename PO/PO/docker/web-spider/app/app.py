import os
import json
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
JOB_SIZE = int(os.getenv("JOB_SIZE"))
retmax = JOB_SIZE

#Datos a extraer
count = 0
lista_ids = []


new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
#Enviamos un request
response = requests.get(new_url)
data = response.text #datos en formato xml
datosFormatted = ET.fromstring(data)
#Guardamos Count
count = int(datosFormatted.find(".//Count").text)


#Paginación
while retstart < count:
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
    db_config = {
    'host': os.getenv('MARIADB'),
    'port': 3306,
    'user': os.getenv('MARIADB_USER'),
    'password': os.getenv('MARIADB_PASS'),
    'database': os.getenv('MARIADB_DB')
    }

    TABLE_NAME = os.getenv("MARIADB_TABLE")
    try:
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()

        insert_query = "INSERT INTO {TABLE_NAME} (id, estado, lista_ids, omitido, fecha_inicio, fecha_final) VALUES (?, ?, ?, ?, ?, ?)"
        try:
            cursor.execute(insert_query, (str(job["id"])
                                          , job["estado"]
                                          , json.dumps(job["lista_ids"]) #para recuperar usar json.loads
                                          , json.dumps(job["omitido"]) #para recuperar usar json.loads
                                          , job["fecha_inicio"]
                                          , job["fecha_final"]))
            conn.commit()
        except mariadb.Error as e:
            conn.rollback()

    except mariadb.Error as e:
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


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
    print(DATA)
    connection.close()
    ###########

    retstart+=20
