import os
import boto3
import pika
import logging
import time
from prometheus_client import Counter, Histogram, start_http_server

# Configuración logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Variables de entorno
S3_BUCKET = os.environ['S3_BUCKET']
S3_PREFIXES = os.environ['S3_PREFIXES'].split(',')
AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET_KEY = os.environ['AWS_SECRET_KEY']
AWS_REGION = os.environ['AWS_REGION']

RABBITMQ_HOST = os.environ['RABBITMQ']
RABBITMQ_QUEUE_CSV = os.environ['RABBITMQ_QUEUE_CSV']
RABBITMQ_QUEUE_PARKET = os.environ['RABBITMQ_QUEUE_PARKET']
RABBITMQ_USER = os.environ['RABBITMQ_USER']
RABBITMQ_PASS = os.environ['RABBITMQ_PASS']

# Métricas (registro global)
documentos_procesados = Counter(
    'total_documentos_procesados',
    'Cantidad total de documentos procesados por el crawler',
    ['componente']
)
tiempo_total = Histogram(
    'tiempo_total_crawler',
    'Duración total de ejecución del crawler en segundos',
    ['componente']
)

# Conexión S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE_CSV, durable=False)
    channel.queue_declare(queue=RABBITMQ_QUEUE_PARKET, durable=False)
    logging.info("Conexión a RabbitMQ exitosa y colas creadas")
    return connection, channel

def publish_message(channel, queue, message):
    channel.basic_publish(exchange='', routing_key=queue, body=message)
    logging.info(f"Mensaje publicado en {queue}: {message}")

def crawl_bucket():
    start_time = time.time()
    connection, channel = rabbitmq_connection()

    for prefix in S3_PREFIXES:
        logging.info(f"Listando objetos en prefijo: {prefix}")
        continuation_token = None

        while True:
            kwargs = {"Bucket": S3_BUCKET, "Prefix": prefix}
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            response = s3.list_objects_v2(**kwargs)

            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".crc") or key.endswith("_SUCCESS"):
                    continue
                if key.endswith(".json"):
                    publish_message(channel, RABBITMQ_QUEUE_CSV, key)
                    documentos_procesados.labels(componente="crawler").inc()
                elif key.endswith(".parquet"):
                    publish_message(channel, RABBITMQ_QUEUE_PARKET, key)
                    documentos_procesados.labels(componente="crawler").inc()

            if response.get("IsTruncated"):
                continuation_token = response.get("NextContinuationToken")
            else:
                break

    connection.close()
    duracion = time.time() - start_time
    tiempo_total.labels(componente="crawler").observe(duracion)
    logging.info(f"Crawler completado en {duracion:.2f} segundos.")

if __name__ == "__main__":
    # Servidor de métricas Prometheus en puerto 8000
    start_http_server(8000)
    logging.info("Servidor de métricas iniciado en puerto 8000")

    # Ejecutar crawling
    crawl_bucket()

    # Mantener Job vivo 5 minutos para scrapear métricas
    logging.info("Crawler completado, manteniendo Job activo 5 minutos para Prometheus...")
    time.sleep(1800)
    logging.info("Finalizando Job.")
