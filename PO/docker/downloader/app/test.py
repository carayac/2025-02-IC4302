from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest
import mariadb
import requests
from functions import *


# Test 1: conexión a MariaDB
def test_connection_mariadb(monkeypatch):
    fake_conn = MagicMock()
    monkeypatch.setattr("mariadb.connect", lambda **kwargs: fake_conn)

    conn = connection_MariaDB()
    assert conn == fake_conn



# Test 2: update_job_status actualiza correctamente
def test_update_job_status(monkeypatch):
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    fake_cursor.rowcount = 1

    monkeypatch.setattr("functions.connection_MariaDB", lambda: fake_conn)

    result = update_job_status("123", "in-progress")
    assert result is True
    fake_cursor.execute.assert_called_once()
    fake_conn.commit.assert_called_once()


# Test 3: update_job_end_date actualiza fecha
def test_update_job_end_date(monkeypatch):
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_cursor.rowcount = 1
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr("functions.connection_MariaDB", lambda: fake_conn)

    result = update_job_end_date("123")
    assert result is True
    fake_cursor.execute.assert_called_once()
    fake_conn.commit.assert_called_once()


# Test 4: get_job_ids retorna lista válida
def test_get_job_ids(monkeypatch):
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    fake_cursor.fetchone.return_value = ("['1','2','3']",)

    monkeypatch.setattr("functions.connection_MariaDB", lambda: fake_conn)

    result = get_job_ids("123")
    assert isinstance(result, list)
    assert result == ["1", "2", "3"]


# Test 5: pubmed_API con respuesta válida
def test_pubmed_api(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "<xml>ok</xml>"

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse())

    result = pubmed_API(["123", "456"])
    assert result == "<xml>ok</xml>"


# Test 6: dois_pubmed extrae DOIs
def test_dois_pubmed():
    xml = """
    <Item Name="DOI" Type="String">10.1000/xyz123</Item>
    <Item Name="DOI" Type="String">10.1000/abc456</Item>
    """
    dois = dois_pubmed(xml)
    assert isinstance(dois, list)
    assert "10.1000/xyz123" in dois
    assert "10.1000/abc456" in dois

#Test 7: process_dois procesa la lista de dois 
def test_process_dois(monkeypatch):
    # Falsos datos de Crossref
    fake_data = {"title": "testing"}

    monkeypatch.setattr("functions.crossref_API", lambda doi: fake_data)

    saved = {}
    def fake_save_json(doi, data):
        saved[doi] = data
    monkeypatch.setattr("functions.save_json", fake_save_json)

    #fake para omitidos
    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    monkeypatch.setattr("functions.connection_MariaDB", lambda: fake_conn)

    monkeypatch.setattr("functions.update_job_status", lambda job_id, status: True)
    monkeypatch.setattr("functions.update_job_end_date", lambda job_id: True)

    dois = ["10.1000/cjg217", "10.1000/bfc123"]
    process_dois("123", dois)

    assert "10.1000/cjg217" in saved
    assert "10.1000/bfc123" in saved
    assert saved["10.1000/cjg217"] == fake_data

#Test #8: save_json guarda json en el path
def test_save_json(tmp_path, monkeypatch):
    monkeypatch.setenv("XPATH", str(tmp_path))

    #fake data para probar
    doi = "10.1000/test"
    data = {"just": "testing"}

    save_json(doi, data)

    import hashlib, json, os
    filename = hashlib.md5(doi.encode()).hexdigest() + ".json"
    filepath = os.path.join(tmp_path, filename)

    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        content = json.load(f)
    assert content == data

#Test 9: crossref_api hace la consulta a crossref
def test_crossref_api(monkeypatch):
    class FakeResponse:
        status_code = 200
        def json(self):
            return {"title": "Crossref"}

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse())

    doi = "10.1000/testing"
    result = crossref_API(doi)

    assert isinstance(result, dict)
    assert result["title"] == "Crossref"


#-------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
