import os
import pika
import mariadb
import requests
import boto3
import time
import pandas as pd
from elasticsearch import Elasticsearch
from prometheus_client import Counter, Histogram, start_http_server

# --- MÉTRICAS ---
objetos_procesados = Counter('total_objetos_procesados', 'Cantidad de objetos procesados', ['componente'])
objetos_error = Counter('total_objetos_error', 'Cantidad de objetos con error', ['componente'])
tiempo_objeto = Histogram('tiempo_procesamiento_objeto', 'Tiempo de procesamiento por objeto (segundos)', ['componente'])

# Iniciar servidor de métricas en el puerto 8000
start_http_server(8000)
print("[INFO] Servidor de métricas Prometheus iniciado en el puerto 8000")

# Variables de entorno
# General
HOSTNAME = os.getenv('HOSTNAME')
XPATH = os.getenv('XPATH')
DATA = os.getenv('DATAFROMK8S')
ENDPOINT = os.getenv("EMBEDDINGENDPOINT")

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
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    s3.download_file(AWS_BUCKET, key_name, download_path)
    return download_path

#Procesar objeto y guardarlo en una lista de diccionarios
def procesar_objeto(file_path):
    dataFrame = pd.read_parquet(file_path)
    dataFrame.columns = [col.lower() for col in dataFrame.columns]
    return dataFrame.to_dict(orient='records')


# # Embeddings

# #Hacer request a huggingface 
# def crear_embedding(texto):
#     if not texto:
#         return None
#     try:
#         response = requests.post(ENDPOINT, json={"text": texto}, timeout=10)
#         if response.status_code == 200:
#             return response.json().get("embedding")
#         else:
#             print(f"Error embedding {response.status_code}: {response.text}")
#             return None
#     except Exception as e:
#         print(f"Error creando embedding: {e}")
#         return None


# #Procesar todos los documentos
# def embedding_todos_documentos(documentos):
#     for idx, doc in enumerate(documentos, start=1):
#         doc["embeddings"] = {"text": None, "summary": None}
#         if "text" in doc:
#             doc["embeddings"]["text"] = crear_embedding(doc["text"])
#         if "review_summary" in doc:
#             doc["embeddings"]["summary"] = crear_embedding(doc["review_summary"])
#         print(f"Documento {idx}/{len(documentos)} procesado")
#     return documentos


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
                print("Conexión a Elasticsearch exitosa")
                return es
        except Exception as e:
            print(f"Intento {intento+1} fallido: {e}")
        time.sleep(delay)
    print("No se pudo conectar a Elasticsearch tras varios intentos")
    return None

#Guardar las reviws en índices de elasticsearch
def guardar_reviews_elasticsearch(documentos):
    es = conectar_elasticsearch()
    if es is None:
        return

    for i, doc in enumerate(documentos, start=1):
        doc_sin_embedding = doc.copy()
        doc_sin_embedding.pop("embeddings", None)

        try:
            es.index(index=ELASTIC_INDEX_REVIEWS, document=doc)
        except Exception as e:
            print(f"Error insertando en {ELASTIC_INDEX_REVIEWS} (doc {i}): {e}")

        try:
            es.index(index=ELASTIC_INDEX_NREVIEWS, document=doc_sin_embedding)
        except Exception as e:
            print(f"Error insertando en {ELASTIC_INDEX_NREVIEWS} (doc {i}): {e}")


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

