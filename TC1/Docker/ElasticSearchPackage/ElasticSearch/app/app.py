from elasticsearch import Elasticsearch
from os import getenv
import sys
from flask import Flask, jsonify, request
import time
import psutil
import threading, time
from prometheus_client import Gauge
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

BD_TYPE = "elasticsearch"
CACHE_TYPE = "none"

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
        ) # crea la conexión a Elasticsearch
        if not conn.ping(): #si la conexión es exitosa
            raise Exception("No se pudo conectar a Elasticsearch")
        return conn # devuelva la conexión creada
    except Exception as e:
        print(f"Error creando conexión Elasticsearch: {e}")
        sys.exit(1)


# List all the animals
@app.route("/animales", methods=["GET"])
def get_animales():
    conn = get_connection() # obtiene la conexión a Elasticsearch
    try:
        res = conn.search(index=INDEX_NAME, size=50, query={"match_all": {}})
        animals = [{"id": hit["_id"], "nombre": hit["_source"]["name"]} for hit in res["hits"]["hits"]]
        return jsonify(animals)# edvuelve la lista de animales
    except Exception as e:
        if e.info and 'index_not_found_exception' in e.info['error']['type']:
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500

@app.route("/colores", methods=["GET"])
def get_colores():
    conn = get_connection()  # obtiene conexión a Elasticsearch
    #query to aggregate animals by color and get their names
    query = {
        "size": 0,
        "aggs": {
            "por_color": {
            "terms": {
                "field": "color",
                "size": 100
            },
            "aggs": {
                "nombres_animales": {
                "top_hits": {
                    "_source": ["name"],
                    "size": 100
                }
                }
            }
            }
        }
    }

    try: # Execute the search query
        res = conn.search(index="animals", body=query)

        result = []
        for bucket in res["aggregations"]["por_color"]["buckets"]: # Process each color bucket
            color = bucket["key"]
            animales = [hit["_source"]["name"] for hit in bucket["nombres_animales"]["hits"]["hits"]]
            result.append({ # Append color and animal names to the result
                "color": color,
                "animals": animales
            })
        return jsonify(result) # Return the aggregated result

    except Exception as e:
        if getattr(e, "info", None) and 'index_not_found_exception' in e.info.get('error', {}).get('type', ''):
            return jsonify({"error": "Debe cargar la base de datos"}), 404
        return jsonify({"error": str(e)}), 500



# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
