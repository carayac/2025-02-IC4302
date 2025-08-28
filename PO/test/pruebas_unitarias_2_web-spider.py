import uuid
from datetime import datetime
import mariadb
import pika
import time
import os
import pytest

# -------------------------------
# Funciones originales (parámetros intactos)
def conectar_MariaDB():
    conn = mariadb.connect(
        host=os.getenv('MARIADB'),
        user=os.getenv('MARIADB_USER'),
        password=os.getenv('MARIADB_PASS')
    )
    cursor = conn.cursor()
    # Base de datos de test
    cursor.execute("CREATE DATABASE IF NOT EXISTS Tests")
    cursor.execute("USE Tests")
    # Tabla de test
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_table (
        id VARCHAR(36) PRIMARY KEY,
        estado VARCHAR(20),
        lista_ids TEXT,
        omitido TEXT,
        fecha_inicio DATETIME,
        fecha_final DATETIME
    )
    """)
    conn.commit()
    return conn, cursor

def insertar_job(cursor, conn, table_name, job):
    insert_query = f"""
        INSERT INTO {table_name}
        (id, estado, lista_ids, omitido, fecha_inicio, fecha_final)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (
        str(job["id"]),
        job["estado"],
        str(job["lista_ids"]),
        str(job["omitido"]),
        job["fecha_inicio"],
        job["fecha_final"]
    ))
    conn.commit()

RABBITMQ_CONFIG = {
    "host": os.getenv('RABBITMQ'),
    "port": 5672,
    "user": os.getenv('RABBITMQ_USER'),
    "password": os.getenv('RABBITMQ_PASS'),
    "queue": "test_queue"
}

def enviar_rabbitmq(job_id):
    """Envía el id del job a RabbitMQ (cola de test)"""
    QUEUE_NAME = "test_queue"
    try:
        credentials = pika.PlainCredentials('user', os.getenv('RABBITMQ_PASS'))
        parameters = pika.ConnectionParameters(host=os.getenv('RABBITMQ'), credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)

        msg = str(job_id)
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=msg)
    except:
        print(f"Error enviando job-id por RabbitMQ")
    time.sleep(1)
    connection.close()

def recibir_rabbitmq(timeout=5):
    credentials = pika.PlainCredentials(RABBITMQ_CONFIG['user'], RABBITMQ_CONFIG['password'])
    parameters = pika.ConnectionParameters(host=RABBITMQ_CONFIG['host'], port=RABBITMQ_CONFIG['port'], credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    start_time = time.time()
    body = None
    while time.time() - start_time < timeout:
        method_frame, header_frame, body_bytes = channel.basic_get(queue=RABBITMQ_CONFIG['queue'], auto_ack=True)
        if body_bytes:
            body = body_bytes.decode()
            break
        time.sleep(0.1)
    connection.close()
    return body

# -------------------------------
# Test funcional MariaDB
def test_funcional_mariadb():
    conn, cursor = conectar_MariaDB()
    table_name = "test_table"
    job = {
        "id": uuid.uuid4(),
        "estado": "pending",
        "lista_ids": ["123", "456"],
        "omitido": [],
        "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_final": None
    }

    insertar_job(cursor, conn, table_name, job)

    cursor.execute(f"SELECT id, estado, lista_ids, omitido, fecha_inicio, fecha_final FROM {table_name} WHERE id=?", (str(job["id"]),))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == str(job["id"])
    assert row[1] == job["estado"]
    assert row[2] == str(job["lista_ids"])
    assert row[3] == str(job["omitido"])
    assert row[4].strftime("%Y-%m-%d %H:%M:%S") == job["fecha_inicio"]
    assert row[5] is None

    cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (str(job["id"]),))
    conn.commit()
    cursor.close()
    conn.close()

# -------------------------------
# Test funcional RabbitMQ
def test_funcional_rabbitmq():
    job_id = str(uuid.uuid4())
    enviar_rabbitmq(job_id)
    recibido = recibir_rabbitmq(timeout=5)
    assert recibido == job_id

# -------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

