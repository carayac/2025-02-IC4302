import os
import boto3
import pika
import logging
import time
import threading
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Flask, Response

app = Flask(__name__)

# --- MÉTRICAS ---
documentos_procesados = Counter(
    'total_documentos_procesados',
    'Total documentos procesados',
    ['componente']
)
tiempo_total = Histogram(
    'tiempo_total_crawler',
    'Tiempo total de ejecución del crawler',
    ['componente']
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
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


def rabbitmq_connection():
    """Crea conexión con RabbitMQ y asegura la existencia de ambas colas."""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE_CSV, durable=False)
        channel.queue_declare(queue=RABBITMQ_QUEUE_PARKET, durable=False)
        logging.info("Conexión a RabbitMQ exitosa y colas creadas")
        return connection, channel
    except Exception as e:
        logging.error(f"Error conectando a RabbitMQ: {e}")
        raise


def publish_message(channel, queue, message):
    """Publica un mensaje en la cola especificada."""
    try:
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message,
            properties=pika.BasicProperties(delivery_mode=1)
        )
        logging.info(f"Mensaje publicado en {queue}: {message}")
    except Exception as e:
        logging.error(f"Error publicando mensaje: {e}")


# Inicializar S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


def crawl_bucket():
    """Recorre el bucket S3 una sola vez por prefijo, usando paginador."""
    start_time = time.time()
    connection, channel = rabbitmq_connection()

    paginator = s3.get_paginator("list_objects_v2")

    for prefix in S3_PREFIXES:
        logging.info(f"Listando objetos para prefijo: {prefix}")

        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]

                if key.endswith(".crc") or key.endswith("_SUCCESS"):
                    continue

                if key.endswith(".json"):
                    publish_message(channel, RABBITMQ_QUEUE_CSV, key)
                    documentos_procesados.labels(componente="crawler").inc()
                elif key.endswith(".parquet"):
                    publish_message(channel, RABBITMQ_QUEUE_PARKET, key)
                    documentos_procesados.labels(componente="crawler").inc()

    connection.close()
    duracion = time.time() - start_time
    tiempo_total.labels(componente="crawler").observe(duracion)
    logging.info(f"Crawler completado en {duracion:.2f} segundos.")


@app.route("/metrics")
def metrics():
    """Endpoint para Prometheus."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == '__main__':
    threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
    ).start()

    crawl_bucket()

