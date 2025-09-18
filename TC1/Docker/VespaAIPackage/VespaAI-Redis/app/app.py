import requests
from os import getenv
import sys
import os, json
import redis
from flask import Flask, jsonify, request
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- MÉTRICAS ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio de consultas', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "vespaai"
CACHE_TYPE = "redis"

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

VESPA_ENDPOINT = getenv("VESPA_ENDPOINT", "http://localhost:8081")
VESPA_COLLECTION = getenv("VESPA_COLLECTION", "animales")

# Variables para Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = 60

redis_client = redis.Redis(host="databases-redis", port=6379, decode_responses=True)

def cache_get(key):
    try:
        raw = redis_client.get(key)
        if not raw:
            cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
            return None

        cache_hit.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return json.loads(raw)
    except Exception:
        cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return None

def cache_set(key: str, value: dict, ttl: int = CACHE_TTL_SECONDS):
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception:
        pass

def get_vespa_docs():
    try:
        query = {
            "yql": "select name, color from animales where true",
            "hits": 100,
            "timeout": "10s"
        }
        response = requests.post(f"{VESPA_ENDPOINT}/search/", json=query, timeout=10)
        if response.status_code == 200:
            data = response.json()
            docs = []
            for hit in data.get("root", {}).get("children", []):
                fields = hit.get("fields", {})
                docs.append({
                    "name": fields.get("name", "Desconocido"),
                    "color": fields.get("color", "N/A")
                })
            return docs
        else:
            print(f"Query falló: {response.status_code} - {response.text[:200]}")
            return []
    except Exception as e:
        print(f"Error en get_vespa_docs: {e}")
        return []

@app.route("/animales", methods=["GET"])
def get_animales():
    cache_key = "animales-nombre"

    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify({"source": "cache", "data": cached})

    docs = get_vespa_docs()
    animales = [{"nombre": doc.get("name", "N/A")} for doc in docs]

    cache_set(cache_key, animales, CACHE_TTL_SECONDS)
    return jsonify({"source": "db", "data": animales})

@app.route("/colores", methods=["GET"])
def get_colores():
    cache_key = "animales-colores"

    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify({"source": "cache", "data": cached})

    docs = get_vespa_docs()
    colores_dict = {}
    for doc in docs:
        color = doc.get("color", "N/A")
        nombre = doc.get("name", "N/A")
        if color not in colores_dict:
            colores_dict[color] = []
        colores_dict[color].append(nombre)

    colores_list = []
    for color, animales_list in colores_dict.items():
        colores_list.append({
            "color": color,
            "animals": ", ".join(animales_list)
        })

    cache_set(cache_key, colores_list, CACHE_TTL_SECONDS)
    return jsonify({"source": "db", "data": colores_list})

if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)
