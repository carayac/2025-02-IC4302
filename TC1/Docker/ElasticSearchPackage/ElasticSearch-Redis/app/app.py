from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
from os import getenv
import os
import json
import sys
import time
import redis
import psutil
import threading, time
from prometheus_client import Gauge
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

BD_TYPE = "elasticsearch"
CACHE_TYPE = "redis"

# --- MÉTRICAS HTTP / CACHE ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio de consultas', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

# --- MÉTRICAS DE SISTEMA ---
cpu_usage = Gauge('system_cpu_usage_percent', 'Uso de CPU (%)', ['bd', 'cache'])
mem_usage = Gauge('system_memory_usage_percent', 'Uso de Memoria (%)', ['bd', 'cache'])
disk_usage = Gauge('system_disk_usage_percent', 'Uso de Disco (%)', ['bd', 'cache'])
net_sent = Gauge('system_network_sent_bytes', 'Bytes enviados por red', ['bd', 'cache'])
net_recv = Gauge('system_network_received_bytes', 'Bytes recibidos por red', ['bd', 'cache'])
open_conns = Gauge('system_open_connections', 'Conexiones de red abiertas', ['bd', 'cache'])
file_descriptors = Gauge('system_file_descriptors', 'Descriptores de archivos abiertos', ['bd', 'cache'])
iops = Gauge('system_iops', 'IOPS simuladas', ['bd', 'cache'])
queries_per_sec = Gauge('vespa_queries_per_second', 'Consultas por segundo', ['bd', 'cache'])
query_response_time = Gauge('vespa_query_response_time_seconds', 'Tiempo de respuesta promedio de consultas', ['bd', 'cache'])
thread_pool_active = Gauge('vespa_thread_pool_active', 'Threads activos en el pool', ['bd', 'cache'])

def actualizar_metricas_sistema(intervalo=5):
    while True:
        # Actualizar métricas con labels (solo bd y cache)
        cpu_usage.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(psutil.cpu_percent(interval=None))
        mem_usage.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(psutil.virtual_memory().percent)
        disk_usage.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(psutil.disk_usage('/').percent)
        
        net = psutil.net_io_counters()
        net_sent.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(net.bytes_sent)
        net_recv.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(net.bytes_recv)
        
        open_conns.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(len(psutil.net_connections()))
        
        try:
            file_descriptors.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(psutil.Process().num_fds())
        except:
            file_descriptors.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(0)
        
        iops.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(0) 
        queries_per_sec.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(0)  
        query_response_time.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(0)  
        thread_pool_active.labels(bd=BD_TYPE, cache=CACHE_TYPE).set(0)  
        
        time.sleep(intervalo)

# Iniciar el thread de métricas del sistema
threading.Thread(target=actualizar_metricas_sistema, daemon=True).start()

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

# Elasticsearch configuration
ES_HOST = getenv("ELASTIC", "localhost")
ES_PORT = getenv("ES_PORT", "9200")
ES_USER = getenv("ELASTIC_USER", "elastic")
ES_PASSWORD = getenv("ELASTIC_PASS", "changeme")

INDEX_NAME = "animals"

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
    cache_key = "animales-nombre"

    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify({"source": "cache", "data": cached})

    conn = get_connection()
    try:
        res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
        animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]

        cache_set(cache_key, animals, CACHE_TTL_SECONDS)
        return jsonify({"source": "db", "data": animals})
    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/colores", methods=["GET"])
def get_colores():
    cache_key = "animales-colores"

    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify({"source": "cache", "data": cached})

    conn = get_connection()
    query = {
        "size": 0,
        "aggs": {
            "por_color": {
                "terms": {"field": "color", "size": 100},
                "aggs": {
                    "nombres_animales": {
                        "top_hits": {"_source": ["name"], "size": 100}
                    }
                }
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

        cache_set(cache_key, result, CACHE_TTL_SECONDS)
        return jsonify({"source": "db", "data": result})
    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
