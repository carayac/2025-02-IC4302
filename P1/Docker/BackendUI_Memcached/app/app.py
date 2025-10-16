from flask import Flask, jsonify
from flask_cors import CORS
from routes.authentication import auth_blueprint
from routes.friend import friend_blueprint  
from routes.prompt import prompt_blueprint
from routes.user import user_blueprint
import logging
import sys

# Set up logging to output to stdout
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

#define CORS policy with the url pattern /promptsy/*
cors = CORS(app, resources={r"/promptsy/*": {"origins": "*"}})

# Register blueprints for modular routes
app.register_blueprint(auth_blueprint, url_prefix='/promptsy/auth')
app.register_blueprint(friend_blueprint, url_prefix='/promptsy/friend')
app.register_blueprint(prompt_blueprint, url_prefix='/promptsy/prompt')
app.register_blueprint(user_blueprint, url_prefix='/promptsy/user')


@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint accessed")
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)