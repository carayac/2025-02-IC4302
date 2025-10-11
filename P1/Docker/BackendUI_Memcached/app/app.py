from flask import Flask, jsonify, Response
from flask_cors import CORS
from routes.authentication import auth_blueprint
from routes.friend import friend_blueprint  
from routes.prompt import prompt_blueprint
from routes.user import user_blueprint
import logging
import sys
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# --- INICIALIZACIÓN FLASK ---
app = Flask(__name__)
CORS(app, resources={r"/promptsy/*": {"origins": "*"}})

# --- REGISTRO DE BLUEPRINTS ---
app.register_blueprint(auth_blueprint, url_prefix='/promptsy/auth')
app.register_blueprint(friend_blueprint, url_prefix='/promptsy/friend')
app.register_blueprint(prompt_blueprint, url_prefix='/promptsy/prompt')
app.register_blueprint(user_blueprint, url_prefix='/promptsy/user')

# --- HEALTH CHECK ---
@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint accessed")
    return jsonify({"status": "ok"}), 200

# --- METRICS ---
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# --- MAIN ---
if __name__ == "__main__":
    logger.info("Starting Flask app on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
