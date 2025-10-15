from unittest.mock import MagicMock, patch
import pytest
import os
import json
import time
import pandas as pd
import mariadb

from functions import *

# Pruebas

# Prueba 1: buscar_objeto retorna True/False 
def test_buscar_objeto():
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    assert buscar_objeto(cursor, "tabla", "key") is True

    cursor.fetchone.return_value = None
    assert buscar_objeto(cursor, "tabla", "key") is False


# Prueba 2: descargar el objeto
def test_descargar_objeto(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY", "fake_access")
    monkeypatch.setenv("AWS_SECRET_KEY", "fake_secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_BUCKET", "fake_bucket")
    monkeypatch.setenv("XPATH", "/tmp")

    with patch("functions.boto3.client") as mock_boto_client:
        mock_boto3 = MagicMock()
        mock_boto_client.return_value = mock_boto3

        key_name = "archivo_prueba.parquet"
        download_path = descargar_objeto(key_name)

        path_correcto = os.path.join("/tmp", key_name)
        assert download_path == path_correcto
        mock_boto_client.assert_called_once_with(
            's3',
            aws_access_key_id="fake_access",
            aws_secret_access_key="fake_secret",
            region_name="us-east-1"
        )
        mock_boto3.download_file.assert_called_once_with("fake_bucket", key_name, path_correcto)


# Prueba 3: Procesar objeto parquet
def test_procesar_objeto_parquet(tmp_path, monkeypatch):
    file_path = tmp_path / "objeto1.parquet"
    data = pd.DataFrame([
        {"title": "Libro A", "review/text": "Excelente", "review/score": 4.5},
        {"title": "Libro B", "review/text": "Malo", "review/score": 2.0},
    ])
    data.to_parquet(file_path)

    documentos = procesar_objeto(str(file_path))
    assert len(documentos) == 2
    assert documentos[0]["title"] == "Libro A"
    assert "review/text" in documentos[0]
    assert documentos[1]["review/score"] == 2.0


# Prueba 4: probar todos los embeddings
def test_embedding_todos_documentos(monkeypatch):
    docs = [
        {"review/summary": "Buen libro", "review/text": "Lo disfruté"},
        {"review/summary": "", "review/text": ""},
        {"no_summary": "x"},
    ]

    def fake_create(texto):
        return [0.1, 0.2, 0.3] if "Buen libro" in texto else None

    monkeypatch.setattr("functions.crear_embedding", fake_create)

    respuesta = embedding_todos_documentos(docs)
    assert respuesta[0]["embeddings"] == [0.1, 0.2, 0.3]
    assert respuesta[1]["embeddings"] is None
    assert respuesta[2]["embeddings"] is None


# Prueba 5: guardar en elasticsearch
@patch("functions.bulk") 
def test_guardar_reviews_elasticsearch(mock_bulk, monkeypatch):
    mock_es = MagicMock()
    monkeypatch.setattr("functions.conectar_elasticsearch", lambda: mock_es)
    docs = [
        {"title": "T1", "review_time": "1696982400"},
        {"title": "T2", "review_time": "1697068800"},
    ]
    monkeypatch.setenv("ELASTIC_INDEX_REVIEWS", "reviews")
    monkeypatch.setenv("ELASTIC_INDEX_NREVIEWS", "nreviews")

    guardar_reviews_elasticsearch(docs)
    assert mock_bulk.call_count >= 2


# Prueba 6: formatear review_time
def test_formatear_review_time_para_elastic():
    doc = {"review_time": "1696982400"}
    result = formatear_review_time_para_elastic(doc)
    assert "review/time" in result
    assert result["review/time"].startswith("2023-")  # formato correcto


# Prueba 7: normalizar review_time varios formatos
def test_normalizar_review_time_varios_formatos():
    # timestamp en segundos
    assert normalizar_review_time("1696982400").startswith("2023-")
    # timestamp en milisegundos
    assert normalizar_review_time("1696982400000").startswith("2023-")
    # formato texto
    assert normalizar_review_time("2020-01-02 10:00:00") == "2020-01-02 10:00:00"
    # formato incorrecto
    assert normalizar_review_time("no-fecha") is None


# Prueba 8: normalizar review_score
def test_normalizar_review_score():
    assert normalizar_review_score("4.5") == 4.5
    assert normalizar_review_score(3) == 3.0
    assert normalizar_review_score(None) is None
    assert normalizar_review_score("abc") is None


# Prueba 9: normalizar price
def test_normalizar_price():
    assert normalizar_price("10.99") == 10.99
    assert normalizar_price(8) == 8.0
    assert normalizar_price(None) is None
    assert normalizar_price("nulo") is None


# Prueba 10: insertar_review
def test_insertar_review(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    monkeypatch.setenv("MARIADB_TABLE_BOOKS", "books")
    monkeypatch.setenv("MARIADB_TABLE_REVIEWS", "reviews")
    monkeypatch.setenv("MARIADB_TABLE_PENDING", "pending")

    cursor.fetchone.return_value = (1,)
    insertar_review(conn, cursor, "obj1", title="Libro X")
    conn.commit.assert_called()

    cursor.fetchone.return_value = None
    insertar_review(conn, cursor, "obj2", title="Libro Y")
    assert conn.commit.called


# Prueba 11: insertar_info
def test_insertar_info(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    key_name = "objeto1.parquet"

    monkeypatch.setattr("functions.insertar_review", lambda *args, **kwargs: None)
    monkeypatch.setattr("functions.normalizar_price", lambda x: x)
    monkeypatch.setattr("functions.normalizar_review_score", lambda x: x)
    monkeypatch.setattr("functions.normalizar_review_time", lambda x: x)

    documentos = [
        {"title": "Libro 1", "price": 10.0, "review/time": "2020-01-01"},
        {"title": "Libro 2", "price": 12.0, "review/time": "2021-02-02"},
    ]

    insertar_info(cursor, conn, key_name, documentos)
    assert conn.method_calls or cursor.method_calls


# Prueba 12: insertar_object
def test_insertar_object(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    monkeypatch.setenv("MARIADB_TABLE", "objects")

    documentos = [{"a": 1}, {"b": 2}]
    key_name = "objeto1.parquet"

    insertar_object(cursor, conn, key_name, documentos, procesado=True)
    cursor.execute.assert_called_once()
    conn.commit.assert_called_once()

#-------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])