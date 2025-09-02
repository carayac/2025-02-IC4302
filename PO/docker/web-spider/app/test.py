from unittest.mock import MagicMock
from functions import *
import uuid
from datetime import datetime
import pytest

retstart = 0

# Test 1: obtener_count devuelve un entero válido
def test_obtener_count():
    count = obtener_count(url_base, db, term, retstart, retmax)
    assert isinstance(count, int), f"obtener_count devolvió {type(count)} en lugar de int"
    assert count >= 0, f"obtener_count devolvió {count}, pero debe ser >= 0"


# Test 2: obtener_ids devuelve lista de IDs válida
def test_obtener_ids():
    ids = obtener_ids(url_base, db, term, retstart, retmax)
    assert isinstance(ids, list), f"Se esperaba lista, pero se obtuvo {type(ids)}"
    assert len(ids) > 0, "La lista de IDs está vacía"
    assert all(i.isdigit() for i in ids), f"La lista contiene valores no numéricos: {ids}"


# Test 3: Inicializar job de manera válida
def test_inicializar_job():
    lista_ids = ["12345678", "12345678", "12345678", "12345678", "12345678", "12345678", "12345677"]
    job = crear_job(lista_ids)

    assert job["estado"] == "pending", f"Estado inicial incorrecto: {job['estado']}"
    assert isinstance(job["lista_ids"], list), f"lista_ids debe ser lista, es {type(job['lista_ids'])}"
    assert len(job["lista_ids"]) > 0, "lista_ids no debe estar vacía"
    assert job["omitido"] == [], f"Omitido debe iniciar vacío, se obtuvo {job['omitido']}"
    assert job["fecha_inicio"] is not None, "fecha_inicio no debe ser None"
    assert job["fecha_final"] is None, f"fecha_final debe iniciar como None, se obtuvo {job['fecha_final']}"


# Test 4: Insertar job en MariaDB
def test_insertar_job():
    conn = MagicMock()  # Simulamos conexión
    cursor = MagicMock()  # Simulamos cursor
    conn.cursor.return_value = MagicMock()  # Fingimos que se creó el cursor correctamente
    cursor.execute.side_effect = None  # Fingimos que se ejecutó y no hubo error
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

    cursor.execute.assert_called_once(), "El cursor no ejecutó ninguna query"
    conn.commit.assert_called_once(), "No se llamó a commit después del insert"


# Test 5: Enviar Job id por RabbitMQ
def test_enviar_rabbitmq():
    channel = MagicMock()
    queue_name = "test"
    job_id = str(uuid.uuid4())
    enviar_rabbitmq(job_id, channel, queue_name)

    channel.basic_publish.assert_called_once(), "No se publicó el mensaje en RabbitMQ"


#-------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
