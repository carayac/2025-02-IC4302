import os
import json
from elasticsearch import Elasticsearch

ELASTIC_HOST = os.getenv("ELASTIC_HOST")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_PASS = os.getenv("ELASTIC_PASS")
MAPPINGS_FILE = "elastic-mappings.json"

es = Elasticsearch(f"http://{ELASTIC_HOST}:9200", basic_auth=(ELASTIC_USER, ELASTIC_PASS))

# Cargar JSON de mappings
with open(MAPPINGS_FILE) as f:
    mappings = json.load(f)

for index_name, body in mappings.items():
    if es.indices.exists(index=index_name):
        print(f"Eliminando índice existente '{index_name}'")
        es.indices.delete(index=index_name)
    es.indices.create(index=index_name, body=body)
    print(f"Índice '{index_name}' creado correctamente")