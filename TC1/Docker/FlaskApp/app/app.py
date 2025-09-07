from flask import Flask, request, jsonify
import os, time
import redis
from prometheus_client import Counter, Histogram, generate_latest
from db_backends import get_db_instance

app = Flask(__name__)

# --- Caché opcional ---
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "none")
cache = None
if CACHE_BACKEND == "redis":
    cache = redis.Redis(host="redis-service", port=6379, decode_responses=True)
elif CACHE_BACKEND == "memcached":
    import pymemcache.client
    cache = pymemcache.client.Client(("memcached-service", 11211))

# --- Métricas Prometheus ---
REQUEST_COUNT = Counter("http_requests_total", "Total de peticiones HTTP", ["endpoint"])
DB_QUERY_TIME = Histogram("db_query_time_seconds", "Tiempo en ejecutar query")
CACHE_HITS = Counter("cache_hits_total", "Número de Cache Hits")
CACHE_MISSES = Counter("cache_misses_total", "Número de Cache Misses")

# --- Instancia de DB ---
db_instance = get_db_instance()

# --- Endpoint principal ---
@app.route("/books", methods=["GET"])
def books_endpoint():
    REQUEST_COUNT.labels(endpoint="/books").inc()
    author = request.args.get("author", None)
    cache_key = f"books:{author}"

    # Revisar caché
    if cache:
        cached = cache.get(cache_key)
        if cached:
            CACHE_HITS.inc()
            return jsonify(eval(cached))
        CACHE_MISSES.inc()

    start = time.time()
    result = db_instance.get_books(author)
    DB_QUERY_TIME.observe(time.time() - start)

    # Guardar en caché
    if cache:
        cache.set(cache_key, str(result), ex=30)

    return jsonify(result)

# --- Endpoint métricas Prometheus ---
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
