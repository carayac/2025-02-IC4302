from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry
import os

# --- METRICS ESTÁNDAR MEMCACHED ---
cache_hit = Counter('cache_hit', 'Cache hits', ['bd', 'cache'])
cache_miss = Counter('cache_miss', 'Cache misses', ['bd', 'cache'])

# --- MÉTRICAS CUSTOM API (DEFINE ONCE, USE EVERYWHERE) ---
cache_hit_api = Counter("api_cache_hit", "Cache hits en API", ["componente"])
cache_miss_api = Counter("api_cache_miss", "Cache misses en API", ["componente"])

tiempo_procesamiento_api = Histogram(
    "api_tiempo_procesamiento_segundos",
    "Tiempo de procesamiento de requests en API", 
    ["componente", "endpoint"]
)

peticiones_endpoint_api = Counter(
    "api_total_peticiones_endpoint",
    "Total de peticiones por endpoint en API",
    ["componente", "endpoint"]
)

# --- MÉTRICAS MEMCACHED ESTÁNDAR ---
memcached_commands_total = Counter(
    'memcached_commands_total',
    'Total number of all requests broken down by command and status', 
    ['command', 'status']
)

memcached_current_connections = Gauge(
    'memcached_current_connections',
    'Current number of open connections'
)

memcached_bytes_read_total = Counter(
    'memcached_bytes_read_total',
    'Total number of bytes read by this server'
)

memcached_bytes_written_total = Counter(
    'memcached_bytes_written_total',
    'Total number of bytes sent by this server'
)

memcached_current_items = Gauge(
    'memcached_current_items', 
    'Current number of items stored'
)

memcached_current_bytes = Gauge(
    'memcached_current_bytes',
    'Current number of bytes used to store items'
)

# CONSTANTS
COMPONENT = "api"
BD_TYPE = "mariadb"
CACHE_TYPE = "memcached"
CACHE_TTL_SECONDS = 60

MEMCACHED_HOST = os.getenv("MEMCACHED_HOST")
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT"))