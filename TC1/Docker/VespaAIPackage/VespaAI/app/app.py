import requests
from os import getenv
from flask import Flask, jsonify, request
import time
import psutil
import threading, time
from prometheus_client import Gauge
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

BD_TYPE = "vespaai"
CACHE_TYPE = "none"

# --- MÉTRICAS ---
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

VESPA_ENDPOINT = getenv("VESPA_ENDPOINT", "http://localhost:8081")
VESPA_COLLECTION = getenv("VESPA_COLLECTION", "animales")


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
                total_count = data.get('root', {}).get('fields', {}).get('totalCount', 0)
                children_count = len(data.get('root', {}).get('children', []))
                        
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
    docs = get_vespa_docs()    
    animales = [{"nombre": doc.get("name", "N/A")} for doc in docs]
    return jsonify(animales)

@app.route("/colores", methods=["GET"])
def get_colores():
    docs = get_vespa_docs()
    print(f"Documentos recibidos: {len(docs)}")
    
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
    
    return jsonify(colores_list)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
