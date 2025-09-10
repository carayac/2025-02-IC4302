from flask import Flask, jsonify
import os
import chromadb

app = Flask(__name__)

CHROMA_HOST = os.getenv("CHROMA_HOST", "databases-chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# List animals
@app.route("/animales", methods=["GET"])
def get_animales():
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_or_create_collection(name="animales")
        # Get first 50 items
        items = collection.get(limit=50)
        # items['ids'] contiene los nombres o IDs de los vectores almacenados
        animales = [{"id": idx+1, "nombre": name} for idx, name in enumerate(items['ids'])]
        return jsonify(animales)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# TOP 5 ANIMAL WITH HIGHEST SPEED
@app.route("/top-velocidad", methods=["GET"])
def top_velocidad():
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_or_create_collection(name="animales_velocidad")
        # Get top 5 items sorted by velocidad_max_kmh descending
        items = collection.get(limit=5, sort_by="velocidad_max_kmh", ascending=False)
        top = [{"nombre": items['ids'][i], "velocidad_max_kmh": items['metadatas'][i]['velocidad_max_kmh']} 
               for i in range(len(items['ids']))]
        return jsonify(top)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
