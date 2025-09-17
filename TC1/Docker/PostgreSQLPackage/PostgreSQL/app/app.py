import psycopg2
import psycopg2.pool
from os import getenv
import sys
from flask import Flask, jsonify, request
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- MÉTRICAS ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio de consultas', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "postgresql"
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

# Load environment variables
POSTGRES = getenv("POSTGRES")
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")


#DATABASE CONNECTION
pg_pool = None

# Initialize connection pool
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

# Get a connection from the pool
def get_connection():
    global pg_pool
    if not pg_pool:
        init_pool()
    return pg_pool.getconn()

# Release a connection back to the pool
def release_connection(conn):
    global pg_pool
    if pg_pool and conn:
        pg_pool.putconn(conn)

#list animals
@app.route("/animales", methods=["GET"])
def get_animales():
    conn = get_connection()
    try:
        if conn is None:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, nombre FROM animal LIMIT 50;")
            rows = cur.fetchall()
            return jsonify([{"id": r[0], "nombre": r[1]} for r in rows])
        finally:
            cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_connection(conn)

#list colors with animals
@app.route("/colores", methods=["GET"])
def get_colores():
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
            return jsonify([{"animals": r[1], "color": r[0]} for r in rows])
        finally:
            cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_connection(conn)


#HEALTH CHECK ENDPOINT
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    app.run(host='localhost', port=5000)