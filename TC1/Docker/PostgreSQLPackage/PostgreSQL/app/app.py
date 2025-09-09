from flask import Flask, jsonify
import psycopg2
from os import getenv
import sys

# Load environment variables
POSTGRES = getenv("POSTGRES")
POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
POSTGRES_DB = getenv("POSTGRES_DB")

app = Flask(__name__)

#DATABASE CONNECTION
def get_connection():
    try:
        pg_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=POSTGRES,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
    )
        print("Pool de conexiones PostgreSQL creado")
        return pg_pool
    except Exception as e:
        print(f"Error creando pool PostgreSQL: {e}")
        return None
        sys.exit(1)

# List all the animals
@app.route("/animales", methods=["GET"])
def get_animales():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM animal LIMIT 50;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "nombre": r[1]} for r in rows])

# List all diets
@app.route("/dietas", methods=["GET"])
def get_dietas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, tipo_dieta FROM dieta;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "tipo_dieta": r[1]} for r in rows])

# List all habitats
@app.route("/habitats", methods=["GET"])
def get_habitats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_habitat FROM habitat;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "nombre_habitat": r[1]} for r in rows])

# List familias
@app.route("/familias", methods=["GET"])
def get_familias():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_familia FROM familia;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"id": r[0], "nombre_familia": r[1]} for r in rows])

#ANIMAL WITH HIGHEST SPEED
@app.route("/top-velocidad", methods=["GET"])
def top_velocidad():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.nombre, i.velocidad_max_kmh
        FROM animal a
        JOIN info_extra i ON a.id = i.animal_id
        ORDER BY NULLIF(i.velocidad_max_kmh, '')::INT DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"nombre": r[0], "velocidad_max_kmh": r[1]} for r in rows])


#HEALTH CHECK ENDPOINT
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200



if __name__ == "__main__":
    app.run(host='localhost', port=5000)