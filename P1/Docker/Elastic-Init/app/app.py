import os
import json
import time
import logging
from elasticsearch import Elasticsearch, exceptions

ELASTIC_HOST = os.getenv("ELASTIC_HOST")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_PASS = os.getenv("ELASTIC_PASS")
MAPPINGS_FILE = "elastic-mappings.json"

MAX_RETRIES = 20
RETRY_DELAY = 5  # segundos

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Función para conectar con reintentos
def conectar_elasticsearch():
    for intento in range(1, MAX_RETRIES + 1):
        try:
            es = Elasticsearch(
                f"http://{ELASTIC_HOST}:9200",
                basic_auth=(ELASTIC_USER, ELASTIC_PASS)
            )
            if es.ping():
                logging.info("Conexión a Elasticsearch exitosa")
                return es
        except exceptions.ConnectionError as e:
            logging.warning(f"Intento {intento}/{MAX_RETRIES} fallido: {e}")
        time.sleep(RETRY_DELAY)
    logging.error("No se pudo conectar a Elasticsearch tras varios intentos")
    return None

# Crear índices
def crear_indices(es, mappings):
    for index_name, body in mappings.items():
        try:
            if es.indices.exists(index=index_name):
                logging.info(f"Eliminando índice existente '{index_name}'")
                es.indices.delete(index=index_name)
            
            # Agregar settings mínimos si no existen
            if "settings" not in body:
                body["settings"] = {"number_of_shards": 1, "number_of_replicas": 0}
            
            es.indices.create(index=index_name, body=body, ignore=400)
            logging.info(f"Índice '{index_name}' creado correctamente")

            # Verificar mappings
            res = es.indices.get_mapping(index=index_name)
            logging.info(json.dumps(res.body, indent=2))
        except Exception as e:
            logging.error(f"Falló al crear/verificar el índice '{index_name}': {e}")

def main():
    # Cargar JSON de mappings
    with open(MAPPINGS_FILE) as f:
        mappings = json.load(f)
    
    es = conectar_elasticsearch()
    if es is None:
        return
    
    crear_indices(es, mappings)

if __name__ == "__main__":
    main()
