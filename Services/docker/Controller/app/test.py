
import json
import hashlib
from unittest.mock import MagicMock
import pytest
import functions as controller



# Prueba que build_doc cree el documento correctamente
def test_build_doc(monkeypatch):

    # fijar la fecha 
    now = "2025-01-01T00:00:00+00:00"
    monkeypatch.setattr(controller, "now", lambda: now)

    key = "carpetaBD/subcarpetaBD/archivo.txt"
    size = 1234
    md5 = "ultimoproyecto1234567890abcdef"

    doc = controller.build_doc(key, size, md5)

    # Verificar que los campos sean correctos
    assert doc["_id"] == key
    assert doc["fileName"] == "archivo.txt"
    assert doc["sizeBytes"] == size
    assert doc["md5"] == md5
    assert doc["state"] == "new"
    assert doc["publishedAt"] == now


def test_build_message():
    # Revisar que build_message extraiga solo el _id
    doc = {"_id": "carpetaBD/archivo.txt", "otro": 123}
    msg = controller.build_message(doc, state="new")

    # contruyendo msg con el _id
    assert msg == {"id": "carpetaBD/archivo.txt"}

def test_list_s3():
    # Simular el listado de objetos de S3
    class Paginator:
        def paginate(self, Bucket, Prefix):
            assert Bucket == "mi-bucket"
            assert Prefix == "prefix/"
            # Devuelve 2 paginas con objetos y 1 vacia
            return [
                {"Contents": [{"Key": "k1", "Size": 1}, {"Key": "k2", "Size": 2}]},
                {"Contents": [{"Key": "k3", "Size": 3}]},
                {"SinContents": []}, 
            ]

    class S3:
        def get_paginator(self, name):
            assert name == "list_objects_v2"
            return Paginator()

    s3 = S3()

    objs = list(controller.list_s3(s3, "mi-bucket", "prefix/"))

    # devolver 3 objetos en total
    assert len(objs) == 3
    assert [o["Key"] for o in objs] == ["k1", "k2", "k3"]


def test_calculate_md5(monkeypatch):
    # Probar que calculate_md5 calcule el hash correctamente
    chunks = [b"hola ", b"mundo"]
    expected_md5 = hashlib.md5(b"hola mundo").hexdigest()

    # Simular el Body que devuelve S3
    class Body:
        def iter_chunks(self, chunk_size):
            for c in chunks:
                yield c

    class S3Client:
        def get_object(self, Bucket, Key):
            assert Bucket == "mi-bucket"
            assert Key == "mi-key"
            return {"Body": Body()}

    class Boto3Module:
        @staticmethod
        def client(service_name, region_name=None):
            assert service_name == "s3"
            return S3Client()

    monkeypatch.setattr(controller, "boto3", Boto3Module)

    result = controller.calculate_md5("mi-bucket", "mi-key")
    assert result == expected_md5


# Test para la funcion publish: new, modified y unchanged
def test_publish_new(monkeypatch):
    # Caso 1: archivo nuevo que no esta en MongoDB
    now = "2025-01-01T00:00:00+00:00"
    monkeypatch.setattr(controller, "now", lambda: now)
    monkeypatch.setattr(controller, "calculate_md5", lambda bucket, key, chunk_size=8192: "md5-new")
    monkeypatch.setattr(controller, "RABBIT_QUEUE_PARSE", "parse-queue")

    
    coll = MagicMock()
    coll.find_one.return_value = None   # no existe el doc todavía

    ch = MagicMock()

    obj = {"Key": "folder/file1.txt", "Size": 123}

    state = controller.publish(coll, ch, obj, bucket="my-bucket")

    # Retorna estado "new"
    assert state == "new"

    # se hizo upsert con los datos correctos
    coll.update_one.assert_called_once()
    (filtro, update), kwargs = coll.update_one.call_args

    assert filtro == {"_id": "folder/file1.txt"}
    assert kwargs["upsert"] is True

    doc_set = update["$set"]
    assert doc_set["fileName"] == "file1.txt"
    assert doc_set["sizeBytes"] == 123
    assert doc_set["md5"] == "md5-new"
    assert doc_set["state"] == "new"
    assert doc_set["publishedAt"] == now

    # Verificar que se publico en RabbitMQ
    ch.basic_publish.assert_called_once()
    _, publish_kwargs = ch.basic_publish.call_args

    assert publish_kwargs["exchange"] == ""
    assert publish_kwargs["routing_key"] == "parse-queue"

    body = json.loads(publish_kwargs["body"].decode("utf-8"))
    assert body == {"id": "folder/file1.txt"}

    assert publish_kwargs["properties"].delivery_mode == 2


def test_publish_modified(monkeypatch):
    # Caso 2: archivo que cambio (md5 diferente)
    now = "2025-01-02T00:00:00+00:00"
    monkeypatch.setattr(controller, "now", lambda: now)
    monkeypatch.setattr(controller, "calculate_md5", lambda bucket, key, chunk_size=8192: "md5-new")
    monkeypatch.setattr(controller, "RABBIT_QUEUE_PARSE", "parse-queue")

    coll = MagicMock()

    # doc existente con otro md5
    coll.find_one.return_value = {"md5": "md5-old", "state": "new"}
    ch = MagicMock()
    obj = {"Key": "folder/file2.txt", "Size": 999}

    state = controller.publish(coll, ch, obj, bucket="my-bucket")

    # Retorna "modified"
    assert state == "modified"

    coll.update_one.assert_called_once()
    (filtro, update), kwargs = coll.update_one.call_args

    assert filtro == {"_id": "folder/file2.txt"}
    assert "upsert" not in kwargs

    doc_set = update["$set"]
    assert doc_set["sizeBytes"] == 999
    assert doc_set["md5"] == "md5-new"
    assert doc_set["state"] == "modified"
    assert doc_set["publishedAt"] == now

    ch.basic_publish.assert_called_once()


def test_publish_unchanged(monkeypatch):
    # Caso 3: archivo sin cambios (mismo md5)
    monkeypatch.setattr(controller, "calculate_md5", lambda bucket, key, chunk_size=8192: "md5-same")

    coll = MagicMock()
    coll.find_one.return_value = {"md5": "md5-same", "state": "new"}
    ch = MagicMock()

    obj = {"Key": "folder/file3.txt", "Size": 500}
    state = controller.publish(coll, ch, obj, bucket="my-bucket")

    # Retorna "unchanged" y no hace nada
    assert state == "unchanged"
    coll.update_one.assert_not_called()
    ch.basic_publish.assert_not_called()
