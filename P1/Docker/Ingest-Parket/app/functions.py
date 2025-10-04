import os
import pika
import mariadb
import requests
import boto3
import pandas as pd
from elasticsearch import Elasticsearch

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
MARIADB_TABLE_REVIEWS = os.getenv('MARIADB_TABLE_REVIEWS')

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
    dataFrame = pd.read_parquet(file_path) #pandas lee parquet como dataFrame
    dataFrame.columns = [col.lower() for col in dataFrame.columns] #todo a minusculas
    documentos = dataFrame.to_dict(orient='records')
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
        doc["embeddings"] = {"text": None, "summary": None}
        if "text" in doc:
            embedding_text = crear_embedding(doc["text"])
            if embedding_text is not None:
                doc["embeddings"]["text"] = embedding_text
        if "review_summary" in doc:
            embedding_summary = crear_embedding(doc["review_summary"])
            if embedding_summary is not None:
                doc["embeddings"]["summary"] = embedding_summary
    return documentos

########################Elastic
# def conectar_elasticsearch():
#     try:
#         es = Elasticsearch(
#             ELASTIC_HOST,
#             http_auth=(ELASTIC_USER, ELASTIC_PASS),
#             scheme="http",
#             port=9200
#         )
#         if not es.ping():
#             print("No se pudo conectar a Elasticsearch")
#             return None
#         return es
#     except Exception as e:
#         print("Error conectando a Elasticsearch:", e)
#         return None

# def guardar_en_elasticsearch(documentos):
#     es = conectar_elasticsearch()
#     if es is None:
#         return

#     for doc in documentos:
#         doc_sin_embedding = doc.copy()
#         doc_sin_embedding.pop("embeddings", None)

#         try:
#             es.index(index=ELASTIC_INDEX_BOOKS, document=doc)
#         except Exception as e:
#             print("Error insertando en books/reviews:", e)

#         try:
#             es.index(index=ELASTIC_INDEX_NBOOKS, document=doc_sin_embedding)
#         except Exception as e:
#             print("Error insertando en nbooks/nreviews:", e)


################################


def insertar_review(conn, cursor, object_key, title=None, price=None, user_id=None,
                    profile_name=None, review_helpfulness=None, review_score=None,
                    review_time=None, review_summary=None, review_text=None):
    query = f"""
    INSERT INTO {MARIADB_TABLE_REVIEWS}
    (object_key, book_id, title, price, user_id, profile_name, review_helpfulness, 
     review_score, review_time, review_summary, review_text)
    VALUES (
        ?,
        (SELECT id FROM {MARIADB_TABLE_BOOKS} WHERE LOWER(title) = LOWER(?) LIMIT 1),
        ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """
    try:
        cursor.execute(query, (
            object_key,
            title,  # para el subquery book_id
            title,
            price,
            user_id,
            profile_name,
            review_helpfulness,
            review_score,
            review_time,
            review_summary,
            review_text
        ))
        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        print(f"Error insertando review: {e}")


def insertar_info(cursor, conn, object_key, documentos):
    for doc in documentos:
        title = doc.get("title")
        price = doc.get("price")
        user_id = doc.get("user_id")
        profile_name = doc.get("profile_name")
        review_helpfulness = doc.get("review_helpfulness")
        review_score = doc.get("review_score")
        review_time = doc.get("review_time")
        review_summary = doc.get("review_summary")
        review_text = doc.get("review_text")

        insertar_review(
            conn, cursor, object_key,
            title, price, user_id,
            profile_name, review_helpfulness, review_score,
            review_time, review_summary, review_text
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
        guardar_en_elasticsearch(documentos)
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