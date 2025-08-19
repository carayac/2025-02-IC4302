import time
import os
import sys
import pika
from datetime import datetime
import json
import hashlib
import mariadb
import requests
import xml.etree.ElementTree as ET
import re


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

        # Verificamos si se actualizo el job
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

# Obtenemos los ids del job
def get_job_ids(job_id):
    connection = connection_MariaDB()
    try:
        cursor = connection.cursor()
        query = f"SELECT lista_ids FROM {MARIADB_TABLE} WHERE id = ?"
        cursor.execute(query, (job_id,))
        result = cursor.fetchone()
        
        if result:
            # Si el resultado viniera como string, averiguar como viene
            lista_ids_str = result[0]
            # Remover corchetes y comillas, luego split por comas
            lista_ids_str = lista_ids_str.strip("[]'\"")
            lista_ids = [id.strip().strip("'\"") for id in lista_ids_str.split(",") if id.strip()]
            return lista_ids
        else:
            print(f"No se encontró job con ID: {job_id}")
            return None
            
    except mariadb.Error as e:
        print(f"Error obteniendo datos del job {job_id}: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

# Consultamos la API de PubMed con la nueva URL
def pubmed_API(ids_list):

    # Convertimos la lista de ids a string separado por comas
    ids_string = ",".join(ids_list)

    # URL de la API con los ids
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_string}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Respuesta exitosa de PubMed")
            return response.text
        else:
            print(f"Error en API de PubMed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error consultando PubMed: {e}")
        return None

# Obtenemos los DOIs de la respuesta de PubMed
def dois_pubmed(xml_response):
    dois = []
    try:
        # Usamos regex para encontrar este patrón exacto del DOI
        doi_pattern = r'<Item Name="DOI" Type="String">([^<]+)</Item>'
        found_dois = re.findall(doi_pattern, xml_response)
        clean_dois = []
        for doi in found_dois:
            # Quitamos espacios en blanco por si acaso
            cleaned_doi = doi.strip()
            if cleaned_doi and cleaned_doi not in clean_dois:
                clean_dois.append(cleaned_doi)
        return clean_dois
        
    except Exception as e:
        print(f"Error extrayendo DOIs: {e}")
        return []



def callback(ch, method, properties, body):
    try:
        job_id = body.decode('utf-8').strip()
        print(f" Job ID: {job_id}")

        # 1. Actualizamos el estado del job a "in-progress"
        change = update_job_status(job_id, "in-progress")
        if change:
            print(f" Se actualizo el estado del job {job_id}")
        
        # 2. Obtenemos la lista de IDs de artículos del job
        ids_list = get_job_ids(job_id)
        if ids_list:
            print(f" Se obtuvieron los IDs del job {job_id}")
            
        # 3. Consultamos la API 
        pubmed_response = pubmed_API(ids_list)
        if pubmed_response:
            print(f" Se obtuvo respuesta de PubMed para job {job_id}")
            
        # 4. Extraemos DOIs de la respuesta de PubMed
        dois_list = dois_pubmed(pubmed_response)
        if dois_list:
            print(f" Se encontraron DOIs en job {job_id}")

    except Exception as e:
        print(f" Error procesando mensaje: {e}")
        print(f" Body recibido: {body}")





credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials) 
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
