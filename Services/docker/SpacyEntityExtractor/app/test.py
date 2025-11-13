import json
import os
from unittest.mock import MagicMock
import pytest
import functions as ner  


@pytest.fixture
def coll():
    # Simula la coleccion de MongoDB
    return MagicMock()


def test_path_from_key():
    # Verifica que genere la ruta correcta del archivo JSON
    base_dir = "/base/augmented"
    s3_key = "carpeta/sub/archivo.html"
    result = ner.path_from_key(base_dir, s3_key)

    assert result == os.path.join(base_dir, "archivo.json")


def test_entities_started(coll):
    # Prueba que actualice el estado a "started"
    doc_id = "file1"
    ner.entities_status(coll, doc_id, "started")

    coll.update_one.assert_called_once()
    (filtro, update), _ = coll.update_one.call_args

    assert filtro == {"_id": doc_id}
    assert update == {"$set": {"entitiesExtraction": "started"}}


def test_entities_error(coll):
    # Prueba que guarde el error cuando falla
    doc_id = "file2"
    ner.entities_status(coll, doc_id, "error", "error X")

    coll.update_one.assert_called_once()
    _, update = coll.update_one.call_args[0]

    assert update == {
        "$set": {
            "entitiesExtraction": "error",
            "entitiesExtractionError": "error X",
        }
    }


def test_normalize_text():
    # Verifica que limpie espacios y saltos de linea
    result = ner.normalize_text("  Hola \n mundo\r\r   NLP  ")
    assert result == "Hola mundo NLP"
    assert ner.normalize_text("") == ""
    assert ner.normalize_text(None) == ""


def test_extract_entities(monkeypatch):
    # Prueba extraccion de entidades y eliminacion de duplicados
    class Ent:
        def __init__(self, label_, text):
            self.label_ = label_
            self.text = text

    class Doc:
        def __init__(self, text):
            self.ents = [
                Ent("ORG", "Facebook"),
                Ent("ORG", "facebook "),  # duplicado
                Ent("PRODUCT", "Coursera")
            ]

    monkeypatch.setattr(ner, "NLP", lambda text: Doc(text))

    ents = ner.extract_entities("texto")
    
    # Solo debe devolver 2, Facebook duplicado se elimina
    assert len(ents) == 2
    assert {"type": "ORG", "value": "Facebook"} in ents
    assert {"type": "PRODUCT", "value": "Coursera"} in ents


def test_ensure_volume(tmp_path):
    # Verifica que cree las carpetas raw y augmented
    base = tmp_path / "volumen"
    ner.ensure_volume(str(base))

    assert (base / "raw").exists()
    assert (base / "augmented").exists()


def test_ensure_volume_empty():
    # Debe fallar si BASE_PATH esta vacio
    with pytest.raises(ValueError):
        ner.ensure_volume("")


def test_message_flujo(tmp_path, monkeypatch, coll):
    # Prueba el flujo completo de procesamiento
    base = tmp_path / "pvc"
    raw_dir = base / "raw"
    aug_dir = base / "augmented"
    raw_dir.mkdir(parents=True)
    aug_dir.mkdir(parents=True)

    monkeypatch.setattr(ner, "BASE_PATH", str(base))

    # crear JSON de entrada en raw
    raw_doc = {
        "title": "Curso Python",
        "description": "Aprende Python",
        "reviews": [{"user": "Ana", "comment": "Buen curso", "rating": 5}]
    }
    raw_path = raw_dir / "curso.json"
    raw_path.write_text(json.dumps(raw_doc), encoding="utf-8")

    msg = {
        "_id": "folder/curso.html",
        "jsonPath": str(raw_path)
    }

    # Simular extraccion de entidades
    monkeypatch.setattr(ner, "extract_entities",
        lambda text: [{"type": "ORG", "value": "Python Institute"}])

    ner.message(coll, msg)

    # Verificar que actualiza MongoDB 2 veces con started y completed
    assert coll.update_one.call_count == 2

    # Verificar que creo el archivo augmented
    out_file = aug_dir / "curso.json"
    assert out_file.exists()

    augmented = json.loads(out_file.read_text(encoding="utf-8"))
    assert augmented["entities"] == [{"type": "ORG", "value": "Python Institute"}]
