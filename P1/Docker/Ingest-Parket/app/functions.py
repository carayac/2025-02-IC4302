import os
import pika
import mariadb
import requests
import boto3
import time
import pandas as pd
from elasticsearch import Elasticsearch
from prometheus_client import Counter, Histogram, start_http_server
from datetime import datetime, timezone
from elasticsearch.helpers import bulk
import threading
import logging
import sys

# Configuración de logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- MÉTRICAS ---
objetos_procesados = Counter('total_objetos_procesados', 'Cantidad de objetos procesados', ['componente'])
objetos_error = Counter('total_objetos_error', 'Cantidad de objetos con error', ['componente'])
tiempo_objeto = Histogram('tiempo_procesamiento_objeto', 'Tiempo de procesamiento por objeto (segundos)', ['componente'])

# Iniciar servidor de métricas en el puerto 8000
start_http_server(8000)

# Variables de entorno
# General
HOSTNAME = os.getenv('HOSTNAME')
XPATH = os.getenv('XPATH')
DATA = os.getenv('DATAFROMK8S')
ENDPOINT = os.getenv("EMBEDDINGENDPOINT", "http://huggingface:5000/encode")

# RabbitMQ
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBIT_MQ_PASSWORD = os.getenv('RABBITMQ_PASS')
QUEUE_NAME = os.getenv('RABBITMQ_QUEUE')

# MariaDB
MARIADB_HOST = os.getenv('MARIADB')
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')
MARIADB_TABLE_BOOKS = os.getenv('MARIADB_TABLE_BOOKS')
MARIADB_TABLE_REVIEWS = os.getenv('MARIADB_TABLE_REVIEWS')
MARIADB_PENDING = os.getenv('MARIADB_TABLE_PENDING')  

# Elasticsearch
ELASTIC_HOST = os.getenv('ELASTIC_HOST')
ELASTIC_USER = os.getenv('ELASTIC_USER')
ELASTIC_PASS = os.getenv('ELASTIC_PASS')
ELASTIC_INDEX_BOOKS = os.getenv('ELASTIC_INDEX_BOOKS')
ELASTIC_INDEX_NBOOKS = os.getenv('ELASTIC_INDEX_NBOOKS')
ELASTIC_INDEX_REVIEWS = os.getenv('ELASTIC_INDEX_REVIEWS', 'reviews')
ELASTIC_INDEX_NREVIEWS = os.getenv('ELASTIC_INDEX_NREVIEWS', 'nreviews')

# AWS S3
AWS_BUCKET = os.getenv('AWS_BUCKET')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')


# Descargar objeto desde AWS

#Revisar si un objeto ha sido procesado
def buscar_objeto(cursor, tabla, key_buscado):
    query = f"SELECT * FROM {tabla} WHERE key_name = %s"
    cursor.execute(query, (key_buscado,))
    return cursor.fetchone() is not None

#Descargar el objeto desde bucket
def descargar_objeto(key_name):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )

    download_path = os.path.join(XPATH, key_name)
    logger.info(download_path)
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    s3.download_file(AWS_BUCKET, key_name, download_path)
    return download_path

#Procesar objeto y guardarlo en una lista de diccionarios
def procesar_objeto(file_path):
    dataFrame = pd.read_parquet(file_path) #se procesan los parquet con pandas
    dataFrame.columns = [col.lower() for col in dataFrame.columns]
    return dataFrame.to_dict(orient='records')


# # Embeddings

#Hacer request a huggingface 
def crear_embedding(texto):
    if not texto:
        return None
    try:
        response = requests.post(ENDPOINT, json={"text": texto})
        if response.status_code == 200:
            return response.json().get("embedding")
        else:
            logger.error(f"Error embedding {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creando embedding: {e}")
        return None


#Procesar hasta 5 documentos para pruebas
def embedding_todos_documentos(documentos):
    for idx, doc in enumerate(documentos[:5], start=1):  # Limitar a los primeros 5
        review_summary = doc.get("review/summary")
        review_text = doc.get("review/text")
        
        # Combinar texto y generar UN embedding
        texto_combinado = f"{review_summary} {review_text}".strip()
        
        if texto_combinado:
            doc["embeddings"] = crear_embedding(texto_combinado)
        else:
            doc["embeddings"] = None
            
        logger.info(f"Documento {idx}/{min(5, len(documentos))} procesado")
    return documentos




