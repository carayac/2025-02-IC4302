from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
from os import getenv
import sys
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# --- Métricas Prometheus ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "elasticsearch"
CACHE_TYPE = "none"

@app.before_request
def iniciar_tiempo():
    request.start_time = time.time()
    request.bd_type = BD_TYPE
    request.cache_type = CACHE_TYPE

@app.after_request
def medir_peticiones(response):
    tiempo = time.time() - request.start_time
    promedio_tiempo.labels(bd=request.bd_type, cache=request.cache_type).observe(tiempo)
    peticiones_http.labels(bd=request.bd_type, cache=request.cache_type).inc()
    return response

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# --- Config Elasticsearch ---
ES_HOST = getenv("ELASTIC", "localhost")
ES_PORT = getenv("ES_PORT", "9200")
ES_USER = getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = getenv("ELASTIC_PASS", "changeme")
INDEX_NAME = "animals"

def get_connection():
    try:
        conn = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"], basic_auth=(ES_USER, ES_PASSWORD))
        if not conn.ping():
            raise Exception("No se pudo conectar a Elasticsearch")
        return conn
    except Exception as e:
        print(f"Error creando conexión Elasticsearch: {e}")
        sys.exit(1)

# Endpoints
@app.route("/animales")
def get_animales():
    conn = get_connection()
    res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
    animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]
    return jsonify(animals)

@app.route("/colores")
def get_colores():
    conn = get_connection()
    query = {"size":0,"aggs":{"por_color":{"terms":{"field":"color","size":100},"aggs":{"nombres_animales":{"top_hits":{"_source":["name"],"size":100}}}}}}
    res = conn.search(index=INDEX_NAME, body=query)
    result = [{"color": b["key"], "animals":[hit["_source"]["name"] for hit in b["nombres_animales"]["hits"]["hits"]]} for b in res["aggregations"]["por_color"]["buckets"]]
    return jsonify(result)

@app.route("/health")
def health_check():
    return jsonify({"status":"healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

