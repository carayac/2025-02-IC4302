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


#-------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])