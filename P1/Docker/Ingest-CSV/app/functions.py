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

# General
HOSTNAME = os.getenv('HOSTNAME')
XPATH = os.getenv('XPATH')
DATA = os.getenv('DATAFROMK8S')

# RabbitMQ
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD = os.getenv('RABBITMQ_PASS')
QUEUE_NAME = os.getenv('RABBITMQ_QUEUE')

# MariaDB
MARIADB_HOST = os.getenv('MARIADB')
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')
MARIADB_TABLE_BOOKS = os.getenv('MARIADB_TABLE_BOOKS')

# ElasticSearch
ELASTIC_HOST = os.getenv('ELASTIC_HOST')
ELASTIC_USER = os.getenv('ELASTIC_USER')
ELASTIC_PASS = os.getenv('ELASTIC_PASS')
ELASTIC_INDEX_BOOKS = os.getenv('ELASTIC_INDEX_BOOKS')  # books/reviews
ELASTIC_INDEX_NBOOKS = os.getenv('ELASTIC_INDEX_NBOOKS')  # nbooks/nreviews

# AWS S3 Bucket
AWS_BUCKET = os.getenv('AWS_BUCKET')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')


import os
import mariadb

def conectar_MariaDB():
    conn = mariadb.connect(
        host= MARIADB_HOST,
        user= MARIADB_USER,
        password= MARIADB_PASS
    )
    cursor = conn.cursor()

    # Crear la base de datos si no existe
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MARIADB_DB}")
    cursor.execute(f"USE {os.getenv('MARIADB_DB')}")

    # Crear tabla de objetos procesados
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {os.getenv('MARIADB_TABLE')} (
        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
        key_name VARCHAR(512),
        fecha_proceso DATETIME DEFAULT CURRENT_TIMESTAMP,
        num_documents INT
    )
    """)

    # Crear tabla de libros
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {os.getenv('MARIADB_TABLE_BOOKS')} (
        id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
        s3_object_name VARCHAR(255) NOT NULL,
        title VARCHAR(500),
        authors TEXT,
        description TEXT,
        categories TEXT,
        published_date DATE,
        publisher VARCHAR(255),
        preview_link TEXT,
        image_link TEXT,
        ratings_count INT,
        embeddings JSON,
        processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_s3_object (s3_object_name)
    )
    """)

    conn.commit()
    return conn, cursor




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
    #Va a consumir esa cola, cuando llega el mensaje llama a callback y no se confirma el mensaje automaticamente
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)




# def insertar_job(cursor, conn, table_name, job):
#     insert_query = f"""
#         INSERT INTO {table_name}
#         (id, estado, lista_ids, omitido, fecha_inicio, fecha_final)
#         VALUES (?, ?, ?, ?, ?, ?)
#     """
#     try:
#         cursor.execute(insert_query, (
#             str(job["id"]),
#             job["estado"],
#             str(job["lista_ids"]),
#             str(job["omitido"]),
#             job["fecha_inicio"],
#             job["fecha_final"]
#         ))
#         conn.commit()
#     except mariadb.Error as e:
#         conn.rollback()
#         print(f"Error insertando job: {e}")



# def conectar_rabbitmq():
#     RABBIT_MQ = os.getenv('RABBITMQ')
#     RABBIT_MQ_PASSWORD = os.getenv('RABBITMQ_PASS')
#     QUEUE_NAME = os.getenv('RABBITMQ_QUEUE')
#     try:
#         credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
#         parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials)
#         connection = pika.BlockingConnection(parameters)
#         channel = connection.channel()
#         channel.queue_declare(queue=QUEUE_NAME)
#         return connection, channel, QUEUE_NAME
#     except Exception as e:
#         print(f"Error conectando a RabbitMQ: {e}")
#         sys.exit(1)


# def enviar_rabbitmq(job_id, channel, queue_name):
#     try:
#         msg = str(job_id) # Se construye el mensaje
#         channel.basic_publish(exchange='', routing_key=queue_name, body=msg) # Se envía el mensaje
#     except Exception as e:
#         print(f"Error enviando job-id por RabbitMQ: {e}")
#     time.sleep(1)


# def crear_job(lista_ids):
#     """Crea un job con un id único y estado inicial"""
#     return {
#         "id": uuid.uuid4(), # Genera un ID único
#         "estado": "pending",
#         "lista_ids": lista_ids,
#         "omitido": [],
#         "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "fecha_final": None
#     }