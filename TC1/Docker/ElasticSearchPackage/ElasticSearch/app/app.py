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
        )
        if not conn.ping():
            raise Exception("No se pudo conectar a Elasticsearch")
        return conn
    except Exception as e:
        print(f"Error creando conexión Elasticsearch: {e}")
        sys.exit(1)


# List all the animals
@app.route("/animales", methods=["GET"])
def get_animales():
    conn = get_connection()
    res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
    animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]
    return jsonify(animals)


# List all diets
@app.route("/dietas", methods=["GET"])
def get_dietas():
    conn = get_connection()
    res = conn.search(
        index=INDEX_NAME,
        size=0,
        aggs={"dietas": {"terms": {"field": "diet"}}}
    )
    diets = [{"tipo_dieta": b["key"], "count": b["doc_count"]} for b in res["aggregations"]["dietas"]["buckets"]]
    return jsonify(diets)


# List all habitats
@app.route("/habitats", methods=["GET"])
def get_habitats():
    conn = get_connection()
    res = conn.search(
        index=INDEX_NAME,
        size=0,
        aggs={"habitats": {"terms": {"field": "habitat"}}}
    )
    habitats = [{"nombre_habitat": b["key"], "count": b["doc_count"]} for b in res["aggregations"]["habitats"]["buckets"]]
    return jsonify(habitats)


# List familias
@app.route("/familias", methods=["GET"])
def get_familias():
    conn = get_connection()
    res = conn.search(
        index=INDEX_NAME,
        size=0,
        aggs={"familias": {"terms": {"field": "family"}}}
    )
    familias = [{"nombre_familia": b["key"], "count": b["doc_count"]} for b in res["aggregations"]["familias"]["buckets"]]
    return jsonify(familias)


# ANIMAL WITH HIGHEST SPEED
@app.route("/top-velocidad", methods=["GET"])
def top_velocidad():
    conn = get_connection()
    res = conn.search(
        index=INDEX_NAME,
        size=5,
        sort=[{"top_speed_kmh": {"order": "desc"}}],
        query={"exists": {"field": "top_speed_kmh"}}
    )
    top = [{"nombre": hit["_source"]["name"], "velocidad_max_kmh": hit["_source"]["top_speed_kmh"]}
           for hit in res["hits"]["hits"]]
    return jsonify(top)


# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
