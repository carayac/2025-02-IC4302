import os
import pika
import json
import time
import mariadb
import requests
import boto3
from elasticsearch import Elasticsearch
from prometheus_client import Counter, Histogram, start_http_server

# --- MÉTRICAS ---
objetos_procesados = Counter('total_objetos_procesados', 'Cantidad de objetos procesados', ['componente'])
objetos_error = Counter('total_objetos_error', 'Cantidad de objetos con error', ['componente'])
tiempo_objeto = Histogram('tiempo_procesamiento_objeto', 'Tiempo de procesamiento por objeto (segundos)', ['componente'])

# Iniciar servidor de métricas en el puerto 8000
start_http_server(8000)
print("[INFO] Servidor de métricas Prometheus iniciado en el puerto 8000")

#Variables globales
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
ELASTIC_INDEX_BOOKS = os.getenv('ELASTIC_INDEX_BOOKS')  
ELASTIC_INDEX_NBOOKS = os.getenv('ELASTIC_INDEX_NBOOKS')  

# AWS S3 Bucket
AWS_BUCKET = os.getenv('AWS_BUCKET')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')

#Descargar objeto desde AWS
#Determinar si el objeto fue procesado
def buscar_objeto(cursor, tabla, key_buscado):
    query = f"SELECT * FROM {tabla} WHERE key_name = %s"
    cursor.execute(query, (key_buscado,))
    resultado = cursor.fetchone()
    if resultado is None:
        return False
    else:
        return True

#Descarga objeto de bucket
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

#Procesa objetos del bucket
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

# #Embeddings
#Crea embeddings haciendo un request al endpoint
def crear_embedding(texto):
    try:
        data = {"text": texto}
        response = requests.post(EMBEDDINGENDPOINT, json=data, timeout=10)  # timeout para no quedarse pegado
        response.raise_for_status()  
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

#embedding de todos los documentos
def embedding_todos_documentos(documentos):
    for i, doc in enumerate(documentos, start=1):
        doc["embeddings"] = None
        if "description" in doc and doc["description"]:
            texto = doc["description"]
            embedding = crear_embedding(texto)
            if embedding is not None:
                doc["embeddings"] = embedding
        print(f"Procesado documento {i}/{len(documentos)}")
    return documentos

#Elastic
#Conectar a elasticsearch
def conectar_elasticsearch(max_retries=50, delay=5):
    for intento in range(max_retries):
        try:
            es = Elasticsearch(
                f"http://{ELASTIC_HOST}:9200",
                basic_auth=(ELASTIC_USER, ELASTIC_PASS)
            )
            if es.ping():
                print("Conexión a Elasticsearch exitosa")
                return es
        except Exception as e:
            print(f"Intento {intento+1} fallido: {e}")
        time.sleep(delay)
    print("No se pudo conectar a Elasticsearch tras varios intentos")
    return None


#Guardar todos los libros en books y nbooks
def guardar_libros_elasticsearch(documentos):
    es = conectar_elasticsearch()
    if es is None:
        print("No se insertarán documentos porque Elasticsearch no está disponible.")
        return

    index_books = os.getenv("ELASTIC_INDEX_BOOKS", "books")
    index_nbooks = os.getenv("ELASTIC_INDEX_NBOOKS", "nbooks")

    for i, doc in enumerate(documentos, start=1):
        doc_sin_embedding = doc.copy()
        doc_sin_embedding.pop("embeddings", None)

        try:
            es.index(index=index_books, document=doc)
        except Exception as e:
            print(f"Error insertando en {index_books} (documento {i}):", e)

        try:
            es.index(index=index_nbooks, document=doc_sin_embedding)
        except Exception as e:
            print(f"Error insertando en {index_nbooks} (documento {i}):", e)

# Mariadb
#Conexión a MariaDB
def conectar_MariaDB():
    conn = mariadb.connect(
        host=MARIADB_HOST,
        user=MARIADB_USER,
        password=MARIADB_PASS
    )
    cursor = conn.cursor()
    cursor.execute(f"USE {MARIADB_DB}")
    return conn, cursor

#Insertar autor (sin repetir) en la tabla
def insertar_author(cursor, conn, author_name):
    query = f"INSERT IGNORE INTO {MARIADB_TABLE_AUTHORS} (name) VALUES (?)"
    cursor.execute(query, (author_name,))
    conn.commit()

    # Obtener el ID del autor
    cursor.execute(f"SELECT id FROM {MARIADB_TABLE_AUTHORS} WHERE name = ?", (author_name,))
    return cursor.fetchone()[0]

#Insertar categoría (sin repetir) en la tabla
def insertar_category(cursor, conn, category_name):
    query = f"INSERT IGNORE INTO {MARIADB_TABLE_CATEGORIES} (name) VALUES (?)"
    cursor.execute(query, (category_name,))
    conn.commit()

    # Obtener el ID de la categoría
    cursor.execute(f"SELECT id FROM {MARIADB_TABLE_CATEGORIES} WHERE name = ?", (category_name,))
    return cursor.fetchone()[0]

#Insertar libro en la tabla
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

#Relacionar los autores y las categorías a los libros
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


#Insertar todos los documentos
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

#Insertar el objeto como procesado y con numero de docs
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

#callback
def callback(ch, method, properties, body):
    key_name = body.decode('utf-8')  # mensaje recibido
    conn, cursor = conectar_MariaDB()  # conectar MariaDB
    existe = buscar_objeto(cursor, MARIADB_TABLE, key_name)

    if existe:
        ch.basic_ack(delivery_tag=method.delivery_tag)  # no se hace nada
    else:
        start_time = time.time()
        try:
            # 1. Descargar desde S3
            file_path = descargar_objeto(key_name)

            # 2. Parsear JSON
            documentos = procesar_objeto(file_path)

            # 3. Generar embeddings
            documentos = embedding_todos_documentos(documentos)

            # 4. Guardar en Elasticsearch (solo reviews)
            guardar_libros_elasticsearch(documentos)

            # 5. Guardar en MariaDB
            insertar_info(cursor, conn, key_name, documentos)

            # 6. Marcar como procesado
            insertar_object(cursor, conn, key_name, documentos, True)
            print("Objeto marcado como procesado")

            objetos_procesados.labels(componente="ingest").inc(len(documentos))
            tiempo_objeto.labels(componente="ingest").observe(time.time() - start_time)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[ERROR] Ocurrió un error: {e}")
            objetos_error.labels(componente="ingest").inc()
            ch.basic_ack(delivery_tag=method.delivery_tag)

#main
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
