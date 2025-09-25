from sentence_transformers import SentenceTransformer
import flask
from flask import request, jsonify

app = flask.Flask(__name__)
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

@app.route('/encode', methods=['POST'])
def encode():
    #Obtenemos el texto del request
    data = request.get_json()
    # Validamos que el campo texto
    if 'text' not in data:
        return jsonify({'Error': 'Falta el campo texto'}), 400
    # Guardamos la info del campo texto
    text = data['text']
    # Generamos el embedding
    embedding = model.encode(text)
    # Retornamos el texto y el embedding en formato JSON
    return jsonify({
        'text': text,
        'embedding': embedding.tolist()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# https://huggingface.co/sentence-transformers/all-mpnet-base-v2
