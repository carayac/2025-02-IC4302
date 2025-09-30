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
    cursor.execute(f"USE {MARIADB_DB}")
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
    object_key = key_name
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
        if "description" in doc:
            texto = doc["description"]
            embedding = crear_embedding(texto)
            if embedding is not None:
                doc["embedding"] = embedding
    return documentos


def insertar_libro(conn, cursor, object_key, title=None, authors=None, description=None,
                   categories=None, published_date=None, publisher=None,
                   preview_link=None, info_link=None, image_link=None,
                   ratings_count=None):
    query = f"""
    INSERT INTO {MARIADB_TABLE_BOOKS}
    (object_key, title, authors, description, categories,
     published_date, publisher, preview_link, info_link,
     image_link, ratings_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor.execute(query, (
            object_key,
            title,
            authors,
            description,
            categories,
            published_date,
            publisher,
            preview_link,
            info_link,
            image_link,
            ratings_count
        ))
        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        print(f"Error insertando libro: {e}")



def insertar_info(cursor, conn, key_name, documentos):
    for doc in documentos:
        title = doc.get("title")
        authors = doc.get("authors")
        description = doc.get("description")
        categories = doc.get("categories")
        published_date = doc.get("published_date")
        publisher = doc.get("publisher")
        preview_link = doc.get("preview_link")
        info_link = doc.get("info_link")
        image_link = doc.get("image_link")
        ratings_count = doc.get("ratings_count")

        insertar_libro(
            conn, cursor, key_name,
            title, authors, description,
            categories, published_date, publisher,
            preview_link, info_link, image_link,
            ratings_count
        )


def insertar_object(cursor, conn, key_name, documentos, procesado):
    insert_query = f"""
        INSERT INTO {MARIADB_TABLE}
        (key_name, num_documents, procesado)
        VALUES (?, ?, ?)
    """
    try:
        cursor.execute(insert_query, (
            key_name,
            len(documentos),
            procesado
        ))
        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        print(f"Error insertando object: {e}")


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
        file_path = descargar_objeto(key_name)
        # 2. Parsear JSON
        documentos = procesar_objeto(file_path)
        # 3. Generar embeddings
        procesado = False
        insertar_object(cursor, conn, key_name, documentos, procesado)
        documentos = embedding_todos_documentos(documentos)
        # 4. Guardar en Elasticsearch

        # 5. Guardar en MariaDB
        insertar_info(cursor, conn, key_name, documentos)
        # 5. Marcar como procesado en MariaDB
        procesado = True
        insertar_object(cursor, conn, key_name, documentos, procesado)

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