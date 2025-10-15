import os
import sys
import pika
import json
import time
import mariadb
import requests
import boto3
from elasticsearch import Elasticsearch
from prometheus_client import Counter, Histogram, start_http_server
import ast  
from datetime import datetime
from elasticsearch.helpers import bulk #para cargar los datos más rápido
import logging

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# --- MÉTRICAS ---
objetos_procesados = Counter('total_objetos_procesados', 'Cantidad de objetos procesados', ['componente'])
objetos_error = Counter('total_objetos_error', 'Cantidad de objetos con error', ['componente'])
tiempo_objeto = Histogram('tiempo_procesamiento_objeto', 'Tiempo de procesamiento por objeto (segundos)', ['componente'])

# Iniciar servidor de métricas en el puerto 8000
start_http_server(8000)

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
    cursor.execute(query, (key_buscado,))#busca el objeto en la tabla objetos
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
    download_path = os.path.join(XPATH, key_name)
    os.makedirs(os.path.dirname(download_path), exist_ok=True) #se asegura que la dirección sea válida

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
                    logger.error("Error decodificando línea: %s", line)
    return documentos

# #Embeddings
#Crea embeddings haciendo un request al endpoint
def crear_embedding(texto):
    if not texto or texto.strip() == "":
        return None 
    try:
        data = {"text": texto}
        response = requests.post(EMBEDDINGENDPOINT, json=data)  # timeout para no quedarse pegado
        response.raise_for_status()  
        embedding = response.json().get("embedding")
        if embedding is None:
            logger.warning(f"No se recibió embedding para el texto: {texto[:50]}...")
        return embedding
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la petición al endpoint {EMBEDDINGENDPOINT}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado generando embedding: {e}")
        return None

#crear embedding, cargar a elastic y meter a mariadb
# def embedding_todos_documentos(documentos):
#     for i, doc in enumerate(documentos, start=1):
#         doc["embeddings"] = None
#         if "description" in doc and doc["description"]:
#             texto = doc["description"]
#             embedding = crear_embedding(texto)
#             if embedding is not None:
#                 doc["embeddings"] = embedding
#         logger.info(f"Procesado documento {i}/{len(documentos)}")
#     return documentos

def embedding_todos_documentos(documentos, limite=5):
    total = len(documentos)
    logger.info(f"Generando embeddings para {min(limite, total)} de {total} documentos...")

    for i, doc in enumerate(documentos[:limite], start=1):  # solo los primeros 'limite'
        doc["embeddings"] = None
        if "description" in doc and doc["description"]:
            texto = doc["description"]
            embedding = crear_embedding(texto)
            if embedding is not None:
                doc["embeddings"] = embedding
        logger.info(f"Procesado documento {i}/{min(limite, total)}")

    # para los demás, se deja embeddings=None explícitamente
    for doc in documentos[limite:]:
        doc["embeddings"] = None

    return documentos


#Elastic
#Conectar a elasticsearch
def conectar_elasticsearch(max_retries=10, delay=5):
    for intento in range(max_retries):
        try:
            es = Elasticsearch(
                f"http://{ELASTIC_HOST}:9200",
                basic_auth=(ELASTIC_USER, ELASTIC_PASS)
            )
            if es.ping():
                logger.info("Conexión a Elasticsearch exitosa")
                return es
        except Exception as e:
            logger.warning(f"Intento {intento+1} fallido: {e}")
        time.sleep(delay)
    logger.error("No se pudo conectar a Elasticsearch tras varios intentos")
    return None



#Guardar todos los libros en books y nbooks
def guardar_libros_elasticsearch(documentos):
    es = conectar_elasticsearch()
    if es is None:
        logger.error("No se insertarán documentos porque Elasticsearch no está disponible.")
        return
    datos_books = []
    datos_nbooks = []

    for doc in documentos:
        if "title" in doc and doc["title"]:
            dato_book = { "_index": ELASTIC_INDEX_BOOKS, "_source": doc }
            datos_books.append(dato_book)

            # Le hace pop al embedding para asegurarse de que no lo guarde
            doc_sin_embedding = doc.copy()
            doc_sin_embedding.pop("embeddings", None)
            dato_nbook = {"_index": ELASTIC_INDEX_NBOOKS, "_source": doc_sin_embedding}
            datos_nbooks.append(dato_nbook)
        else:
            logger.warning(f"Book ignorado en elastic: no tiene título")
            objetos_error.labels(componente="ingest").inc()
            return
    # Enviar en bulk a elastic
    try:
        bulk(es, datos_books, raise_on_error=False)
        bulk(es, datos_nbooks, raise_on_error=False)
    except Exception as e:
        logger.error(f"Bulk insert falló: {e}")


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

