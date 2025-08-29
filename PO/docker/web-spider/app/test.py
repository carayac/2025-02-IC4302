from unittest.mock import MagicMock
from functions import *
import uuid
from datetime import datetime
import mariadb
import pika
import time
import os
import pytest
import unittest

# Test 1: obtener_count devuelve un entero válido
def test_obtener_count():
    count = obtener_count(url_base, db, term, retstart, retmax)
    assert isinstance(count, int) #Debe ser un número entero
    assert count >= 0 #Debe ser mayor o igual a 0 (en caso de que no haya ningún artículo)



# Test 2: obtener_ids devuelve lista de IDs válida
def test_obtener_ids():
    ids = obtener_ids(url_base, db, term, retstart, retmax)
    assert isinstance(ids, list) #Debe ser una lista
    assert len(ids) > 0          #Debe contener artículos, no puede estar vacía
    assert all(i.isdigit() for i in ids) #Debe contener solo strings de números



# Test 3: Inicializar job de manera válida
def test_inicializar_job():
    lista_ids = ["12345678", "12345678", "12345678", "12345678", "12345678", "12345678", "12345677"]
    job = crear_job (lista_ids)

    assert job["estado"] == "pending"         #Siempre debe tener pending como estado inicial
    assert isinstance(job["lista_ids"], list) #Debe ser una lista
    assert len(job["lista_ids"]) > 0          #La lista no debe estar vacía
    assert job["omitido"] == []               #Omitido siempre inicia como vacío
    assert job["fecha_inicio"] is not None    #Fecha de inicio debe tener una fecha
    assert job["fecha_final"] is None         #Fecha final no debe tener una fecha todavía



# Test 4: Insertar job en MariaDB
def test_insertar_job():
    conn = MagicMock() #Simulamos conexión
    cursor = MagicMock() #Simulamos cursor
    conn.cursor.return_value = MagicMock() #Fingimos que se creo el cursor correctamente
    cursor.execute.side_effect = None #Fingimos que se ejecutó y no hubo error
    table_name = "test"
    job = {
    "id": str(uuid.uuid4()),             
    "estado": "pending",                 
    "lista_ids": ["12345678", "23456789", "34567890", "45678901", "56789012"],              
    "omitido": [],                     
    "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  
    "fecha_final": None                  
    }

    insertar_job(cursor, conn, table_name, job)

    cursor.execute.assert_called_once() #Verificar que se ejecuto el cursor
    conn.commit.assert_called_once() #Verificar que se hizo commit


# Test 5: Enviar Job id por RabbitMQ
def test_enviar_rabbitmq():
    channel = MagicMock()
    queue_name = "test"
    job_id = str(uuid.uuid4())
    enviar_rabbitmq(job_id, channel, queue_name)
    
    channel.basic_publish.assert_called_once()



#-------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])