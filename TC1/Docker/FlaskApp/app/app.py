from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest
import time

app = Flask(__name__)

# Creación de distintas métricas
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_constlta', 'Total Cache Hit', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD = ""
CACHE = ""

#Promedio de latencia
#Se inicia cronometro justo antes de la peticion para calcular latencia
@app.before_request
def configurar_metricas():
    request.start_time = time.time()

    #determinar bd y tipo cache
    request.bd_type = BD 
    request.cache_type = CACHE

#Se calcula el tiempo justo despues de la peticion
#luego se hace la suma de http
@app.after_request
def registrar_metricas(response):
    tiempo = time.time() - request.start_time
    
    promedio_tiempo.labels(bd=request.bd_type, cache=request.cache_type).observe(tiempo)
    peticiones_http.labels(bd=request.bd_type, cache=request.cache_type).inc()
    
    return response

# Endpoint para métricas de Prometheus
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

# Funcion para obtener las metricas
def get_metrics():
    return {
        'peticiones_http': peticiones_http,
        'promedio_tiempo': promedio_tiempo,
        'cache_hit': cache_hit,
        'cache_miss': cache_miss
    }