#Insertar autores
def insertar_author(cursor, conn, author_name):
    if not author_name or not author_name.strip():
        return None  # no insertamos nombres vacíos
    
    author_name = author_name.strip()

    query = f"INSERT IGNORE INTO {MARIADB_TABLE_AUTHORS} (name) VALUES (?)"
    cursor.execute(query, (author_name,))

    cursor.execute(f"SELECT id FROM {MARIADB_TABLE_AUTHORS} WHERE name = ?", (author_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        logger.warning(f"No se encontró el autor '{author_name}' después de insertar.")
        return None

#Insertar categoría (sin repetir) en la tabla
def insertar_category(cursor, conn, category_name):
    if not category_name or not category_name.strip():
        return None
    
    category_name = category_name.strip()

    query = f"INSERT IGNORE INTO {MARIADB_TABLE_CATEGORIES} (name) VALUES (?)"
    cursor.execute(query, (category_name,))

    cursor.execute(f"SELECT id FROM {MARIADB_TABLE_CATEGORIES} WHERE name = ?", (category_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        logger.warning(f" No se encontró la categoría '{category_name}' después de insertar.")
        return None

#Insertar libro en la tabla
def insertar_libro(conn, cursor, object_key, title=None, description=None,
                   published_date=None, publisher=None, preview_link=None,
                   info_link=None, image_link=None, ratings_count=None):
    if not title:
        logger.warning(f"Book ignorado en mariadb: no tiene título")
        return
    query = f"""
    INSERT INTO {MARIADB_TABLE_BOOKS}
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
        author_name = str(authors).strip()  # convierte todo en string, por si acaso
        author_id = insertar_author(cursor, conn, author_name)
        if author_id:
            cursor.execute(f"""
                INSERT IGNORE INTO {MARIADB_TABLE_AUTHORS_BOOKS} (book_id, author_id)
                VALUES (?, ?)
            """, (book_id, author_id))

    # Categorías
    if categories:
        category_name = str(categories).strip()
        category_id = insertar_category(cursor, conn, category_name)
        if category_id:
            cursor.execute(f"""
                INSERT IGNORE INTO {MARIADB_TABLE_CATEGORIES_BOOKS} (book_id, category_id)
                VALUES (?, ?)
            """, (book_id, category_id))

    conn.commit()


# Validar que la fecha tenga el formato 
def normalizar_fecha(fecha_str):
    if not fecha_str:
        return None

    s = str(fecha_str).strip()
    formatos = [ "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y", "%Y-%m", "%Y/%m", "%Y"]

    for formato in formatos:
        try:
            dt = datetime.strptime(s, formato)
            if formato in ("%Y-%m", "%Y/%m"):
                objetos_error.labels(componente="ingest").inc()
                dt = dt.replace(day=1)
            elif formato == "%Y":
                objetos_error.labels(componente="ingest").inc()
                dt = dt.replace(month=1, day=1)
            return dt.date()
        except ValueError:
            continue
    objetos_error.labels(componente="ingest").inc()
    return None


#Quitar ratingscount si no es un numero
def normalizar_ratings(rating):
    try:
        if rating is None:
            return None
        return float(rating)
    except (ValueError, TypeError):
        objetos_error.labels(componente="ingest").inc()
        return None
        

def limpiar_texto(texto):
    if texto:
        return texto.replace('""', '"').strip(' "')
    return texto

# Insertar documento
def insertar_info(cursor, conn, key_name, documentos, cantidad=100):
    count = 0
    for doc in documentos:
        title = doc.get("title")
        description = doc.get("description")
        published_date = normalizar_fecha(doc.get("publisheddate"))
        publisher = doc.get("publisher")
        preview_link = doc.get("previewlink")
        info_link = doc.get("infolink")
        image_link = doc.get("image")
        ratings_count = normalizar_ratings(doc.get("ratingscount"))

        # Insertar libro
        book_id = insertar_libro(
            conn, cursor, key_name, title, description,
            published_date, publisher, preview_link,
            info_link, image_link, ratings_count
        )

        if not book_id:
            continue  # libro no insertado, saltar

        # Insertar autores y categorías
        authors = limpiar_texto(doc.get("authors"))
        categories = limpiar_texto(doc.get("categories"))
        relacionar_autores_categories(cursor, conn, book_id, authors=authors, categories=categories)

        count += 1
        if count % cantidad == 0:
            conn.commit() 

    conn.commit() 


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
        logger.error(f"Error insertando object: {e}")

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
            logger.info("Objeto marcado como procesado")


            objetos_procesados.labels(componente="ingest").inc(len(documentos))
            tiempo_objeto.labels(componente="ingest").observe(time.time() - start_time)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f" Ocurrió un error: {e}")
            objetos_error.labels(componente="ingest").inc()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        finally:
            cursor.close()
            conn.close()

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
            connection = pika.BlockingConnection(parameters)
            logger.info(" Conexión a RabbitMQ exitosa")
            break
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f" No se pudo conectar a RabbitMQ (intento {intento+1}): {e}")
            time.sleep(10)
    else:
        logger.error(" No se pudo conectar a RabbitMQ tras varios intentos")
        return

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    logger.info(" Esperando mensajes...")
    channel.start_consuming()
