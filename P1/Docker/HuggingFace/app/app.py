from sentence_transformers import SentenceTransformer
import flask
from flask import request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = flask.Flask(__name__)

# --- MÉTRICAS ---
peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['componente'])
promedio_tiempo = Histogram('promedio_tiempo_embedding', 'Tiempo promedio de embeddings', ['componente'])


@app.before_request
def iniciar_tiempo():
    request.start_time = time.time()

@app.after_request
def medir_peticiones(response):
    tiempo = time.time() - request.start_time
    promedio_tiempo.labels(componente="huggingface").observe(tiempo)
    peticiones_http.labels(componente="huggingface").inc()


model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

@app.route('/encode', methods=['POST'])
def encode():
    #Obtenemos el texto del request
    data = request.get_json()
    # Validamos el campo texto
    if 'text' not in data:
        return jsonify({'Error': 'Falta el campo text'}), 400
    # Guardamos la info del campo texto
    text = data['text']
    # Generamos el embedding
    embedding = model.encode(text)
    # Retornamos el texto y el embedding en formato JSON
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

@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

