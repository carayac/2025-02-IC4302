import os
import pika
import json
import mariadb
import requests
import boto3

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
        id INT AUTO_INCREMENT PRIMARY KEY,   
        key_name VARCHAR(512),
        fecha_proceso DATETIME DEFAULT CURRENT_TIMESTAMP,
        num_documents INT
    )
    """)

    # Crear tabla de libros
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {MARIADB_TABLE_BOOKS} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        object_key VARCHAR(255) NOT NULL,
        title VARCHAR(500),
        authors TEXT,
        description TEXT,
        categories TEXT,
        published_date DATE,
        publisher VARCHAR(255),
        preview_link TEXT,
        info_link TEXT,
        image_link TEXT,
        ratings_count INT,
        FOREIGN KEY (object_key) REFERENCES {MARIADB_TABLE}(key_name)
    );
    """)
    conn.commit()
    return conn, cursor

def buscar_objeto(cursor, tabla, key_buscado):
    query = f"SELECT * FROM {tabla} WHERE key_name = %s"
    cursor.execute(query, (key_buscado,))
    resultado = cursor.fetchone()
    if resultado is None:
        return False
    else:
        return True


def descargar_objeto(key_name):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    bucket_name = AWS_BUCKET
    object_key = f"amazon-books/{key_name}"
    download_path = XPATH + key_name

    s3.download_file(bucket_name, object_key, download_path)

    return download_path


def procesar_objeto(file_path):
    documentos = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                try:
                    doc = json.loads(line)
                    doc = {clave.lower(): 
                           valor for clave, 
                           valor in doc.items()} #pasa las keys a minuscula
                    documentos.append(doc)
                except json.JSONDecodeError:
                    print("Error decodificando línea:", line)
    return documentos


def crear_embedding(texto):
    url = "http://localhost:5000/encode"

    response = requests.post(url, json={"text": texto})

    if response.status_code == 200:
        data = response.json()
        embedding = data["embedding"]
        return embedding
    else:
        print("Error:", response.text)
        return None


def embedding_todos_documentos(documentos):
    for doc in documentos:
        doc["embeddings"] = None
        texto = doc["description"]
        embedding = crear_embedding(texto)
        if not embedding is None:
            doc["embedding"] = embedding
    return documentos




def callback(ch, method, body):
    key_name = body.decode('utf-8')  # mensaje recibido, 
    #amazon-books/part-00099-7aac03f4-2533-4b8f-8be9-9057d831d6be-c000.json

    conn, cursor = conectar_MariaDB() #conectar mariadb

    # Verificar si ya se procesó
    existe = buscar_objeto(cursor, MARIADB_TABLE, key_name)

    if existe:
        ch.basic_ack(delivery_tag=method.delivery_tag) #no se hace nada
    else:
        # 1. Descargar desde S3
        # 2. Parsear JSON
        # 3. Generar embeddings
        # 4. Guardar en Elasticsearch
        # 5. Guardar en MariaDB
        # 5. Marcar como procesado en MariaDB

        ch.basic_ack(delivery_tag=method.delivery_tag)

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
