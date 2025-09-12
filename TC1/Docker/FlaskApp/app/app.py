from flask import Flask, jsonify, request
import os
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram


app = Flask(__name__)
metrics = PrometheusMetrics(app)


# Creación de distintas métricas
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['method', 'endpoint'])
cache_hit = Histogram('promedio_tiempo_constlta', 'Total Cache Hit', ['method', 'endpoint'])
cache_hit = Counter('total_cache_hit', 'Total Cache Hit', ['method', 'endpoint'])
cache_miss = Counter('total_cache_miss', 'Total Cache Miss', ['method', 'endpoint'])


CHROMA_URL = os.getenv("CHROMA_URL", "http://databases-chromadb:8000")

@app.route("/")
def hello_world():
    DATA=os.getenv('PROMETHEUSENDPOINT')
    return "<p>Hello, "+ DATA +"World!</p>"

@app.route("/chromadb")
def chroma():
    client = chromadb.HttpClient(
    host="databases-chromadb",  # nombre del servicio Kubernetes
    port=8000
    )
    # Crear colección de prueba
    collection = client.get_or_create_collection(name="coleccion_prueba2")
    return jsonify({"coleccion": collection.name})

@app.route("/colecciones")
def listar_colecciones():
    client = chromadb.HttpClient(
        host="databases-chromadb",
        port=8000
    )

    # Obtener todas las colecciones
    colecciones = client.list_collections()

    # Extraer solo los nombres
    nombres = [c.name for c in colecciones]

    return jsonify({"colecciones": nombres})



