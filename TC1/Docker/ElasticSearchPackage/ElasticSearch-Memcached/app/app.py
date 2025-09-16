from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
from pymemcache.client.base import Client
from os import getenv
import json
import sys
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ------------------ Config Flask ------------------
app = Flask(__name__)

# ------------------ Métricas Prometheus ------------------
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "elasticsearch"
CACHE_TYPE = "memcached"

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

# ------------------ Config Elasticsearch ------------------
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

# ------------------ Config Memcached ------------------
MEMCACHED_HOST = getenv("MEMCACHED_HOST", "databases-memcached")
MEMCACHED_PORT = int(getenv("MEMCACHED_PORT", 11211))
CACHE_TTL_SECONDS = 60
memcached = Client((MEMCACHED_HOST, MEMCACHED_PORT))

def cache_get(key):
    try:
        raw = memcached.get(key)
        if not raw:
            cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
            return None
        cache_hit.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return None

def cache_set(key, value, ttl=CACHE_TTL_SECONDS):
    try:
        memcached.set(key, json.dumps(value), expire=ttl)
    except Exception:
        pass

# ------------------ Endpoints ------------------
@app.route("/animales", methods=["GET"])
def get_animales():
    cache_key = "animales-nombre"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"source": "cache", "data": cached})

    conn = get_connection()
    try:
        res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
        animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]
        cache_set(cache_key, animals)
        return jsonify({"source": "db", "data": animals})
    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/colores", methods=["GET"])
def get_colores():
    cache_key = "animales-colores"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"source": "cache", "data": cached})

    conn = get_connection()
    query = {
        "size": 0,
        "aggs": {
            "por_color": {
                "terms": {"field": "color", "size": 100},
                "aggs": {"nombres_animales": {"top_hits": {"_source": ["name"], "size": 100}}}
            }
        }
    }
    try:
        res = conn.search(index=INDEX_NAME, body=query)
        result = [{"color": b["key"], "animals":[hit["_source"]["name"] for hit in b["nombres_animales"]["hits"]["hits"]]} for b in res["aggregations"]["por_color"]["buckets"]]
        cache_set(cache_key, result)
        return jsonify({"source": "db", "data": result})
    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
