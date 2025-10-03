import os
import boto3
import pika
import logging

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
RABBITMQ_QUEUE = os.environ['RABBITMQ_QUEUE']
RABBITMQ_USER = os.environ['RABBITMQ_USER']
RABBITMQ_PASS = os.environ['RABBITMQ_PASS']

def rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    logging.info("Conexión a RabbitMQ exitosa")
    return connection, channel

def publish_message(channel, queue, message):
    try:
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # persistente
        )
        logging.info(f"Mensaje publicado: {message}")
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

                # Ignorar archivos innecesarios
                if key.endswith(".crc") or key.endswith("_SUCCESS"):
                    continue

                # Solo procesar JSON o Parquet
                if not (key.endswith(".json") or key.endswith(".parquet")):
                    continue

                #de momento se publica solo la key, preguntar
                publish_message(channel, RABBITMQ_QUEUE, key)

            if response.get("IsTruncated"):  # hay más objetos
                continuation_token = response.get("NextContinuationToken")
            else:
                break

    connection.close()
    logging.info("Crawler finalizado")

if __name__ == '__main__':
    crawl_bucket()