# Elasticsearch
#Conectar a elasticsearch
def conectar_elasticsearch(max_retries=50, delay=5):
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

#Cambia formato timestamp a date
def formatear_review_time_para_elastic(doc):
    review_time = doc.get("review_time")
    if review_time:
        from datetime import datetime, timezone
        try:
            valor_int = int(float(review_time))
            if valor_int > 1e12:  # si viene en ms
                valor_int //= 1000
            date = datetime.fromtimestamp(valor_int, tz=timezone.utc)
            doc["review/time"] = date.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OSError):
            pass  # si no es numero, dejarlo como está
    return doc

#Guardar las reviws en índices de elasticsearch
def guardar_reviews_elasticsearch(documentos):
    es = conectar_elasticsearch()
    if es is None:
        logger.error("No se insertarán documentos porque Elasticsearch no está disponible.")
        return
    datos_reviews = []
    datos_nreviews = []

    for doc in documentos:
        doc=formatear_review_time_para_elastic(doc)
        if "title" in doc and doc["title"]:
            dato_review = { "_index": ELASTIC_INDEX_REVIEWS, "_source": doc }
            datos_reviews.append(dato_review)

            # Le hace pop al embedding para asegurarse de que no lo guarde
            doc_sin_embedding = doc.copy()
            doc_sin_embedding.pop("embeddings", None)
            dato_nreview = {"_index": ELASTIC_INDEX_NREVIEWS, "_source": doc_sin_embedding}
            datos_nreviews.append(dato_nreview)
        else:
            logger.warning(f"[WARN] Review ignorada en elastic: no tiene título")
            return
    try:
        bulk(es, datos_reviews, raise_on_error=False)
        bulk(es, datos_nreviews, raise_on_error=False)
    except Exception as e:
        logger.error(f"[ERROR] Bulk insert falló: {e}")


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


# Arregla las reviews que no tienen FK a libro
def arreglar_reviews_pendientes(batch_size=500):
    try:
        conn, cursor = conectar_MariaDB()

        # Obtener todos los libros existentes
        cursor.execute(f"SELECT id, LOWER(title) FROM {MARIADB_TABLE_BOOKS}")
        libros = {title: book_id for book_id, title in cursor.fetchall()}

        # Obtener las reviews pendientes
        cursor.execute(f"""
            SELECT review_id, book_title
            FROM {MARIADB_PENDING}
            WHERE processed = FALSE
            LIMIT {batch_size}
        """)
        pendientes = cursor.fetchall()

        filas_actualizadas = 0

        for review_id, book_title in pendientes:
            book_id = libros.get(book_title.lower())
            if book_id:
                # Actualiza review con book_id
                cursor.execute(f"""
                    UPDATE {MARIADB_TABLE_REVIEWS}
                    SET book_id = ?
                    WHERE id = ?
                """, (book_id, review_id))

                # Marca pendiente como procesada
                cursor.execute(f"""
                    UPDATE {MARIADB_PENDING}
                    SET processed = TRUE
                    WHERE review_id = ?
                """, (review_id,))
                filas_actualizadas += 1

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"[INFO] {filas_actualizadas} reviews pendientes actualizadas")
        return filas_actualizadas

    except mariadb.Error as e:
        logger.error(f"[ERROR] Error en arreglar_reviews_pendientes: {e}")
        return 0


# Normalizar review_time
def normalizar_review_time(value):
    if not value:
        return None
    try:
        valor_int = int(float(value))
        if valor_int > 1e12: #si el value es mayor a 1 billon, se connvierte a segundos
            valor_int //= 1000
        date = datetime.fromtimestamp(valor_int, tz=timezone.utc) #convierte el timestamp a un date time
        return date.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OSError):
        pass #si no lo puede convertir a int ignora el error y revisa si es un string

    formatos = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for formato in formatos:
        try:
            date = datetime.strptime(str(value).strip(), formato)
            return date.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue #prueba todos los formatos

    objetos_error.labels(componente="ingest").inc()
    return None


