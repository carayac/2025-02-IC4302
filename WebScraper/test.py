from main import *
from unittest.mock import MagicMock, patch
import pytest


def test_obtenerProductos(monkeypatch):
    #hacer mock de todo
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_requests = MagicMock()
    mock_requests.get.return_value = mock_response
    monkeypatch.setattr("main.requests", mock_requests)


    #realizar prueba
    result = obtenerProductos("https://example.com")
    assert result == "OK"


#asegurarse que solo se cantengan los links válidos
def test_obtenerLinks():
    html = '''
    <a href="https://edutin.com/curso-de-python"></a>
    <a href="https://edutin.com/curso-de-cocina"></a>
    <a href="https://edutin.com/imagen.jpg"></a>
    <a href="https://facebook.com/curso"></a>
    '''

    links = obtenerLinks(html)

    assert len(links) == 2
    assert "https://edutin.com/curso-de-python" in links
    assert "https://edutin.com/curso-de-cocina" in links


#si no hay links es vacio
def test_obtenerLinks_vacio():
    assert obtenerLinks(None) == []
    assert obtenerLinks("") == []


#prueba de descargar html
def test_descargarHtml(tmp_path, monkeypatch):
    monkeypatch.setattr("main.folder", str(tmp_path))

    #probar con curso 001
    descargarHtml("<html>hola</html>", 1)

    file_path = tmp_path / "curso_001.html"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "<html>hola</html>"

#------------------------------------------- 
if __name__ == "__main__": 
    pytest.main([__file__, "-v"])