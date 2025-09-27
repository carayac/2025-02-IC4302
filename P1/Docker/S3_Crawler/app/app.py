import os
import boto3
import pika
import json
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

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
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        logging.info("Conexión a RabbitMQ exitosa")
        return connection, channel
    except Exception as e:
        logging.error(f"Error conectando a RabbitMQ: {e}")
        return None, None

def publish_message(channel, queue, message):
    try:
        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(message),
        )
        logging.info(f"Mensaje publicado en RabbitMQ ({queue}): {message}")
    except Exception as e:
        logging.error(f"Error publicando mensaje en RabbitMQ: {e}")

# Inicializar S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


if __name__ == '__main__':
    connection, channel = rabbitmq_connection()




