import uuid
from datetime import datetime
import pytest
import xml.etree.ElementTree as ET
import requests

# -------------------------------
#Probamos las siguientes funciones unitarias
url_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
db = "pubmed"
term = "science[journal]"
retstart = 0
retmax = 20

def obtener_count(url_base, db, term, retstart, retmax):
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
    response = requests.get(new_url)
    data = response.text
    datosFormatted = ET.fromstring(data)
    return int(datosFormatted.find(".//Count").text)

def obtener_ids(url_base, db, term, retstart, retmax):
    new_url = f"{url_base}?db={db}&term={term}&retstart={retstart}&retmax={retmax}"
    response = requests.get(new_url)
    data = response.text
    datosFormatted = ET.fromstring(data)
    return [elem.text for elem in datosFormatted.findall(".//Id")]






# -------------------------------
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

# Test 3: inicializar job de manera válida
def test_inicializar_job():
    ids = obtener_ids(url_base, db, term, retstart, retmax)
    job = {
        "id": uuid.uuid4(),
        "estado": "pending",
        "lista_ids": ids,
        "omitido": [],
        "fecha_inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_final": None
    }
    assert isinstance(job["id"], uuid.UUID)   #Un id único y aleatorio
    assert job["estado"] == "pending"         #Siempre debe tener pending como estado inicial
    assert isinstance(job["lista_ids"], list) #Debe ser una lista
    assert len(job["lista_ids"]) > 0          #La lista no debe estar vacía
    assert job["omitido"] == []               #Omitido siempre inicia como vacío
    assert job["fecha_inicio"] is not None    #Fecha de inicio debe tener una fecha
    assert job["fecha_final"] is None         #Fecha final d¿no debe tener una fecha todavía

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
