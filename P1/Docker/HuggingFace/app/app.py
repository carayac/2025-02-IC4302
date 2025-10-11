from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# --- MÉTRICAS ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['componente'])
promedio_tiempo = Histogram('promedio_tiempo_embedding', 'Tiempo promedio de embeddings', ['componente'])

# --- Hooks para medir tiempo y requests ---
@app.before_request
def iniciar_tiempo():
    request.start_time = time.time()

@app.after_request
def medir_peticiones(response):
    tiempo = time.time() - request.start_time
    promedio_tiempo.labels(componente="huggingface").observe(tiempo)
    peticiones_http.labels(componente="huggingface").inc()
    return response

# --- Modelo de embeddings ---
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

@app.route('/encode', methods=['POST'])
def encode():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Falta el campo text'}), 400

    text = data['text']
    embedding = model.encode(text)
    return jsonify({
        'text': text,
        'embedding': embedding.tolist()
    })

@app.route('/status', methods=['GET'])
def status():
    text = "Si funciona"
    embedding = model.encode(text)
    return jsonify({
        'text': text,
        'embedding': embedding.tolist()
    })

# --- Métricas Prometheus ---
@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    # Ejecutar Flask en 0.0.0.0 para que Prometheus pueda hacer scrape
    app.run(host='0.0.0.0', port=5000)