#Inserta review. Si el libro ya se encuentra en la base de datos, la guarda
#Si el libro de la review no se ha procesado, se queda en tabla auxiliar "pendientes"
def insertar_review(conn, cursor, object_key, title=None, price=None, user_id=None,
                    profile_name=None, review_helpfulness=None, review_score=None,
                    review_time=None, review_summary=None, review_text=None):
    try:
        cursor.execute(f"SELECT id FROM {MARIADB_TABLE_BOOKS} WHERE LOWER(title)=LOWER(?) LIMIT 1", (title,))
        book_row = cursor.fetchone()
        book_id = book_row[0] if book_row else None

        if book_id:
            # Inserta review normal
            query = f"""
                INSERT INTO {MARIADB_TABLE_REVIEWS}
                (object_key, book_id, title, price, user_id, profile_name, 
                 review_helpfulness, review_score, review_time, review_summary, review_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                object_key, book_id, title, price, user_id, profile_name,
                review_helpfulness, review_score, review_time, review_summary, review_text
            ))
        else:
            # Inserta review sin fk y la marca pendiente
            query = f"""
                INSERT INTO {MARIADB_TABLE_REVIEWS}
                (object_key, book_id, title, price, user_id, profile_name, 
                 review_helpfulness, review_score, review_time, review_summary, review_text)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                object_key, title, price, user_id, profile_name,
                review_helpfulness, review_score, review_time, review_summary, review_text
            ))

            # Guardar pendiente
            cursor.execute(f"""
                INSERT INTO {MARIADB_PENDING} (review_object_key, book_title, processed)
                VALUES (?, ?, FALSE)
            """, (object_key, title))

        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        print(f"Error insertando review: {e}")

#Se insertan todos los documentos
def insertar_info(cursor, conn, object_key, documentos):
    for doc in documentos:
        insertar_review(
            conn, cursor, object_key,
            title=doc.get("title"),
            price=doc.get("price"),
            user_id=doc.get("user_id"),
            profile_name=doc.get("profile_name"),
            review_helpfulness=doc.get("review_helpfulness"),
            review_score=doc.get("review_score"),
            review_time=doc.get("review_time"),
            review_summary=doc.get("review_summary"),
            review_text=doc.get("review_text")
        )

#Arregla las reviews que no tienen fk a libro
def arreglar_reviews_pendientes():
    """Actualiza los reviews sin book_id cuando el libro ya existe."""
    conn, cursor = conectar_MariaDB()
    query = f"""
        SELECT p.id, r.id AS review_id, b.id AS book_id
        FROM {MARIADB_PENDING} p
        JOIN {MARIADB_TABLE_REVIEWS} r ON r.object_key = p.review_object_key
        JOIN {MARIADB_TABLE_BOOKS} b ON LOWER(b.title) = LOWER(p.book_title)
        WHERE p.processed = FALSE;
    """
    cursor.execute(query)
    pendientes = cursor.fetchall()

    for p_id, review_id, book_id in pendientes:
        cursor.execute(f"UPDATE {MARIADB_TABLE_REVIEWS} SET book_id=? WHERE id=?", (book_id, review_id))
        cursor.execute(f"UPDATE {MARIADB_PENDING} SET processed=TRUE WHERE id=?", (p_id,))
        conn.commit()

    print(f"[INFO] Reconciliadas {len(pendientes)} reviews pendientes.")
    cursor.close()
    conn.close()

#Inserta en la tabla de objetos el objeto y numero de documentos
def insertar_object(cursor, conn, key_name, documentos, procesado):
    insert_query = f"""
        INSERT INTO {MARIADB_TABLE}
        (key_name, num_documents, procesado)
        VALUES (?, ?, ?)
    """
    try:
        cursor.execute(insert_query, (key_name, len(documentos), procesado))
        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        print(f"Error insertando object: {e}")


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
        # documentos = embedding_todos_documentos(documentos)
        guardar_reviews_elasticsearch(documentos)

        insertar_info(cursor, conn, key_name, documentos)
        insertar_object(cursor, conn, key_name, documentos, True)

        arreglar_reviews_pendientes()


        objetos_procesados.labels(componente="ingest").inc(len(documentos))
        tiempo_objeto.labels(componente="ingest").observe(time.time() - start_time)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[ERROR] Ocurrió un error: {e}")
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
    max_retries = 30
    for intento in range(max_retries):
        try:
            print(f"[INFO] Intentando conectar a RabbitMQ... intento {intento+1}/30")
            connection = pika.BlockingConnection(parameters)
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"[WARN] No se pudo conectar, reintentando...")
            time.sleep(10)
    else:
        print("[ERROR] RabbitMQ no disponible.")
        return

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    print("[INFO] Esperando mensajes...")
    channel.start_consuming()


