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

# --- Elasticsearch config ---
ES_HOST = getenv("ELASTIC", "localhost")
ES_PORT = getenv("ES_PORT", "9200")
ES_USER = getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = getenv("ELASTIC_PASS", "changeme")
INDEX_NAME = "animals"

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

@app.route("/animales", methods=["GET"])
def get_animales():
    conn = get_connection()
    try:
        res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
        animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]
        return jsonify(animals)
    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/colores", methods=["GET"])
def get_colores():
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
        res = conn.search(index="animals", body=query)
        result = []
        for bucket in res["aggregations"]["por_color"]["buckets"]:
            color = bucket["key"]
            animales = [hit["_source"]["name"] for hit in bucket["nombres_animales"]["hits"]["hits"]]
            result.append({"color": color, "animals": animales})
        return jsonify(result)
    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