# Normalizar review_score
def normalizar_review_score(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        objetos_error.labels(componente="ingest").inc()
        return None

# Normalizar price
def normalizar_price(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        objetos_error.labels(componente="ingest").inc()
        return None
    
#Inserta una review en Mariadb y si no esta el book la guarda en pendientes
def insertar_review(conn, cursor, object_key, title=None, price=None, user_id=None,
                    profile_name=None, review_helpfulness=None, review_score=None,
                    review_time=None, review_summary=None, review_text=None):
    if not title:
        logger.warning(f"[WARN] Review ignorada en mariadb: no tiene título")
        objetos_error.labels(componente="ingest").inc()
        return

    try:
        # Buscar si el libro ya existe
        cursor.execute(f"SELECT id FROM {MARIADB_TABLE_BOOKS} WHERE title=? LIMIT 1", (title,))
        book_row = cursor.fetchone()
        book_id = book_row[0] if book_row else None

        if book_id:
            # Inserta review
            query = f"""
                INSERT INTO {MARIADB_TABLE_REVIEWS}
                (book_id, object_key, title, price, user_id, profile_name, 
                 review_helpfulness, review_score, review_time, review_summary, review_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                book_id, object_key, title, price, user_id, profile_name,
                review_helpfulness, review_score, review_time, review_summary, review_text
            ))
        else:
            # Inserta review sin book_id
            query = f"""
                INSERT INTO {MARIADB_TABLE_REVIEWS}
                (book_id, object_key, title, price, user_id, profile_name, 
                 review_helpfulness, review_score, review_time, review_summary, review_text)
                VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                object_key, title, price, user_id, profile_name,
                review_helpfulness, review_score, review_time, review_summary, review_text
            ))

            # Obtener el ID
            review_id = cursor.lastrowid

            # Guardar pendiente solo con el review_id y el título 
            cursor.execute(f"""
                INSERT INTO {MARIADB_PENDING} (review_id, book_title, processed)
                VALUES (?, ?, FALSE)
            """, (review_id, title))

        conn.commit()

    except mariadb.Error as e:
        conn.rollback()
        logger.error(f"[ERROR] Error insertando review: {e}")




#Se insertan todos los documentos
def insertar_info(cursor, conn, object_key, documentos):
    for doc in documentos:
        insertar_review(
            conn, cursor, object_key,
            title=doc.get("title"),
            price = normalizar_price(doc.get("price")),
            user_id=doc.get("user_id"),
            profile_name=doc.get("profilename"),
            review_helpfulness=doc.get("review/helpfulness"),
            review_score = normalizar_review_score(doc.get("review/score")),
            review_time = normalizar_review_time(doc.get("review/time")),
            review_summary=doc.get("review/summary"),
            review_text=doc.get("review/text")
        )

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


#Aux
def thread_arreglar_pendientes(batch_size=500):
    while True:
        filas = arreglar_reviews_pendientes(batch_size)
        if filas == 0:
            time.sleep(30)  # no hay pendientes
        else:
            time.sleep(10)

#Callback
#Llama a cada función
def callback(ch, method, properties, body):
    key_name = body.decode('utf-8')
    conn, cursor = conectar_MariaDB()

    if buscar_objeto(cursor, MARIADB_TABLE, key_name):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    start_time = time.time()
    try:
        file_path = descargar_objeto(key_name)

        documentos = procesar_objeto(file_path)

        documentos = embedding_todos_documentos(documentos)

        guardar_reviews_elasticsearch(documentos)

        insertar_info(cursor, conn, key_name, documentos)

        insertar_object(cursor, conn, key_name, documentos, True)

        cursor.close()
        conn.close()

        logger.info("Objeto marcado como procesado")

        objetos_procesados.labels(componente="ingest").inc(len(documentos))
        tiempo_objeto.labels(componente="ingest").observe(time.time() - start_time)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"[ERROR] Ocurrió un error: {e}")
        objetos_error.labels(componente="ingest").inc()
        ch.basic_ack(delivery_tag=method.delivery_tag)


# Main
def main():
    credentials = pika.PlainCredentials(RABBIT_MQ_USER, RABBIT_MQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBIT_MQ,
        credentials=credentials,
        heartbeat=2000,
        blocked_connection_timeout=300
    )
    threading.Thread(target=thread_arreglar_pendientes, daemon=True).start()
    max_retries = 30
    for intento in range(max_retries):
        try:
            connection = pika.BlockingConnection(parameters)
            break
        except pika.exceptions.AMQPConnectionError:
            logger.warning(f"[WARN] No se pudo conectar, reintentando...")
            time.sleep(10)
    else:
        logger.error("[ERROR] RabbitMQ no disponible.")
        return

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    logger.info("[INFO] Esperando mensajes...")
    channel.start_consuming()
