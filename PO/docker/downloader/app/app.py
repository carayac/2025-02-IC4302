import time
import os
import sys
import pika
from datetime import datetime
import json
import hashlib
import json


hostname = os.getenv('HOSTNAME')



def callback(ch, method, properties, body):
    try:
        print(" [x] Received JSON:")
    except:
        print(" [x] Received:")


DATA=os.getenv('DATAFROMK8S')
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITMQ_PASS')
QUEUE_NAME=os.getenv('RABBITMQ_QUEUE')



#Comienza a consumir mensajes sincronos el se queda en espera de mensajes para enviarlos a la cola 
credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials) 
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
