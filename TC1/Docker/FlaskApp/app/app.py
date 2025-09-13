from flask import Flask, jsonify, request
import os
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram
import time


app = Flask(__name__)

# Creación de distintas métricas
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_constlta', 'Total Cache Hit', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])


#Suma peticiones http
@app.after_request
def diferencia_tiempo(response):
    peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache']).inc()
    return response


#Promedio de latencia
#Se inicia cronometro justo antes de la peticion para calcular latencia
@app.before_request
def iniciar_cronometro():
    request.start_time = time.time()

#Se calcula el tiempo justo despues de la peticion
@app.after_request
def diferencia_tiempo(response):
    tiempo = time.time() - request.start_time #tiempo tardado
    promedio_tiempo = Histogram('promedio_tiempo_constlta', 'Total Cache Hit', ['bd', 'cache']).observe(tiempo)
    return response


