from flask import Flask, jsonify
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)

# Elasticsearch configuration from environment variables
ES_HOST = os.getenv('ELASTIC')
ES_PORT = os.getenv('ES_PORT')
ES_USER = os.getenv('ELASTIC_USER')
ES_PASSWORD = os.getenv('ELASTIC_PASS')

@app.route("/testConnection", methods=['GET'])
def testConnection():
    try:
        # Crear conexión
        connection = Elasticsearch(
            [f"http://{ES_HOST}:{ES_PORT}"],
            basic_auth=(ES_USER, ES_PASSWORD)  # <-- tuple, no list
        )
        # Probar ping
        if connection.ping():
            return "Elasticsearch connection successful ✅", 200
        else:
            return "Elasticsearch no responde ❌", 400
    except Exception as e:
        return f"Error: {e}", 400

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
