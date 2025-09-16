import chromadb
from chromadb.utils import embedding_functions
from os import getenv
import sys
from flask import Flask, jsonify, request
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- MÉTRICAS ---
peticiones_http = Counter(
    'total_peticiones_http',
    'Total peticiones HTTP',
    ['bd', 'cache']
)

promedio_tiempo = Histogram(
    'promedio_tiempo_consulta',
    'Tiempo promedio de consultas',
    ['bd', 'cache']
)

cache_hit = Counter(
    'total_cache_hit',
    'Total Cache Hit',
    ['bd', 'cache']
)

cache_miss = Counter(
    'total_cache_miss',
    'Total Cache Miss',
    ['bd', 'cache']
)

BD_TYPE = "chromadb"
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


# Variables de entorno
CHROMA_ENDPOINT = getenv("CHROMA_ENDPOINT", "http://localhost:8000")
CHROMA_COLLECTION = getenv("CHROMA_COLLECTION", "animals")
CHROMA_EMBED_MODEL = getenv("CHROMA_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

chroma_collection = None

def init_chroma():
    global chroma_collection
    try:
        host = CHROMA_ENDPOINT.replace("http://", "").replace("https://", "").split(":")[0]
        client = chromadb.HttpClient(host=host, port=8000)
        
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=CHROMA_EMBED_MODEL
        )
        chroma_collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Colección Chroma inicializada: {CHROMA_COLLECTION}")
        return True
    except Exception as e:
        print(f"Error inicializando Chroma: {e}")
        return False

def get_collection():
    global chroma_collection
    if not chroma_collection:
        if not init_chroma():
            return None
    return chroma_collection

# list animals 
@app.route("/animales", methods=["GET"])
def get_animales():
    try:
        collection = get_collection()
        if not collection:
            return jsonify({"error": "No se pudo conectar a ChromaDB"}), 500
        
        results = collection.get(include=["metadatas"])
        
        animales = []
        for metadata in results["metadatas"]:
            animales.append({
                "nombre": metadata.get("name", "N/A")
            })
        
        return jsonify(animales)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# list colors with animals 
@app.route("/colores", methods=["GET"])
def get_colores():
    try:
        collection = get_collection()
        if not collection:
            return jsonify({"error": "No se pudo conectar a ChromaDB"}), 500
        
        results = collection.get(include=["metadatas"])
        
        colores_dict = {}
        for metadata in results["metadatas"]:
            color = metadata.get("color", "N/A")
            nombre = metadata.get("name", "N/A")
            
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
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# HEALTH CHECK ENDPOINT
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    init_chroma()
    app.run(host='localhost', port=5000)