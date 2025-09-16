from flask import Flask, jsonify, request
import os
import chromadb
from pymemcache.client.base import Client
import json
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

CHROMA_URL = os.getenv("CHROMA_URL", "http://databases-chromadb:8000")

# ------------------ Métricas Prometheus ------------------
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "chromadb"
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

# ------------------ Variables para Memcached ------------------
MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "localhost")
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", "11211"))
CACHE_TTL_SECONDS = 60  

memcached = Client(("databases-memcached", 11211))

def cache_get(key):
    raw = memcached.get(key)
    if raw is None:
        cache_miss.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
        return None
    cache_hit.labels(bd=BD_TYPE, cache=CACHE_TYPE).inc()
    return None if raw is None else raw.decode("utf-8")

def cache_set(key: str, value: dict, ttl: int = CACHE_TTL_SECONDS):
    memcached.set(key, json.dumps(value).encode("utf-8"), expire=ttl)

# ------------------ Endpoints originales ------------------
@app.route("/", methods=['GET'])
def hello_world():
    DATA = os.getenv('PROMETHEUSENDPOINT', "")
    return "<p>Hello, " + DATA + "World!</p>"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route("/chromadb", methods=['GET'])
def chroma():
    cache_key = "coleccion_prueba2"

    # Lee desde caché
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"source": "cache", "coleccion": json.loads(cached)})
    
    # En caso de no estar, lee en chroma
    client = chromadb.HttpClient(
        host="databases-chromadb",  # nombre del servicio Kubernetes
        port=8000
    )
    # Crear colección de prueba
    collection = client.get_or_create_collection(name="coleccion_prueba2")

    cache_set(cache_key, collection.name)
    return jsonify({"source": "withoutCache", "coleccion": collection.name})

@app.route("/colecciones", methods=['GET'])
def listar_colecciones():
    cache_key = "lista_colecciones"

    # Lee desde caché
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"source": "cache", "colecciones": json.loads(cached)})
    
    # En caso de no estar, lee en chroma
    client = chromadb.HttpClient(
        host="databases-chromadb",
        port=8000
    )

    # Obtener todas las colecciones
    colecciones = client.list_collections()
    # Extraer solo los nombres
    nombres = [c.name for c in colecciones]
    cache_set(cache_key, nombres)

    return jsonify({"source": "withoutCache", "colecciones": nombres})

if __name__ == "__main__":
    app.run(host='localhost', port=5000)
