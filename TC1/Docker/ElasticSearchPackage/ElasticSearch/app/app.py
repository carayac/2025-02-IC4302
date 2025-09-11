from flask import Flask, jsonify
from elasticsearch import Elasticsearch
from os import getenv
import sys

app = Flask(__name__)

# Elasticsearch configuration from environment variables
ES_HOST = getenv("ELASTIC", "localhost")
ES_PORT = getenv("ES_PORT", "9200")
ES_USER = getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = getenv("ELASTIC_PASS", "changeme")

# Index name for animals in Elasticsearch
INDEX_NAME = "animals"


# Database connection
def get_connection():
    try:
        conn = Elasticsearch(
            [f"http://{ES_HOST}:{ES_PORT}"],
            basic_auth=(ES_USER, ES_PASSWORD)
        ) # Crear conexión a Elasticsearch
        if not conn.ping(): #chequear si la conexión es exitosa
            raise Exception("No se pudo conectar a Elasticsearch")
        return conn # Devolver la conexión
    except Exception as e:
        print(f"Error creando conexión Elasticsearch: {e}")
        sys.exit(1)


# List all the animals
@app.route("/animales", methods=["GET"])
def get_animales():
    conn = get_connection() # Obtener conexión a Elasticsearch
    try:
        res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
        animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]
        return jsonify(animals)# Devolver la lista de animales
    except Exception as e:
        if e.info and 'index_not_found_exception' in e.info['error']['type']:
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/colores", methods=["GET"])
def get_colores():
    conn = get_connection() # Obtener conexión a Elasticsearch
    query = { # Consulta de agregación para obtener colores y sus animales
        "size": 0,  # No necesitamos documentos, solo agregaciones
        "aggs": {
            "por_color": {
                "terms": {
                    "field": "color.keyword",
                    "size": 1000  # máximo número de colores
                },
                "aggs": {
                    "animales_unicos": {
                        "terms": {
                            "field": "name.keyword",
                            "size": 1000  # máximo número de animales por color
                        }
                    }
                }
            }
        }
    }
    # Realizar la búsqueda con agregaciones
    try:
        res = conn.search(index="animals", body=query)
        # Procesar los resultados
        result = []
        for bucket in res["aggregations"]["por_color"]["buckets"]:
            color = bucket["key"]
            animales = [a["key"] for a in bucket["animales_unicos"]["buckets"]]
            result.append({
                "color": color,
                "animals": animales
            })
        return jsonify(result) # Devolver la lista de colores con sus animales
    except Exception as e:
        if e.info and 'index_not_found_exception' in e.info['error']['type']:
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
