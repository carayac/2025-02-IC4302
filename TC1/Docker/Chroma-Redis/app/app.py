from flask import Flask, jsonify
import os
import chromadb

app = Flask(__name__)

CHROMA_URL = os.getenv("CHROMA_URL", "http://databases-chromadb:8000")

@app.route("/")
def hello_world():
    DATA=os.getenv('PROMETHEUSENDPOINT')
    return "<p>Hello, "+ DATA +"World!</p>"

@app.route("/chromadb/redis/create")
def chroma():
    client = chromadb.HttpClient(
    host="databases-chromadb",  # nombre del servicio Kubernetes
    port=8000
    )
    # Crear colección de prueba
    collection = client.get_or_create_collection(name="coleccion_prueba")
    return jsonify({"coleccion": collection.name})

@app.route("/chromadb/redis/view")
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



