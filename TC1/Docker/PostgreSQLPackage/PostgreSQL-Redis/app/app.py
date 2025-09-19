import psycopg2
import psycopg2.pool
from os import getenv
import os, json
import sys
import redis
from flask import Flask, jsonify, request
import time
import psutil
import threading, time
from prometheus_client import Gauge
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- MÉTRICAS ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio de consultas', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "postgresql"
CACHE_TYPE = "redis"

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

# Load environment variables
POSTGRES = getenv("POSTGRES")
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")

# Variables para Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = 60

redis_client = redis.Redis(host="databases-redis", port=6379, decode_responses=True)

# Funciones de caché
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

# Pool de conexiones PostgreSQL
pg_pool = None

def init_pool():
    global pg_pool
    try:
        pg_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=POSTGRES,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        print("Pool de conexiones PostgreSQL creado")
    except Exception as e:
        print(f"Error creando pool PostgreSQL: {e}")
        sys.exit(1)

def get_connection():
    global pg_pool
    if not pg_pool:
        init_pool()
    return pg_pool.getconn()

def release_connection(conn):
    global pg_pool
    if pg_pool and conn:
        pg_pool.putconn(conn)

# list animals
@app.route("/animales", methods=["GET"])
def get_animales():
    cache_key = "animales-nombre"

    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify({"source": "cache", "data": cached})

    conn = get_connection()
    try:
        if conn is None:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, nombre FROM animal LIMIT 50;")
            rows = cur.fetchall()
            animales = [{"id": r[0], "nombre": r[1]} for r in rows]

            cache_set(cache_key, animales, CACHE_TTL_SECONDS)
            return jsonify({"source": "db", "data": animales})
        finally:
            cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_connection(conn)

# list colors with animals
@app.route("/colores", methods=["GET"])
def get_colores():
    cache_key = "animales-colores"

    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify({"source": "cache", "data": cached})

    conn = get_connection()
    try:
        if conn is None:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT a.color, STRING_AGG(DISTINCT a.nombre, ', ') AS animales
                FROM animal a
                GROUP BY a.color;
            """)
            rows = cur.fetchall()
            colores = [{"animals": r[1], "color": r[0]} for r in rows]

            cache_set(cache_key, colores, CACHE_TTL_SECONDS)
            return jsonify({"source": "db", "data": colores})
        finally:
            cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_connection(conn)

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
