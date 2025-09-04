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
import ast
import time


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

#Nos conectamos a MariaDB considerando si se cae que lo reintente
def connection_MariaDB():
    for i in range (3):
        try:
            # Hacemos la conexion con las variables
            connection = mariadb.connect(
                host=MARIADB_HOST,
                port=3306,
                user=MARIADB_USER,
                password=MARIADB_PASS,
                database=MARIADB_DB,
                connect_timeout=15
            )
            return connection
        except mariadb.Error as e:
            print(f"Error conectando a MariaDB: {e}")
            time.sleep(5)
    return None

# Actualizamos el estado del job
def update_job_status(job_id, status):
    connection = connection_MariaDB()
    if not connection: 
        print(f"No se pudo conectar a MariaDB para job {job_id}")
        return False
        
    try:
        #Ejecutamos el query para cambiar el estado
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

# Actualizamos la fecha final con la hora actual
def update_job_end_date(job_id):
    connection = connection_MariaDB()
    if not connection: 
        print(f"No se pudo conectar a MariaDB para job {job_id}")
        return False
        
    try:
        # Ejecutamos el query para cambiar la fecha final
        cursor = connection.cursor()
        query = f"UPDATE {MARIADB_TABLE} SET fecha_final = ? WHERE id = ?"
        cursor.execute(query, (datetime.now(), job_id))
        connection.commit()

        # Verificamos si se actualizo el job
        if cursor.rowcount > 0:
            print(f"Job {job_id} actualizado con nueva fecha final.")
            return True
        else:
            print(f"No se encontró job con ID: {job_id}")
            return False

    except mariadb.Error as e:
        print(f"Error actualizando fecha final del job {job_id}: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

# Obtenemos los ids del job
def get_job_ids(job_id):
    connection = connection_MariaDB()
    if not connection: 
        print(f"No se pudo conectar a MariaDB para job {job_id}")
        return []
        
    try:
        # Ejecutamos el query y obtenemos la fila con los resultados
        cursor = connection.cursor()
        query = f"SELECT lista_ids FROM {MARIADB_TABLE} WHERE id = ?"
        cursor.execute(query, (job_id,))
        result = cursor.fetchone()

        if result:
            # Obtenemos el string y lo convertimos a lista
            lista_ids= ast.literal_eval(result[0])
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
        response = requests.get(url, timeout=30)
        # Verificamos si todo salió bien
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
        # Usamos regex para encontrar el patrón del DOI
        doi_pattern = r'<Item Name="DOI" Type="String">([^<]+)</Item>'
        found_dois = re.findall(doi_pattern, xml_response)
        final_dois = []
        for doi in found_dois:
            # Quitamos espacios en blanco por si acaso
            cleaned_doi = doi.strip()
            if cleaned_doi and cleaned_doi not in final_dois:
                final_dois.append(cleaned_doi)
        return final_dois
        
    except Exception as e:
        print(f"Error extrayendo DOIs: {e}")
        return []


def process_dois(job_id, dois_list): #Recibe una lista de dois, consulta crossref e invoca la funcion que guarda el json o añade el doi a omitidos. 
    omitidos = []

    for doi in dois_list:
        crossref_data = crossref_API(doi)
        if crossref_data:
            save_json(doi, crossref_data)
        else:
            omitidos.append(doi)

    # Guardamos los omitidos en la tabla (si hay)
    if omitidos:
        try:
            connection = connection_MariaDB()
            cursor = connection.cursor()
            query = f"UPDATE {MARIADB_TABLE} SET omitido = ? WHERE id = ?"
            cursor.execute(query, (",".join(omitidos), job_id))
            connection.commit()
            print(f"Job {job_id}: {len(omitidos)} DOIs omitidos guardados en DB")
        except mariadb.Error as e:
            print(f"Error guardando omitidos en DB: {e}")
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

    # Actualizamos el estado del job a "done" y agregramos la fecha final
    update_job_status(job_id, "done")
    update_job_end_date(job_id)
    print(f"Job {job_id} finalizado correctamente.")

def save_json(doi, data): #Guarda el Json en el volumen. 
    path = os.getenv("XPATH", "/data")  # ruta compartida definida en charts/application/templates/volume.yaml
    filename = hashlib.md5(doi.encode()).hexdigest() + ".json"
    filepath = os.path.join(path, filename)
    try:
        with open(filepath, "w") as f:
            json.dump(data, f)
        print(f"Guardado correctamente {filepath}")
    except Exception as e:
        print(f"Error en {filepath}: {e}")

def crossref_API(doi): #Consulta Crossref
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"DOI no encontrado en Crossref: {doi}")
            return None
        else:
            print(f"Crossref error con el codigo: {response.status_code}") #Si el status code no es 200 lo imprime para ver qué respuesta dio
            return None
    except Exception as e:
        print(f"Crossref error: {e}")
        return None

contador=0
def callback(ch, method, properties, body):
    global contador
    job_id = body.decode('utf-8').strip()

    try:
        change = update_job_status(job_id, "in-progress")
        ids_list = get_job_ids(job_id)

        if ids_list == []:
            print(f"Job {job_id} no tiene IDs válidos.")
            update_job_status(job_id, "done sin IDs")
            update_job_end_date(job_id)
        else:
            pubmed_response = pubmed_API(ids_list)

            if pubmed_response is None:
                print(f"Error en API de PubMed para job {job_id}")
                update_job_status(job_id, "done sin PubMed")
                update_job_end_date(job_id)
            else:
                dois_list = dois_pubmed(pubmed_response)

                if dois_list == []:
                    print(f"Job {job_id} no tiene DOIs válidos.")
                    update_job_status(job_id, "done sin DOIs")
                    update_job_end_date(job_id)
                else:
                    process_dois(job_id, dois_list)

        contador += 1
        print(f"Job {contador} procesado")
        print("------------------------------------------------------")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        print(f"Body recibido: {body}")
        update_job_status(job_id, "error")
        update_job_end_date(job_id)
        time.sleep(5)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)



def main():
    credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBIT_MQ,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
