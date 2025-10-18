from flask import Blueprint, request,jsonify, g
from tools.mariadb_connection import execute_query
import logging
import sys
import mariadb
import bcrypt
import time

# Importar las métricas desde el módulo metrics
from metrics import (
    tiempo_procesamiento_api, 
    peticiones_endpoint_api,
    COMPONENT
)

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

# --- Hooks para medir tiempo de request ---
@auth_blueprint.before_request
def medir_tiempo_peticion_start():
    g.start_time = time.time()
    endpoint = request.endpoint or "unknown"
    # Incrementar el contador de peticiones para este endpoint
    peticiones_endpoint_api.labels(componente=COMPONENT, endpoint=endpoint).inc()

@auth_blueprint.after_request
def medir_tiempo_peticion_end(response):
    # Calcular duración de la request
    start_time = getattr(g, "start_time", None)
    if start_time is not None:
        duracion = time.time() - start_time
        endpoint = request.endpoint or "unknown"
        # Registrar la duración en el histograma
        tiempo_procesamiento_api.labels(componente=COMPONENT, endpoint=endpoint).observe(duracion)
    return response


#Route for login into promptsy
@auth_blueprint.route('/login' , methods=['POST'])
def login():
    email = request.json.get("email")
    password = request.json.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        res = execute_query(
            "SELECT id, name, lastname, description, email, password FROM User WHERE email = ? LIMIT 1",
            (email,)
        )

        user = res[0] if res else None
        if not user:
            logger.warning(f"Login failed: email not found {email}")
            return jsonify({"error": "Invalid email or password"}), 401

        # CHECK PASSWORD
        if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            logger.warning(f"Login failed: wrong password for {email}")
            return jsonify({"error": "Invalid email or password"}), 401

        logger.info(f"User {email} logged in successfully")
        return jsonify({
            "id": user["id"],
            "name": user["name"],
            "lastname": user["lastname"],
            "description": user["description"],
            "email": user["email"]
        }), 200

    except mariadb.Error as e:
        logger.error(f"Database error during login: {e}")
        return jsonify({"error": "Database error"}), 500

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500



#Route for registering into promptsy
@auth_blueprint.route('/register', methods=['POST'])
def register():
    logger.info("Register route accessed")

    #get the data from the request
    name = request.json.get('name')
    lastname = request.json.get('lastname')
    description = request.json.get('description')
    email = request.json.get('email')
    password = request.json.get('password')

    if not all([name, lastname, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        #hase the password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        # execute the insert query in the table users
        res = execute_query(
            "INSERT INTO User (name, lastname, description, email, password) VALUES (?, ?, ?, ?, ?)",
            (name, lastname, description, email, hashed_password.decode("utf-8"))
        )

        logger.info(f"User {email} registered successfully")
        return {"message": "User registered successfully"}, 201

    except mariadb.IntegrityError as e:
        # the email must be unique this error is for duplicate entry
        if e.errno == 1062:
            logger.warning(f"Email already exists: {email}")
            return {"error": "Email already exists"}, 400
        else:
            logger.error(f"Integrity error registering user {email}: {e}")
            return {"error": "Database integrity error"}, 500

    except Exception as e:
        logger.error(f"Unexpected error registering user {email}: {e}")
        return {"error": "Error registering user"}, 500
