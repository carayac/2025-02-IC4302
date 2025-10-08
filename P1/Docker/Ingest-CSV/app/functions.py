import os
import pika
import json
import time
import mariadb
import requests
import boto3
from elasticsearch import Elasticsearch

# General
HOSTNAME = os.getenv('HOSTNAME')
XPATH = os.getenv('XPATH')
DATA = os.getenv('DATAFROMK8S')
EMBEDDINGENDPOINT = os.getenv("EMBEDDINGENDPOINT", "http://huggingface:5000/encode")

# RabbitMQ
RABBIT_MQ = os.getenv('RABBITMQ')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
QUEUE_NAME = os.getenv('RABBITMQ_QUEUE')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
print("USER:", os.environ.get("RABBITMQ_USER"))
print("PASS:", os.environ.get("RABBITMQ_PASS"))

# MariaDB
MARIADB_HOST = os.getenv('MARIADB')
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')
MARIADB_TABLE_BOOKS = os.getenv('MARIADB_TABLE_BOOKS')
MARIADB_TABLE_AUTHORS = os.getenv("MARIADB_TABLE_AUTHORS")
MARIADB_TABLE_CATEGORIES = os.getenv("MARIADB_TABLE_CATEGORIES")
MARIADB_TABLE_AUTHORS_BOOKS = os.getenv("MARIADB_TABLE_AUTHORS_BOOKS")
MARIADB_TABLE_CATEGORIES_BOOKS = os.getenv("MARIADB_TABLE_CATEGORIES_BOOKS")


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
    print(key_name)
    download_path = os.path.join(XPATH, key_name)
    print(download_path)
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    print(download_path)

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
    """Genera el embedding de un texto usando el endpoint Flask."""
    try:
        data = {"text": texto}
        response = requests.post(EMBEDDINGENDPOINT, json=data, timeout=10)  # timeout para no quedarse pegado
        response.raise_for_status()  # lanza excepción si status != 200
        embedding = response.json().get("embedding")
        if embedding is None:
            print(f"No se recibió embedding para el texto: {texto[:50]}...")
        return embedding
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición al endpoint {EMBEDDINGENDPOINT}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado generando embedding: {e}")
        return None

def embedding_todos_documentos(documentos):
    """Itera sobre los documentos y genera embeddings para la descripción si existe."""
    for i, doc in enumerate(documentos, start=1):
        doc["embeddings"] = None
        if "description" in doc and doc["description"]:
            texto = doc["description"]
            embedding = crear_embedding(texto)
            if embedding is not None:
                doc["embeddings"] = embedding
        print(f"Procesado documento {i}/{len(documentos)}")
    return documentos

#########################Elastic
# Conexión a Elasticsearch
def conectar_elasticsearch():
    try:
        es_host = os.getenv("ELASTIC_HOST")
        es_user = os.getenv("ELASTIC_USER")
        es_pass = os.getenv("ELASTIC_PASS")

        # Forma correcta para Elasticsearch >=8.x
        es = Elasticsearch(
            f"http://{es_user}:{es_pass}@{es_host}:9200"
        )

        if not es.ping():
            print("No se pudo conectar a Elasticsearch")
            return None

        print("Conexión a Elasticsearch exitosa")
        return es

    except Exception as e:
        print("Error conectando a Elasticsearch:", e)
        return None

# Guardar libros en Elasticsearch
def guardar_libros_elasticsearch(documentos):
    es = conectar_elasticsearch()
    if es is None:
        return

    for i, doc in enumerate(documentos, start=1):
        # Documento sin embeddings
        doc_sin_embedding = doc.copy()
        doc_sin_embedding.pop("embeddings", None)

        # Insertar con embeddings en "books"
        try:
            es.index(index="books", document=doc)
        except Exception as e:
            print(f"Error insertando en books (documento {i}):", e)

        # Insertar sin embeddings en "nbooks"
        try:
            es.index(index="nbooks", document=doc_sin_embedding)
        except Exception as e:
            print(f"Error insertando en nbooks (documento {i}):", e)

################################

def insertar_author(cursor, conn, author_name):
    query = f"INSERT IGNORE INTO {MARIADB_TABLE_AUTHORS} (name) VALUES (?)"
    cursor.execute(query, (author_name,))
    conn.commit()

    # Obtener el ID del autor
    cursor.execute(f"SELECT id FROM {MARIADB_TABLE_AUTHORS} WHERE name = ?", (author_name,))
    return cursor.fetchone()[0]


def insertar_category(cursor, conn, category_name):
    query = f"INSERT IGNORE INTO {MARIADB_TABLE_CATEGORIES} (name) VALUES (?)"
    cursor.execute(query, (category_name,))
    conn.commit()

    # Obtener el ID de la categoría
    cursor.execute(f"SELECT id FROM {MARIADB_TABLE_CATEGORIES} WHERE name = ?", (category_name,))
    return cursor.fetchone()[0]


