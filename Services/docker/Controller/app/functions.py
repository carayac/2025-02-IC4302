import os
import json
import logging
from datetime import datetime, timezone

import boto3
import hashlib
import pika
from pymongo import MongoClient

# S3
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIXES = [p.strip() for p in os.getenv("S3_PREFIXES").split(",") if p.strip()]
AWS_REGION = os.getenv("AWS_REGION")

# MongoDB
MONGO_URI = "mongodb+srv://dbUser:B1b5xCdAOZDVfjcC@productssearch.sao2plc.mongodb.net/ecomm?appName=ProductsSearch"

INGESTION_COLLECTION = "ingestion"

# RabbitMQ
RABBIT_HOST = os.getenv("RABBITMQ")
RABBIT_USER = os.getenv("RABBITMQ_USER")
RABBIT_PASS = os.getenv("RABBITMQ_PASS")  
RABBIT_QUEUE_PARSE = os.getenv("RABBITMQ_QUEUE_PARSE")

# Config de logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("controller")


# Definicion de fecha actual para colección
def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def calculate_md5(bucket: str, key: str, chunk_size: int = 8192) -> str:
    """
    Calcula el hash MD5 real del contenido del archivo, leyendo el body que da el s3.
    Lee el objeto por partes para evitar cargarlo todo en memoria.
    """
    s3 = boto3.client("s3")
    hasher = hashlib.md5()
    
    # Descargar el objeto en streaming
    obj = s3.get_object(Bucket=bucket, Key=key)
    for chunk in obj["Body"].iter_chunks(chunk_size):
        hasher.update(chunk)
    
    # Devuelve el hash
    return hasher.hexdigest()

def s3_client():
    return boto3.client("s3", region_name=AWS_REGION)

#Conexion a MongoDB
def mongo_collection():

    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    return db[INGESTION_COLLECTION]
# Conexion a RabbitMQ
def rabbit_channel():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=RABBIT_QUEUE_PARSE, durable=True)
    ch.confirm_delivery()
    return conn, ch

def list_s3(s3, bucket: str, prefix: str):
    """
    Recorre todo el bucket s3 usando el prefijo definido.
    """
    paginator = s3.get_paginator("list_objects_v2") #list_objects_v2 devuelve 1000 archivos por pagina 
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):   #Hace paginacion automatica en caso de aumento de archivos
        for obj in page.get("Contents", []):
            
            yield obj


#Contruccion del documento que se guardará en colección ingestion 
def build_doc(bucket: str, key: str, size: int, md5: str):
    file_name = key.split("/")[-1]
    return {
        "_id": key,                          
        "s3Bucket": bucket,
        "s3Key": key,                        # ruta exacta dentro del bucket CARPETA_HCDCP/producto.html
        "fileName": file_name,
        "sizeBytes": size,
        "md5": md5,
        "state": "new",                      # estado new para inicio de procesamiento 
        "publishedAt": now()
    }

def build_message(doc: dict, state: str):
    """
    Mensaje que se publica en rabbitmq y que será utilizado por el BeautifulSoup.
    """
    return {
        "s3Key": doc["s3Key"]
    }


def publish(coll, ch, obj, bucket: str) -> str:
    """
    Con cada objeto S3:
    - Inserta 'new' si no existe.
    - Si existe y cambió md5, actualiza y pone 'modified'.
    Publica a RabbitMQ SOLO si 'new' o 'modified'.
    """
    key = obj["Key"]
    size = int(obj["Size"])
    md5 = calculate_md5(bucket, key)

    # Documento base para insercion a mongo y mensaje a rabbit
    doc = build_doc(bucket, key, size, md5)

    # Busca documento existente
    current = coll.find_one({"_id": key}, {"md5": 1, "state": 1})

    #Si current es None, no existe el documento y debe insertarse
    if not current:
        
        coll.update_one({"_id": key}, {"$set": doc}, upsert=True) # Actualiza/inserta en collección
        state = "new"
        msg = build_message(doc, state)

        #Envio de nuevo mensaje a rabbitmq
        ch.basic_publish(
            exchange="",
            routing_key=RABBIT_QUEUE_PARSE,
            body=json.dumps(msg).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2)  
        )
        log.info(f"Nuevo {key} publicado en {RABBIT_QUEUE_PARSE}")
        return state

    # existe un doc entonces compara hash
    if current.get("md5") != md5:
        
        coll.update_one(
            {"_id": key},
            {"$set": {
                "sizeBytes": size,
                "md5": md5,
                "state": "modified",
                "publishedAt": now()
            }}
        )
        state = "modified"
        msg = build_message(doc, state)
        ch.basic_publish(
            exchange="",
            routing_key=RABBIT_QUEUE_PARSE,
            body=json.dumps(msg).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        log.info(f"Modificado {key} y publicado en {RABBIT_QUEUE_PARSE}")
        return state

    # Existe el doc y su hash es el mismo, se ignora
    log.debug(f"Sin modificaciones {key}")
    return "unchanged"

def run():
    log.info("Controller iniciado")

    # inicializar instancias 
    s3 = s3_client()
    coll = mongo_collection()
    conn, ch = rabbit_channel()

    totals = {"new": 0, "modified": 0, "unchanged": 0} #trazabilidad

    try:
        for prefix in S3_PREFIXES:
            log.info(f"Revisando s3://{S3_BUCKET}/{prefix}")
            for obj in list_s3(s3, S3_BUCKET, prefix):

                log.info("Revisando objeto: %s", obj["Key"])

                state = publish(coll, ch, obj, S3_BUCKET)
                totals[state] = totals.get(state, 0) + 1
    finally:
        try:
            conn.close()
        except Exception:
            pass

    log.info(f"Nuevos: {totals['new']} modificados: {totals['modified']} sin cambios: {totals['unchanged']}")
