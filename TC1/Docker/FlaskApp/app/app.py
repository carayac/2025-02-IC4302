from flask import Flask, jsonify
import os
import chromadb
import kagglehub
import pandas as pd
import mysql.connector

app = Flask(__name__)

CHROMA_URL = os.getenv("CHROMA_URL", "http://databases-chromadb:8000")

@app.route("/")
def hello_world():
    DATA=os.getenv('PROMETHEUSENDPOINT')
    return "<p>Hello, "+ DATA +"World!</p>"

@app.route("/chromadb")
def chroma():
    client = chromadb.HttpClient(
    host="databases-chromadb",  # nombre del servicio Kubernetes
    port=8000
    )
    # Crear colección de prueba
    collection = client.get_or_create_collection(name="coleccion_prueba2")
    return jsonify({"coleccion": collection.name})

@app.route("/colecciones")
def listar_colecciones():
    client = chromadb.HttpClient(
        host="databases-chromadb",
        port=8000
    )

    # Obtener todas las colecciones
    colecciones = client.list_collections()

    # Extraer solo los nombres
    nombres = [c.name for c in colecciones]

    return jsonify({"colecciones": nombres})



@app.route("/load_dataset", methods=["POST"])
def load_dataset():
    try:
        # Descargar dataset desde Kaggle
        path = kagglehub.dataset_download("iamsouravbanerjee/animal-information-dataset")

        # Buscar el CSV dentro de la carpeta
        csv_file = None
        for file in os.listdir(path):
            if file.endswith(".csv"):
                csv_file = os.path.join(path, file)
                break

        if not csv_file:
            return jsonify({"error": "No CSV found in dataset"}), 500

        # Cargar dataset en Pandas
        df = pd.read_csv(csv_file)

        # Conectar a MariaDB
        conn = mysql.connector.connect(
            host="databases-mariadb",  # ← usa el nombre del servicio
            port=3306,
            user="root",
            password="root123",
            database="ic4302_db"
        )
        cursor = conn.cursor()

        # Crear tabla si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                
                name VARCHAR(100),
                height_cm VARCHAR(50),
                weight_kg VARCHAR(50),
                color VARCHAR(100),
                lifespan_years VARCHAR(50),
                diet VARCHAR(50),
                habitat VARCHAR(100),
                predators VARCHAR(100),
                average_speed_kmh VARCHAR(50),
                countries_found VARCHAR(255),
                conservation_status VARCHAR(100),
                family VARCHAR(100),
                gestation_period_days VARCHAR(50),
                top_speed_kmh VARCHAR(50),
                social_structure VARCHAR(100),
                offspring_per_birth VARCHAR(50)
            )
        """)

# Insertar datos
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO animals (
                    name, height_cm, weight_kg, color, lifespan_years, diet, habitat, predators,
                    average_speed_kmh, countries_found, conservation_status, family, gestation_period_days,
                    top_speed_kmh, social_structure, offspring_per_birth
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row["Animal"], row["Height (cm)"], row["Weight (kg)"], row["Color"], row["Lifespan (years)"],
                row["Diet"], row["Habitat"], row["Predators"], row["Average Speed (km/h)"], row["Countries Found"],
                row["Conservation Status"], row["Family"], row["Gestation Period (days)"], row["Top Speed (km/h)"],
                row["Social Structure"], row["Offspring per Birth"]
            ))

        conn.commit()
        conn.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