def insertar_libro(conn, cursor, object_key, title=None, description=None,
                   published_date=None, publisher=None, preview_link=None,
                   info_link=None, image_link=None, ratings_count=None):
    query = f"""
    INSERT INTO books
    (object_key, title, description, published_date, publisher, preview_link, info_link, image_link, ratings_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (
        object_key, title, description, published_date,
        publisher, preview_link, info_link, image_link, ratings_count
    ))
    conn.commit()

    cursor.execute("SELECT LAST_INSERT_ID()")
    return cursor.fetchone()[0]  # ID del libro insertado

def relacionar_autores_categories(cursor, conn, book_id, authors=None, categories=None):
    # Autores
    if authors:
        for author in authors:
            author_id = insertar_author(cursor, conn, author.strip())
            cursor.execute(f"""
                INSERT IGNORE INTO {MARIADB_TABLE_AUTHORS_BOOKS} (book_id, author_id)
                VALUES (?, ?)
            """, (book_id, author_id))
    # Categorías
    if categories:
        for category in categories:
            category_id = insertar_category(cursor, conn, category.strip())
            cursor.execute(f"""
                INSERT IGNORE INTO {MARIADB_TABLE_CATEGORIES_BOOKS} (book_id, category_id)
                VALUES (?, ?)
            """, (book_id, category_id))
    conn.commit()



def insertar_info(cursor, conn, key_name, documentos):
    for doc in documentos:
        title = doc.get("title")
        authors = doc.get("authors")  # Debe ser lista
        description = doc.get("description")
        categories = doc.get("categories")  # Debe ser lista
        published_date = doc.get("published_date")
        publisher = doc.get("publisher")
        preview_link = doc.get("preview_link")
        info_link = doc.get("info_link")
        image_link = doc.get("image_link")
        ratings_count = doc.get("ratings_count")

        # Insertar libro
        book_id = insertar_libro(conn, cursor, key_name, title, description,
                                 published_date, publisher, preview_link,
                                 info_link, image_link, ratings_count)

        # Relacionar autores y categorías
        relacionar_autores_categories(cursor, conn, book_id, authors, categories)


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


def callback(ch, method, properties, body):
    key_name = body.decode('utf-8')  # mensaje recibido
    print(f"[INFO] Mensaje recibido: {key_name}")

    conn, cursor = conectar_MariaDB()  # conectar MariaDB
    print("[INFO] Conectado a MariaDB")

    # Verificar si ya se procesó
    existe = buscar_objeto(cursor, MARIADB_TABLE, key_name)
    print(f"[INFO] ¿Ya procesado? {existe}")

    if existe:
        print("[INFO] Objeto ya procesado. Reconociendo mensaje...")
        ch.basic_ack(delivery_tag=method.delivery_tag)  # no se hace nada
        #amazon-books/part-00099-7aac03f4-2533-4b8f-8be9-9057d831d6be-c000.json
    else:
        try:
            # 1. Descargar desde S3
            print("[INFO] Descargando objeto desde S3...")
            file_path = descargar_objeto(key_name)
            print(f"[INFO] Objeto descargado en: {file_path}")

            # 2. Parsear JSON/parquet
            print("[INFO] Procesando objeto...")
            documentos = procesar_objeto(file_path)
            print(f"[INFO] Documentos extraídos: {len(documentos)}")

            # 3. Generar embeddings
            print("[INFO] Generando embeddings...")
            documentos = embedding_todos_documentos(documentos)
            print("[INFO] Embeddings generados")

            # 4. Guardar en Elasticsearch (solo reviews)
            print("[INFO] Guardar en Elasticsearch")
            guardar_libros_elasticsearch(documentos)

            # 5. Guardar en MariaDB
            procesado = True
            print("[INFO] Insertando registro inicial en MariaDB...")
            insertar_object(cursor, conn, key_name, documentos, procesado)
            print("[INFO] Insertando información en MariaDB...")
            insertar_info(cursor, conn, key_name, documentos)
            print("[INFO] Información insertada en MariaDB")

            # 6. Marcar como procesado
            procesado = True
            #insertar_object(cursor, conn, key_name, documentos, procesado)
            print("[INFO] Objeto marcado como procesado")

            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("[INFO] Mensaje confirmado (ack)")
        except Exception as e:
            print(f"[ERROR] Ocurrió un error: {e}")

def main():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBIT_MQ,
        credentials=credentials,
        heartbeat=2000,
        blocked_connection_timeout=300
    )

    # Intentar conexión hasta que RabbitMQ esté listo
    max_retries = 30
    for intento in range(max_retries):
        try:
            print(f"[INFO] Intentando conectar a RabbitMQ... intento {intento+1}/{max_retries}")
            connection = pika.BlockingConnection(parameters)
            print("[INFO] Conexión a RabbitMQ exitosa")
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[WARN] No se pudo conectar a RabbitMQ (intento {intento+1}): {e}")
            time.sleep(10)
    else:
        print("[ERROR] No se pudo conectar a RabbitMQ tras varios intentos")
        return

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    print("[INFO] Esperando mensajes...")
    channel.start_consuming()
