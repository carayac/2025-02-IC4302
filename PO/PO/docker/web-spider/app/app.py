import time
import os
import sys
import pika
import requests
import xml.etree.ElementTree as ET
import uuid
from datetime import datetime

url_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

#Parametros en la url
db = "pubmed"
term = "science journal"
retstart = 0
retmax = 20

#Datos a extraer
count = 0
lista_ids = []

#Paginacion
while retstart+20 <= count:
    #Nueva url con parametros
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"

    #Enviamos un request
    response = requests.get(new_url)
    data = response.text #datos en formato xml
    datosFormatted = ET.fromstring(data)

    #Guardamos los datos
    count = int(datosFormatted.find(".//Count").text)
    for elem in datosFormatted.findall(".//Id"):
        lista_ids.append(elem.text)

    #Creamos un job
    job = {
        "id": uuid.uuid4(), #libreria que genera id aleatorio y unico
        "estado": "pending",
        "Lista_ids": lista_ids,
        "omitido": [],
        "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_fin": None
    }

    #Aquí lo subiríamos a MariaDB


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


    localtime = time.localtime()
    result = time.strftime("%I:%M:%S %p", localtime)
    msg = str(job["id"])
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=msg)
    print(DATA+" - " +result)
    time.sleep(1)
        
    connection.close()


    retstart+20
