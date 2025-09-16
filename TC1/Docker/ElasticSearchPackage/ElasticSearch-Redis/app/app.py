from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
import os
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# ------------------ Métricas Prometheus ------------------
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio', ['bd', 'cache'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['bd', 'cache'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['bd', 'cache'])

BD_TYPE = "elasticsearch"
CACHE_TYPE = "redis"  

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
ES_HOST = os.getenv('ELASTIC')
ES_PORT = os.getenv('ES_PORT')
ES_USER = os.getenv('ELASTIC_USER')
ES_PASSWORD = os.getenv('ELASTIC_PASS')
connection = None #global connection variable

@app.route("/testConnection", methods=['GET'])
def testConnection():
    try:#Try to connect to elasticsearch
        connection = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"], 
                                                 basic_auth=[ES_USER, ES_PASSWORD]) #connection basic with user and password
        return "Elasticsearch connection successful",200
    except Exception as e:
        return f"Error: {e}",400

#health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)